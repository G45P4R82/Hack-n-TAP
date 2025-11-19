import json
import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.utils import timezone
from datetime import timedelta
from .models import Tap, TapUsage
from .services import DeviceService
from apps.core.utils import get_client_ip

logger = logging.getLogger('lhctap.api')


@login_required
def dashboard(request):
    """Dashboard simplificado do usuário"""
    # Dispositivos vinculados ao usuário
    user_devices = request.user.devices.all()
    devices_count = user_devices.count()
    
    # Histórico de consumo (apenas sucessos)
    user_usage = TapUsage.objects.filter(
        user=request.user,
        result='ok'
    ).select_related('tap').order_by('-created_at')[:50]
    
    context = {
        'user': request.user,
        'devices_count': devices_count,
        'user_devices': user_devices,
        'user_usage': user_usage,
    }
    
    return render(request, 'taps/dashboard.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def check_tap_access(request, tap_id):
    """
    Endpoint simplificado: POST /api/tap/<tap_id>/
    Recebe device_id no body JSON
    Retorna apenas se o tap está liberado ou não
    """
    device_id = None
    try:
        # Obter device_id do body
        try:
            data = json.loads(request.body)
            device_id = data.get('device_id')
        except json.JSONDecodeError as e:
            logger.error(f"Erro: JSON inválido na requisição para tap_id={tap_id}, body={request.body.decode('utf-8', errors='ignore')[:200]}, erro={str(e)}")
            return JsonResponse({
                'liberado': False,
                'erro': 'json_invalido',
                'message': 'JSON inválido'
            }, status=400)
        
        # Validar device_id
        if not device_id:
            logger.error(f"Erro: device_id não fornecido na requisição para tap_id={tap_id}, body={request.body.decode('utf-8', errors='ignore')[:200]}")
            return JsonResponse({
                'liberado': False,
                'erro': 'device_id_obrigatorio',
                'message': 'device_id é obrigatório no body'
            }, status=400)
        
        # Validar device e liberar tap
        result = DeviceService.validate_device(
            device_id=device_id,
            tap_id=tap_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        logger.info(f"Resultado: {result}")
        # Log do resultado
        if result['ok']:
            logger.info(f"✅ Tap liberado: device_id={device_id}, tap_id={tap_id}, user={result.get('user_name', 'N/A')}, tap={result.get('tap_name', 'N/A')}")
        else:
            logger.warning(f"❌ Tap não liberado: device_id={device_id}, tap_id={tap_id}, erro={result.get('error', 'desconhecido')}, message={result.get('message', '')}")
        
        # Retornar apenas se está liberado ou não
        if result['ok']:
            return JsonResponse({
                'liberado': True
            }, status=200)
        else:
            return JsonResponse({
                'liberado': False,
                'erro': result.get('error', 'erro_desconhecido'),
                'message': result.get('message', '')
            }, status=200)
            
    except Exception as e:
        logger.error(f"❌ Erro interno ao verificar acesso: device_id={device_id or 'N/A'}, tap_id={tap_id}, ip={get_client_ip(request)}, erro={str(e)}", exc_info=True)
        return JsonResponse({
            'liberado': False,
            'erro': 'erro_interno',
            'message': 'Erro interno do servidor'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def validate_device(request):
    """
    Endpoint simplificado para validação por device_id
    
    Recebe:
    - device_id: ID do dispositivo (cartão RFID)
    - tap_id: ID do tap a ser liberado
    """
    try:
        # Obter device_id do header
        device_id = request.META.get('HTTP_X_DEVICE_ID')
        if not device_id:
            return JsonResponse({
                'ok': False,
                'error': 'missing_device_id',
                'message': 'Header X-Device-ID é obrigatório'
            }, status=400)
        
        # Obter dados da requisição
        try:
            data = json.loads(request.body)
            tap_id = data.get('tap_id')
            device_id_from_body = data.get('device_id')
        except json.JSONDecodeError:
            return JsonResponse({
                'ok': False,
                'error': 'invalid_json',
                'message': 'JSON inválido'
            }, status=400)
        
        # Validar parâmetros obrigatórios
        if not tap_id:
            return JsonResponse({
                'ok': False,
                'error': 'missing_parameters',
                'message': 'tap_id é obrigatório'
            }, status=400)
        
        # Se device_id vier no body também, verificar consistência
        if device_id_from_body and device_id != device_id_from_body:
            return JsonResponse({
                'ok': False,
                'error': 'device_id_mismatch',
                'message': 'Device ID inconsistente entre header e body'
            }, status=400)
        
        # Validar device e liberar tap
        result = DeviceService.validate_device(
            device_id=device_id,
            tap_id=tap_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Retornar resultado
        if result['ok']:
            return JsonResponse(result, status=200)
        else:
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"Erro na validação de device: {e}", exc_info=True)
        return JsonResponse({
            'ok': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor'
        }, status=500)


@require_http_methods(["GET"])
@never_cache
def tap_status(request, tap_id):
    """Endpoint para verificação de status operacional do tap"""
    try:
        tap = Tap.objects.get(id=tap_id, is_active=True)
        
        # Buscar último uso
        from datetime import datetime
        
        last_usage = TapUsage.objects.filter(
            tap=tap,
            result='ok'
        ).order_by('-created_at').first()
        
        # Contar usos de hoje
        today_start = timezone.make_aware(
            datetime.combine(timezone.now().date(), datetime.min.time())
        )
        
        usages_today = TapUsage.objects.filter(
            tap=tap,
            result='ok',
            created_at__gte=today_start
        ).count()
        
        return JsonResponse({
            'tap_id': tap.id,
            'name': tap.name,
            'type': tap.type,
            'type_display': tap.get_type_display(),
            'location': tap.location,
            'dose_ml': tap.dose_ml,
            'is_active': tap.is_active,
            'last_usage': last_usage.created_at.isoformat() if last_usage else None,
            'usages_today': usages_today
        })
        
    except Tap.DoesNotExist:
        return JsonResponse({
            'error': 'tap_not_found',
            'message': 'Tap não encontrado ou inativo'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Erro no status do tap {tap_id}: {e}", exc_info=True)
        return JsonResponse({
            'error': 'internal_error',
            'message': 'Erro interno do servidor'
        }, status=500)


@require_http_methods(["GET"])
def list_taps(request):
    """Lista todos os taps ativos"""
    try:
        taps = Tap.objects.filter(is_active=True).order_by('name')
        
        taps_data = [{
            'id': tap.id,
            'name': tap.name,
            'type': tap.type,
            'type_display': tap.get_type_display(),
            'location': tap.location,
            'dose_ml': tap.dose_ml,
        } for tap in taps]
        
        return JsonResponse({
            'ok': True,
            'taps': taps_data,
            'count': len(taps_data)
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar taps: {e}", exc_info=True)
        return JsonResponse({
            'ok': False,
            'error': 'internal_error',
            'message': 'Erro interno do servidor'
        }, status=500)
