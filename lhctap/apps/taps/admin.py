from django.contrib import admin
from django.utils.html import format_html
from .models import Tap, TapUsage


@admin.register(Tap)
class TapAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'location', 'dose_ml', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'location', 'created_at']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Tap', {
            'fields': ('name', 'type', 'location', 'dose_ml', 'is_active')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TapUsage)
class TapUsageAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'user', 'tap', 'result_display', 'created_at']
    list_filter = ['result', 'created_at', 'tap']
    search_fields = ['device_id', 'user__username', 'tap__name', 'ip_address']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def result_display(self, obj):
        """Mostra resultado com cor"""
        colors = {
            'ok': 'green',
            'device_not_found': 'red',
            'device_inactive': 'orange',
            'device_not_linked': 'orange',
            'tap_inactive': 'orange',
            'rate_limited': 'red',
        }
        color = colors.get(obj.result, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_result_display()
        )
    result_display.short_description = 'Resultado'
    
    fieldsets = (
        ('Informações do Uso', {
            'fields': ('device_id', 'user', 'tap', 'result')
        }),
        ('Metadados de Segurança', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # Logs de uso não devem ser criados manualmente
    
    def has_change_permission(self, request, obj=None):
        return False  # Logs de uso não devem ser editados manualmente
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Apenas superuser pode deletar logs
