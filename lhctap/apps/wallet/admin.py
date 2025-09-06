from django.contrib import admin
from django.utils.html import format_html
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance_display', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['updated_at']
    
    def balance_display(self, obj):
        return format_html(
            '<span style="color: {};">R$ {:.2f}</span>',
            'green' if obj.balance_cents > 0 else 'red',
            obj.balance_cents / 100
        )
    balance_display.short_description = 'Saldo'
    
    fieldsets = (
        ('Informações da Carteira', {
            'fields': ('user', 'balance_cents')
        }),
        ('Metadados', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount_display', 'volume_ml', 'description', 'created_at']
    list_filter = ['category', 'created_at', 'ref_session__tap']
    search_fields = ['user__username', 'description', 'ref_session__tap__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
    
    def amount_display(self, obj):
        color = 'green' if obj.amount_cents > 0 else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_amount_display()
        )
    amount_display.short_description = 'Valor'
    
    fieldsets = (
        ('Informações da Transação', {
            'fields': ('user', 'amount_cents', 'category', 'volume_ml', 'description')
        }),
        ('Referências', {
            'fields': ('ref_session',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )