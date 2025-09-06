from django.contrib import admin
from django.utils.html import format_html
from .models import Tap, TapSession, TapValidationAudit


@admin.register(Tap)
class TapAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'location', 'dose_ml', 'price_display', 'is_active', 'created_at']
    list_filter = ['type', 'is_active', 'location', 'created_at']
    search_fields = ['name', 'location']
    readonly_fields = ['created_at', 'updated_at']
    
    def price_display(self, obj):
        return format_html(
            '<span style="color: green;">R$ {:.2f}</span>',
            obj.price_cents / 100
        )
    price_display.short_description = 'Preço'
    
    fieldsets = (
        ('Informações do Tap', {
            'fields': ('name', 'type', 'location', 'dose_ml', 'price_cents', 'is_active')
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TapSession)
class TapSessionAdmin(admin.ModelAdmin):
    list_display = ['token_short', 'user', 'tap', 'status', 'created_at', 'expires_at', 'used_at']
    list_filter = ['status', 'tap__type', 'created_at', 'expires_at']
    search_fields = ['token', 'user__username', 'tap__name']
    readonly_fields = ['token', 'created_at', 'expires_at', 'used_at']
    date_hierarchy = 'created_at'
    
    def token_short(self, obj):
        return f"{obj.token[:8]}..."
    token_short.short_description = 'Token'
    
    fieldsets = (
        ('Informações da Sessão', {
            'fields': ('user', 'tap', 'token', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at', 'used_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TapValidationAudit)
class TapValidationAuditAdmin(admin.ModelAdmin):
    list_display = ['device_id', 'token_short', 'result', 'user', 'tap', 'ip_address', 'created_at']
    list_filter = ['result', 'created_at', 'device_id']
    search_fields = ['device_id', 'token', 'user__username', 'tap__name', 'ip_address']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def token_short(self, obj):
        return f"{obj.token[:8]}..."
    token_short.short_description = 'Token'
    
    fieldsets = (
        ('Informações da Validação', {
            'fields': ('device_id', 'token', 'result', 'user', 'tap')
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
        return False  # Logs de auditoria não devem ser criados manualmente