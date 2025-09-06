import json
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from .models import Wallet, Transaction
from .services import WalletService
from apps.taps.models import Tap
from apps.taps.services import TokenService


@login_required
def dashboard(request):
    """Dashboard principal do usuário"""
    # Obter taps disponíveis
    available_taps = Tap.objects.filter(is_active=True).order_by('type', 'name')
    
    # Obter resumo financeiro
    balance_summary = WalletService.get_balance_summary(request.user)
    
    # Obter últimas transações
    recent_transactions = WalletService.get_user_statement(request.user, days=7)[:10]
    
    context = {
        'available_taps': available_taps,
        'balance_summary': balance_summary,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'dashboard/member.html', context)


@login_required
@require_http_methods(["POST"])
def generate_token(request):
    """Gera token QR para consumo em tap"""
    try:
        tap_id = request.POST.get('tap_id')
        
        if not tap_id:
            return JsonResponse({
                'error': 'Tap ID é obrigatório'
            }, status=400)
        
        try:
            tap = Tap.objects.get(id=tap_id, is_active=True)
        except Tap.DoesNotExist:
            return JsonResponse({
                'error': 'Tap não encontrado ou inativo'
            }, status=404)
        
        # Verificar saldo
        if not request.user.wallet.has_sufficient_balance(tap.price_cents):
            return JsonResponse({
                'error': 'Saldo insuficiente',
                'required': tap.price_cents,
                'available': request.user.wallet.balance_cents
            }, status=400)
        
        # Criar sessão de token
        session = TokenService.create_session(request.user, tap)
        
        return JsonResponse({
            'token': session.token,
            'expires_at': session.expires_at.isoformat(),
            'tap_name': tap.name,
            'dose_ml': tap.dose_ml,
            'price_cents': tap.price_cents
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Erro interno do servidor'
        }, status=500)


@login_required
def statement(request):
    """Extrato detalhado do usuário"""
    # Obter parâmetros de filtro
    days = int(request.GET.get('days', 30))
    
    # Obter transações
    transactions = WalletService.get_user_statement(request.user, days=days)
    
    # Obter resumo
    balance_summary = WalletService.get_balance_summary(request.user)
    
    context = {
        'transactions': transactions,
        'balance_summary': balance_summary,
        'days': days,
    }
    
    return render(request, 'wallet/statement.html', context)


@login_required
def profile(request):
    """Perfil do usuário"""
    context = {
        'user': request.user,
        'profile': request.user.profile,
        'wallet': request.user.wallet,
    }
    
    return render(request, 'accounts/profile.html', context)