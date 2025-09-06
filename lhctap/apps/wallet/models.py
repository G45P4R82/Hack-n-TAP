from django.db import models
from django.contrib.auth.models import User


class Wallet(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance_cents = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance_cents__gte=0),
                name='positive_balance'
            )
        ]
    
    def __str__(self):
        return f"Wallet de {self.user.username}: R$ {self.get_balance_display()}"
    
    def get_balance_display(self):
        """Formata o saldo para exibição (R$ X,XX)"""
        return f"{self.balance_cents / 100:.2f}"
    
    def has_sufficient_balance(self, amount_cents):
        """Verifica se há saldo suficiente"""
        return self.balance_cents >= amount_cents
    
    def debit(self, amount_cents):
        """Débito com validação de saldo suficiente"""
        if not self.has_sufficient_balance(amount_cents):
            raise ValueError("Saldo insuficiente")
        self.balance_cents -= amount_cents
        self.save()
    
    def credit(self, amount_cents):
        """Crédito com validação de valor positivo"""
        if amount_cents <= 0:
            raise ValueError("Valor deve ser positivo")
        self.balance_cents += amount_cents
        self.save()


class Transaction(models.Model):
    CATEGORY_CHOICES = [
        ('beer', 'Chope'),
        ('mate', 'Mate'),
        ('topup', 'Recarga'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_cents = models.IntegerField()
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES)
    volume_ml = models.PositiveIntegerField(default=0)
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ref_session = models.ForeignKey(
        'taps.TapSession',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(category__in=['beer', 'mate'], amount_cents__lt=0, volume_ml__gt=0) |
                    models.Q(category='topup', amount_cents__gt=0, volume_ml=0)
                ),
                name='valid_transaction_type'
            )
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_category_display()}: {self.get_amount_display()}"
    
    def get_amount_display(self):
        """Formatação monetária com sinal"""
        amount = self.amount_cents / 100
        if self.amount_cents > 0:
            return f"+R$ {amount:.2f}"
        else:
            return f"R$ {amount:.2f}"
