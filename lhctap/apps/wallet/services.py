from django.db import transaction
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .models import Wallet, Transaction
from apps.core.exceptions import InsufficientBalanceError


class WalletService:
    """Serviço para operações financeiras com transações atômicas"""
    
    @staticmethod
    @transaction.atomic
    def process_consumption(user, tap, session):
        """Processa consumo: débito + transação + atualização de sessão"""
        wallet = user.wallet
        
        # Verificação de saldo com lock
        wallet = Wallet.objects.select_for_update().get(user=user)
        
        if wallet.balance_cents < tap.price_cents:
            raise InsufficientBalanceError(
                f"Saldo insuficiente: {wallet.balance_cents} < {tap.price_cents}"
            )
        
        # Débito atômico
        wallet.balance_cents -= tap.price_cents
        wallet.save()
        
        # Registro da transação
        transaction_record = Transaction.objects.create(
            user=user,
            amount_cents=-tap.price_cents,
            category=tap.type,
            volume_ml=tap.dose_ml,
            description=f"Consumo em {tap.name}",
            ref_session=session
        )
        
        return transaction_record
    
    @staticmethod
    @transaction.atomic
    def add_credits(user, amount_cents, description="Recarga manual"):
        """Adiciona créditos à carteira do usuário"""
        if amount_cents <= 0:
            raise ValueError("Valor deve ser positivo")
        
        wallet = Wallet.objects.select_for_update().get(user=user)
        wallet.balance_cents += amount_cents
        wallet.save()
        
        return Transaction.objects.create(
            user=user,
            amount_cents=amount_cents,
            category='topup',
            volume_ml=0,
            description=description
        )
    
    @staticmethod
    def get_user_statement(user, days=30):
        """Extrato do usuário com paginação"""
        since = timezone.now() - timedelta(days=days)
        
        return Transaction.objects.filter(
            user=user,
            created_at__gte=since
        ).select_related('ref_session__tap').order_by('-created_at')
    
    @staticmethod
    def get_balance_summary(user):
        """Resumo financeiro do usuário"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_transactions = Transaction.objects.filter(
            user=user,
            created_at__gte=thirty_days_ago
        )
        
        consumed = recent_transactions.filter(
            amount_cents__lt=0
        ).aggregate(
            total=models.Sum('amount_cents'),
            volume=models.Sum('volume_ml')
        )
        
        topped_up = recent_transactions.filter(
            amount_cents__gt=0
        ).aggregate(total=models.Sum('amount_cents'))
        
        return {
            'current_balance': user.wallet.balance_cents,
            'consumed_30d': abs(consumed['total'] or 0),
            'volume_30d': consumed['volume'] or 0,
            'topped_up_30d': topped_up['total'] or 0,
            'transaction_count': recent_transactions.count()
        }
