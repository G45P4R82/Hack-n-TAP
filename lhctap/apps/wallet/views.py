import json
import qrcode
import io
import base64
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
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
def generate_qr_image(request, token):
    """Gera imagem do QR Code para o token"""
    try:
        # Verificar se o token pertence ao usuário
        from apps.taps.models import TapSession
        session = TapSession.objects.get(
            token=token,
            user=request.user,
            status='pending'
        )
        
        # Verificar se não expirou
        if session.is_expired():
            return HttpResponse("Token expirado", status=410)
        
        # Criar QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(token)
        qr.make(fit=True)
        
        # Criar imagem
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return JsonResponse({
            'qr_code': f"data:image/png;base64,{img_str}",
            'token': token,
            'expires_at': session.expires_at.isoformat()
        })
        
    except TapSession.DoesNotExist:
        return JsonResponse({'error': 'Token não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Erro ao gerar QR Code'}, status=500)


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
def add_credits(request):
    """Página para adicionar créditos à carteira"""
    # Valores pré-definidos de crédito
    credit_options = [
        {'value': 3000, 'display': 'R$ 30,00', 'description': 'Recarga básica'},
        {'value': 4000, 'display': 'R$ 40,00', 'description': 'Recarga média'},
        {'value': 5000, 'display': 'R$ 50,00', 'description': 'Recarga premium'},
        {'value': 10000, 'display': 'R$ 100,00', 'description': 'Recarga grande'},
        {'value': 20000, 'display': 'R$ 200,00', 'description': 'Recarga máxima'},
    ]
    
    context = {
        'credit_options': credit_options,
        'wallet': request.user.wallet,
    }
    
    return render(request, 'wallet/add_credits.html', context)


@login_required
@require_http_methods(["POST"])
def process_credits(request):
    """Processa adição de créditos à carteira"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Processando créditos para usuário: {request.user.username}")
        
        amount_cents = request.POST.get('amount_cents')
        logger.info(f"Valor recebido: {amount_cents}")
        
        if not amount_cents:
            logger.warning("Valor não fornecido")
            return JsonResponse({
                'error': 'Valor é obrigatório'
            }, status=400)
        
        try:
            amount_cents = int(amount_cents)
        except ValueError:
            logger.warning(f"Valor inválido: {amount_cents}")
            return JsonResponse({
                'error': 'Valor inválido'
            }, status=400)
        
        if amount_cents <= 0:
            logger.warning(f"Valor não positivo: {amount_cents}")
            return JsonResponse({
                'error': 'Valor deve ser positivo'
            }, status=400)
        
        # Valores permitidos (em centavos)
        allowed_amounts = [3000, 4000, 5000, 10000, 20000]
        if amount_cents not in allowed_amounts:
            logger.warning(f"Valor não permitido: {amount_cents}")
            return JsonResponse({
                'error': 'Valor não permitido'
            }, status=400)
        
        logger.info(f"Adicionando {amount_cents} centavos para {request.user.username}")
        
        # Adicionar créditos usando o serviço
        transaction = WalletService.add_credits(
            request.user, 
            amount_cents, 
            f"Recarga de R$ {amount_cents/100:.2f}"
        )
        
        # Atualizar o saldo do usuário
        request.user.wallet.refresh_from_db()
        
        logger.info(f"Créditos adicionados com sucesso. Novo saldo: {request.user.wallet.balance_cents}")
        
        return JsonResponse({
            'success': True,
            'message': f'Créditos adicionados com sucesso!',
            'new_balance': request.user.wallet.balance_cents,
            'amount_added': amount_cents,
            'transaction_id': transaction.id
        })
        
    except Exception as e:
        logger.error(f"Erro ao processar créditos: {str(e)}", exc_info=True)
        return JsonResponse({
            'error': f'Erro interno do servidor: {str(e)}'
        }, status=500)


@login_required
def profile(request):
    """Perfil do usuário"""
    context = {
        'user': request.user,
        'profile': request.user.profile,
        'wallet': request.user.wallet,
    }
    
    return render(request, 'accounts/profile.html', context)