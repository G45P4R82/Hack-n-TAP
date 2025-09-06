from django.db import models
from django.contrib.auth.models import User


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
