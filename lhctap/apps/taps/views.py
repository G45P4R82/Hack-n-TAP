import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from django.views import View
from .models import Tap
from .services import TokenService
from apps.core.services import RateLimitService
from apps.core.utils import get_client_ip
from apps.core.exceptions import RateLimitExceededError

logger = logging.getLogger('lhctap.api')


@csrf_exempt
@require_http_methods(["POST"])
@ratelimit(key='header:X-Device-ID', rate='10/m', method='POST')
def validate_token(request):
    """Endpoint crítico para validação de tokens QR por dispositivos leitores"""
    try:
        # Verificar rate limit
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
            token = data.get('token')
            device_id_from_body = data.get('device_id')
        except json.JSONDecodeError:
            return JsonResponse({
                'ok': False,
                'error': 'invalid_json',
                'message': 'JSON inválido'
            }, status=400)
        
        # Validar parâmetros obrigatórios
        if not token or not device_id_from_body:
            return JsonResponse({
                'ok': False,
                'error': 'missing_parameters',
                'message': 'Token e device_id são obrigatórios'
            }, status=400)
        
        # Verificar consistência do device_id
        if device_id != device_id_from_body:
            return JsonResponse({
                'ok': False,
                'error': 'device_id_mismatch',
                'message': 'Device ID inconsistente'
            }, status=400)
        
        # Verificar rate limits
        try:
            RateLimitService.validate_rate_limits(
                device_id, 
                get_client_ip(request)
            )
        except RateLimitExceededError:
            return JsonResponse({
                'ok': False,
                'error': 'rate_limited',
                'message': 'Rate limit excedido',
                'retry_after': 60
            }, status=429)
        
        # Validar token
        result = TokenService.validate_token(
            token=token,
            device_id=device_id,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Retornar resultado
        if result['ok']:
            return JsonResponse(result)
        else:
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"Erro na validação de token: {e}", exc_info=True)
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
        
        # Buscar última transação
        from apps.wallet.models import Transaction
        last_transaction = Transaction.objects.filter(
            ref_session__tap=tap,
            amount_cents__lt=0
        ).order_by('-created_at').first()
        
        # Contar transações de hoje
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        today_start = timezone.make_aware(
            datetime.combine(timezone.now().date(), datetime.min.time())
        )
        
        transactions_today = Transaction.objects.filter(
            ref_session__tap=tap,
            amount_cents__lt=0,
            created_at__gte=today_start
        ).count()
        
        return JsonResponse({
            'tap_id': tap.id,
            'name': tap.name,
            'is_active': tap.is_active,
            'dose_ml': tap.dose_ml,
            'price_cents': tap.price_cents,
            'last_transaction': last_transaction.created_at.isoformat() if last_transaction else None,
            'transactions_today': transactions_today
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