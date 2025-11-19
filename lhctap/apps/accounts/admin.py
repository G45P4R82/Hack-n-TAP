from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, Device


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


class UserDeviceInline(admin.TabularInline):
    """Inline para vincular dispositivos aos usuários"""
    model = Device.users.through
    extra = 1
    verbose_name = 'Dispositivo Vinculado'
    verbose_name_plural = 'Dispositivos Vinculados'
    raw_id_fields = ['device']


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, UserDeviceInline)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Admin para gerenciar dispositivos (cartões RFID)"""
    list_display = ['device_id', 'name', 'status', 'user_count', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['device_id', 'name', 'notes', 'users__username', 'users__email']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['users']
    
    fieldsets = (
        ('Informações do Dispositivo', {
            'fields': ('device_id', 'name', 'status')
        }),
        ('Usuários Vinculados', {
            'fields': ('users',),
            'description': 'Selecione os usuários que terão acesso a este dispositivo (cartão RFID)'
        }),
        ('Observações', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count(self, obj):
        """Mostra quantidade de usuários vinculados"""
        count = obj.users.count()
        if count == 0:
            return "Nenhum usuário"
        elif count == 1:
            return "1 usuário"
        else:
            return f"{count} usuários"
    user_count.short_description = 'Usuários Vinculados'
    
    def get_queryset(self, request):
        """Otimizar consultas com prefetch"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('users')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'created_at', 'updated_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Usuário', {
            'fields': ('user', 'role')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )