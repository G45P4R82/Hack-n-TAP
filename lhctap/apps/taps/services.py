import secrets
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from django.db import models
from .models import TapSession, TapValidationAudit
from apps.core.exceptions import (
    TokenExpiredError, 
    TokenAlreadyUsedError, 
    InsufficientBalanceError,
    TapInactiveError
)


class TokenService:
    """Serviço para geração e validação de tokens QR"""
    
    TOKEN_EXPIRY_SECONDS = 30
    
    @staticmethod
    def generate_secure_token(length=32):
        """Gera token criptograficamente seguro"""
        return secrets.token_urlsafe(length)
    
    @classmethod
    def create_session(cls, user, tap):
        """Cria nova sessão de token para usuário e tap"""
        # Invalidar sessões pendentes anteriores
        cls.invalidate_pending_sessions(user, tap)
        
        return TapSession.objects.create(
            user=user,
            tap=tap,
            token=cls.generate_secure_token(),
            expires_at=timezone.now() + timedelta(seconds=cls.TOKEN_EXPIRY_SECONDS)
        )
    
    @staticmethod
    def invalidate_pending_sessions(user, tap):
        """Invalida sessões pendentes do usuário para o tap específico"""
        TapSession.objects.filter(
            user=user,
            tap=tap,
            status='pending'
        ).update(status='expired')
    
    @staticmethod
    def cleanup_expired_sessions():
        """Remove sessões expiradas (management command)"""
        expired_count = TapSession.objects.filter(
            expires_at__lt=timezone.now(),
            status='pending'
        ).update(status='expired')
        
        return expired_count
    
    @staticmethod
    def get_session_stats(days=30):
        """Estatísticas de sessões para dashboard admin"""
        since = timezone.now() - timedelta(days=days)
        
        return {
            'total_generated': TapSession.objects.filter(created_at__gte=since).count(),
            'successful_uses': TapSession.objects.filter(
                created_at__gte=since,
                status='used'
            ).count(),
            'expired_unused': TapSession.objects.filter(
                created_at__gte=since,
                status='expired'
            ).count()
        }
    
    @staticmethod
    def validate_token(token, device_id, ip_address=None, user_agent=None):
        """Valida token e processa consumo"""
        audit_result = 'not_found'
        session = None
        
        try:
            with transaction.atomic():
                # Buscar sessão com lock
                try:
                    session = TapSession.objects.select_for_update().get(
                        token=token,
                        status='pending'
                    )
                except TapSession.DoesNotExist:
                    return {
                        'ok': False,
                        'error': 'not_found',
                        'message': 'Token não encontrado'
                    }
                
                # Verificar expiração
                if session.is_expired():
                    session.status = 'expired'
                    session.save()
                    audit_result = 'expired'
                    return {
                        'ok': False,
                        'error': 'expired',
                        'message': 'Token expirado'
                    }
                
                # Verificar saldo
                wallet = session.user.wallet
                if not wallet.has_sufficient_balance(session.tap.price_cents):
                    audit_result = 'insufficient'
                    return {
                        'ok': False,
                        'error': 'insufficient',
                        'message': 'Saldo insuficiente'
                    }
                
                # Verificar tap ativo
                if not session.tap.is_active:
                    audit_result = 'tap_inactive'
                    return {
                        'ok': False,
                        'error': 'tap_inactive',
                        'message': 'Tap temporariamente indisponível'
                    }
                
                # Processar consumo
                from apps.wallet.services import WalletService
                transaction_record = WalletService.process_consumption(
                    session.user, session.tap, session
                )
                
                # Marcar sessão como usada
                session.mark_as_used()
                audit_result = 'ok'
                
                return {
                    'ok': True,
                    'dose_ml': session.tap.dose_ml,
                    'user_name': session.user.get_full_name() or session.user.username,
                    'tap_name': session.tap.name,
                    'remaining_balance_cents': wallet.balance_cents,
                    'transaction_id': transaction_record.id
                }
                
        except Exception as e:
            audit_result = 'error'
            return {
                'ok': False,
                'error': 'internal_error',
                'message': 'Erro interno do servidor'
            }
        
        finally:
            # Auditoria obrigatória
            TapValidationAudit.objects.create(
                device_id=device_id,
                token=token,
                result=audit_result,
                user=session.user if session else None,
                tap=session.tap if session else None,
                ip_address=ip_address,
                user_agent=user_agent or ''
            )
