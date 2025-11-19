from django.db import models
from django.contrib.auth.models import User


class Device(models.Model):
    """Modelo para cartões RFID e dispositivos vinculados aos usuários"""
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('lost', 'Perdido'),
        ('blocked', 'Bloqueado'),
    ]
    
    device_id = models.CharField(
        max_length=64,
        unique=True,
        verbose_name='ID do Dispositivo',
        help_text='ID único do cartão RFID ou dispositivo'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='Nome do Dispositivo',
        help_text='Nome descritivo do dispositivo (ex: Cartão Principal, Cartão Reserva)',
        blank=True
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Status'
    )
    users = models.ManyToManyField(
        User,
        related_name='devices',
        blank=True,
        verbose_name='Usuários Vinculados',
        help_text='Usuários que têm acesso a este dispositivo'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='Observações',
        help_text='Notas adicionais sobre o dispositivo'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    
    class Meta:
        db_table = 'devices'
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        if self.name:
            return f"{self.name} ({self.device_id})"
        return f"Dispositivo {self.device_id}"
    
    def get_status_display_color(self):
        """Retorna cor CSS para status"""
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'lost': 'orange',
            'blocked': 'red',
        }
        return colors.get(self.status, 'gray')
    
    def is_active(self):
        """Verifica se o dispositivo está ativo"""
        return self.status == 'active'


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('member', 'Membro'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='member'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        indexes = [
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        return self.role == 'admin'
