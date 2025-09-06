// LHC Tap System - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips do Bootstrap
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializar popovers do Bootstrap
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts após 5 segundos
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Adicionar animação de entrada para cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
});

// Função utilitária para formatar moeda
function formatCurrency(cents) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(cents / 100);
}

// Função utilitária para obter token CSRF
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
           document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

// Função para mostrar loading
function showLoading(element) {
    element.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div>';
}

// Função para mostrar erro
function showError(element, message) {
    element.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> ${message}</div>`;
}
