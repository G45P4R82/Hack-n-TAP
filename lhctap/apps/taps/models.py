from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Tap(models.Model):
    TYPE_CHOICES = [
        ('beer', 'Chope'),
        ('mate', 'Mate'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='Nome')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, verbose_name='Tipo')
    location = models.CharField(max_length=120, blank=True, null=True, verbose_name='Localização')
    dose_ml = models.PositiveIntegerField(default=300, verbose_name='Dose (ml)')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        db_table = 'taps'
        verbose_name = 'Tap'
        verbose_name_plural = 'Taps'
        indexes = [
            models.Index(fields=['type', 'is_active']),
            models.Index(fields=['location']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(dose_ml__gt=0),
                name='positive_dose'
            )
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def is_available(self):
        """Verifica disponibilidade operacional"""
        return self.is_active


class TapUsage(models.Model):
    """Histórico de uso dos taps - registro simplificado"""
    
    RESULT_CHOICES = [
        ('ok', 'Sucesso'),
        ('device_not_found', 'Dispositivo Não Encontrado'),
        ('device_inactive', 'Dispositivo Inativo'),
        ('device_not_linked', 'Dispositivo Não Vinculado'),
        ('tap_inactive', 'Tap Inativo'),
        ('rate_limited', 'Rate Limit Excedido'),
    ]
    
    device_id = models.CharField(max_length=64, verbose_name='ID do Dispositivo')
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        verbose_name='Usuário'
    )
    tap = models.ForeignKey(
        Tap, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
        verbose_name='Tap'
    )
    result = models.CharField(
        max_length=20, 
        choices=RESULT_CHOICES,
        verbose_name='Resultado'
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    
    class Meta:
        db_table = 'tap_usage'
        verbose_name = 'Uso do Tap'
        verbose_name_plural = 'Histórico de Uso'
        indexes = [
            models.Index(fields=['device_id', '-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['tap', '-created_at']),
            models.Index(fields=['result', '-created_at']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        user_name = self.user.username if self.user else 'N/A'
        tap_name = self.tap.name if self.tap else 'N/A'
        return f"{user_name} - {tap_name} - {self.get_result_display()} - {self.created_at}"
    
    @property
    def is_success(self):
        """Verifica se o uso foi bem-sucedido"""
        return self.result == 'ok'
