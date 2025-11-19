from django.db import transaction
from django.utils import timezone
import logging
from apps.accounts.models import Device
from .models import Tap, TapUsage

logger = logging.getLogger('lhctap.api')


class DeviceService:
    """Serviço simplificado para validação por device_id"""
    
    @staticmethod
    def validate_device(device_id, tap_id, ip_address=None, user_agent=None):
        """
        Valida device_id e libera tap se tudo estiver ok
        
        Args:
            device_id: ID do dispositivo (cartão RFID)
            tap_id: ID do tap a ser liberado
            ip_address: IP do cliente (opcional)
            user_agent: User agent do cliente (opcional)
            
        Returns:
            dict: Resultado da validação
        """
        result = 'ok'
        user = None
        tap = None
        device = None
        
        try:
            # Buscar device
            try:
                device = Device.objects.select_related().get(device_id=device_id)
            except Device.DoesNotExist:
                result = 'device_not_found'
                logger.warning(f"Device não encontrado: device_id={device_id}, tap_id={tap_id}, ip={ip_address}")
                # Registrar no histórico fora da transação
                TapUsage.objects.create(
                    device_id=device_id,
                    user=None,
                    tap=None,
                    result='device_not_found',
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
                return {
                    'ok': False,
                    'error': 'device_not_found',
                    'message': 'Dispositivo não encontrado'
                }
            
            # Verificar se device está ativo
            if device.status != 'active':
                result = 'device_inactive'
                logger.warning(f"Device inativo: device_id={device_id}, status={device.status}, tap_id={tap_id}, ip={ip_address}")
                TapUsage.objects.create(
                    device_id=device_id,
                    user=None,
                    tap=None,
                    result='device_inactive',
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
                return {
                    'ok': False,
                    'error': 'device_inactive',
                    'message': 'Dispositivo inativo'
                }
            
            # Verificar se device está vinculado a usuário
            users = device.users.all()
            if not users.exists():
                result = 'device_not_linked'
                logger.warning(f"Device não vinculado a usuário: device_id={device_id}, tap_id={tap_id}, ip={ip_address}")
                TapUsage.objects.create(
                    device_id=device_id,
                    user=None,
                    tap=None,
                    result='device_not_linked',
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
                return {
                    'ok': False,
                    'error': 'device_not_linked',
                    'message': 'Dispositivo não vinculado a nenhum usuário'
                }
            
            # Usar o primeiro usuário vinculado (se houver múltiplos, usar o primeiro)
            user = users.first()
            
            # Buscar tap
            try:
                tap = Tap.objects.get(id=tap_id)
            except Tap.DoesNotExist:
                result = 'tap_not_found'
                logger.warning(f"Tap não encontrado: device_id={device_id}, tap_id={tap_id}, user={user.username if user else 'N/A'}, ip={ip_address}")
                TapUsage.objects.create(
                    device_id=device_id,
                    user=user,
                    tap=None,
                    result='tap_not_found',
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
                return {
                    'ok': False,
                    'error': 'tap_not_found',
                    'message': 'Tap não encontrado'
                }
            
            # Verificar se tap está ativo
            if not tap.is_active:
                result = 'tap_inactive'
                logger.warning(f"Tap inativo: device_id={device_id}, tap_id={tap_id}, tap_name={tap.name}, user={user.username if user else 'N/A'}, ip={ip_address}")
                TapUsage.objects.create(
                    device_id=device_id,
                    user=user,
                    tap=tap,
                    result='tap_inactive',
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
                return {
                    'ok': False,
                    'error': 'tap_inactive',
                    'message': 'Tap inativo'
                }
            
            # Registro de uso bem-sucedido (dentro de transação atômica)
            with transaction.atomic():
                TapUsage.objects.create(
                    device_id=device_id,
                    user=user,
                    tap=tap,
                    result='ok',
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
            
            return {
                'ok': True,
                'message': 'Tap liberado com sucesso',
                'dose_ml': tap.dose_ml,
                'tap_name': tap.name,
                'tap_type': tap.get_type_display(),
                'user_name': user.get_full_name() or user.username,
                'device_name': device.name or device.device_id
            }
            
        except Exception as e:
            # Log do erro completo
            logger.error(
                f"Erro interno ao validar device: device_id={device_id}, tap_id={tap_id}, "
                f"user={user.username if user else 'N/A'}, tap={tap.name if tap else 'N/A'}, "
                f"ip={ip_address}, erro={str(e)}",
                exc_info=True
            )
            
            # Registrar erro no histórico (fora de transação para evitar problemas)
            try:
                TapUsage.objects.create(
                    device_id=device_id,
                    user=user,
                    tap=tap,
                    result='error',
                    ip_address=ip_address,
                    user_agent=user_agent or ''
                )
            except Exception as db_error:
                logger.error(f"Erro ao registrar TapUsage: {db_error}", exc_info=True)
            
            return {
                'ok': False,
                'error': 'internal_error',
                'message': 'Erro interno do servidor'
            }
    
    @staticmethod
    def get_usage_stats(user=None, tap=None, days=30):
        """Estatísticas de uso para dashboard"""
        from datetime import timedelta
        
        since = timezone.now() - timedelta(days=days)
        queryset = TapUsage.objects.filter(created_at__gte=since)
        
        if user:
            queryset = queryset.filter(user=user)
        if tap:
            queryset = queryset.filter(tap=tap)
        
        return {
            'total_uses': queryset.count(),
            'successful_uses': queryset.filter(result='ok').count(),
            'failed_uses': queryset.exclude(result='ok').count(),
        }
