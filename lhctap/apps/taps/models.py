from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class Tap(models.Model):
    TYPE_CHOICES = [
        ('beer', 'Chope'),
        ('mate', 'Mate'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    location = models.CharField(max_length=120, blank=True, null=True)
    dose_ml = models.PositiveIntegerField(default=300)
    price_cents = models.PositiveIntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'taps'
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['location']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(dose_ml__gt=0),
                name='positive_dose'
            ),
            models.CheckConstraint(
                check=models.Q(price_cents__gt=0),
                name='positive_price'
            )
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def get_price_display(self):
        """Formatação monetária"""
        return f"R$ {self.price_cents / 100:.2f}"
    
    def is_available(self):
        """Verifica disponibilidade operacional"""
        return self.is_active


class TapSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pendente'),
        ('used', 'Utilizado'),
        ('expired', 'Expirado'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tap = models.ForeignKey(Tap, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tap_sessions'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'tap']),
            models.Index(fields=['expires_at']),
            models.Index(
                fields=['status'],
                condition=models.Q(status='pending'),
                name='pending_sessions_idx'
            ),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(expires_at__gt=models.F('created_at')),
                name='valid_expiration'
            )
        ]
    
    def __str__(self):
        return f"Session {self.token[:8]}... - {self.user.username} - {self.tap.name}"
    
    def is_expired(self):
        """Verifica se o token está expirado"""
        return timezone.now() > self.expires_at
    
    def mark_as_used(self):
        """Marca como utilizado"""
        self.status = 'used'
        self.used_at = timezone.now()
        self.save()


class TapValidationAudit(models.Model):
    RESULT_CHOICES = [
        ('ok', 'Sucesso'),
        ('expired', 'Token Expirado'),
        ('used', 'Token Já Utilizado'),
        ('insufficient', 'Saldo Insuficiente'),
        ('not_found', 'Token Não Encontrado'),
        ('rate_limited', 'Rate Limit Excedido'),
        ('tap_inactive', 'Tap Inativo'),
    ]
    
    device_id = models.CharField(max_length=64)
    token = models.CharField(max_length=64)
    result = models.CharField(max_length=16, choices=RESULT_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    tap = models.ForeignKey(Tap, on_delete=models.SET_NULL, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'tap_validations_audit'
        indexes = [
            models.Index(fields=['device_id', '-created_at']),
            models.Index(fields=['token']),
            models.Index(fields=['result', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Audit {self.device_id} - {self.result} - {self.created_at}"
    
    def get_success_rate(self):
        """Calcula taxa de sucesso para métricas"""
        # Será implementado posteriormente
        return 0
