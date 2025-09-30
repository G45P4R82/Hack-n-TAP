# 💻 Interface Web - LHC Tap System

## 🎯 Visão Geral

A interface web do LHC Tap System oferece uma experiência moderna e responsiva para usuários gerenciarem suas carteiras, gerarem tokens QR e visualizarem suas transações. O design segue princípios mobile-first com animações suaves e feedback visual imediato.

## 🏗️ Arquitetura Frontend

### Stack Tecnológica
- **Framework:** Django Templates + Bootstrap 5.3
- **CSS:** Bootstrap 5.3 + Custom CSS
- **JavaScript:** Vanilla JS + Anime.js
- **Icons:** Font Awesome 6.4
- **Fonts:** Google Fonts (Roboto)
- **Responsive:** Mobile-first design

### Estrutura de Templates

```
templates/
├── base.html                 # Template base
├── accounts/                 # Templates de autenticação
│   ├── login.html
│   ├── register.html
│   └── profile.html
├── dashboard/                # Dashboard principal
│   └── member.html
├── wallet/                   # Funcionalidades de carteira
│   ├── statement.html
│   └── add_credits.html
└── registration/             # Templates de registro
    └── login.html
```

## 🎨 Design System

### Paleta de Cores

**Cores Principais:**
- **Primary:** `#007bff` (Azul Bootstrap)
- **Success:** `#28a745` (Verde)
- **Danger:** `#dc3545` (Vermelho)
- **Warning:** `#ffc107` (Amarelo)
- **Info:** `#17a2b8` (Ciano)

**Cores Customizadas:**
- **Balance Card:** Gradiente `#667eea` → `#764ba2`
- **Tap Cards:** Hover com `translateY(-5px)`
- **Transaction Items:** Bordas coloridas por tipo

### Tipografia

**Font Family:**
```css
font-family: 'Roboto', sans-serif;
```

**Hierarquia:**
- **H1 (Display-4):** 2rem (mobile) / 3.5rem (desktop)
- **H2:** 1.5rem (mobile) / 2rem (desktop)
- **H5:** 1rem (mobile) / 1.25rem (desktop)
- **Body:** 16px (mobile-optimized)

### Componentes

#### Cards de Tap
```html
<div class="card tap-card h-100" data-tap-id="{{ tap.id }}">
    <div class="card-body">
        <h6 class="card-title text-primary">
            <i class="fas fa-beer me-1"></i>{{ tap.name }}
        </h6>
        <span class="badge bg-{{ tap.type|lower }}">
            {{ tap.get_type_display }}
        </span>
        <p class="card-text text-muted small">
            <i class="fas fa-tint me-1"></i>{{ tap.dose_ml }}ml
        </p>
        <div class="d-flex justify-content-between">
            <span class="h5 text-success">R$ {{ tap.price_cents|cents_to_reais }}</span>
            <button class="btn btn-primary btn-sm">
                <i class="fas fa-qrcode me-1"></i>Gerar QR
            </button>
        </div>
    </div>
</div>
```

#### Cards de Saldo
```html
<div class="card balance-card h-100">
    <div class="card-body text-center">
        <h5 class="card-title">
            <i class="fas fa-wallet me-2"></i>Saldo Atual
        </h5>
        <h2 class="mb-0">R$ {{ balance_summary.current_balance|cents_to_reais }}</h2>
    </div>
</div>
```

## 📱 Responsividade

### Breakpoints

**Mobile First:**
- **xs:** < 576px (Mobile)
- **sm:** ≥ 576px (Large Mobile)
- **md:** ≥ 768px (Tablet)
- **lg:** ≥ 992px (Desktop)
- **xl:** ≥ 1200px (Large Desktop)

### Otimizações Mobile

**Touch-Friendly:**
```css
.btn {
    min-height: 44px; /* Touch-friendly button size */
}

.credit-card, .tap-card {
    min-height: 80px;
    -webkit-tap-highlight-color: rgba(0,0,0,0.1);
}
```

**Prevenção de Zoom:**
```css
input, select, textarea {
    font-size: 16px; /* Previne zoom no iOS */
}
```

**Spacing Mobile:**
```css
@media (max-width: 768px) {
    .mb-4 { margin-bottom: 1.5rem !important; }
    .mt-4 { margin-top: 1.5rem !important; }
}
```

## 🎮 Funcionalidades Principais

### Dashboard Principal

**Localização:** `templates/dashboard/member.html`

**Funcionalidades:**
- Exibição de saldo atual
- Resumo financeiro (30 dias)
- Lista de taps disponíveis
- Últimas transações
- Geração de QR codes

**Layout:**
```html
<div class="container mt-4">
    <!-- Header -->
    <div class="row mb-4">
        <div class="col-12">
            <h1 class="display-4 text-primary">
                <i class="fas fa-tachometer-alt me-3"></i>Dashboard
            </h1>
        </div>
    </div>

    <!-- Balance Summary -->
    <div class="row mb-4">
        <div class="col-12 col-sm-6 col-lg-4 mb-3">
            <!-- Saldo Atual -->
        </div>
        <div class="col-12 col-sm-6 col-lg-4 mb-3">
            <!-- Total Recebido -->
        </div>
        <div class="col-12 col-sm-6 col-lg-4 mb-3">
            <!-- Total Gasto -->
        </div>
    </div>

    <div class="row">
        <div class="col-12 col-lg-8 mb-4">
            <!-- Taps Disponíveis -->
        </div>
        <div class="col-12 col-lg-4">
            <!-- Últimas Transações -->
        </div>
    </div>
</div>
```

### Geração de QR Code

**Fluxo de Interação:**
1. Usuário clica no card do tap
2. Sistema verifica saldo
3. Gera token seguro
4. Exibe modal com QR code
5. Inicia countdown de 30 segundos

**JavaScript:**
```javascript
function generateToken(tapId) {
    const tapCard = document.querySelector(`[data-tap-id="${tapId}"]`);
    const button = tapCard.querySelector('button');
    
    // Loading state
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Gerando...';
    button.disabled = true;

    fetch('/dashboard/generate-token/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: `tap_id=${tapId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Erro: ' + data.error);
        } else {
            showQRCode(data);
        }
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}
```

### Modal de QR Code

**Estrutura:**
```html
<div class="modal fade" id="qrModal" tabindex="-1">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">
                    <i class="fas fa-qrcode me-2"></i>Token QR Code
                </h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body text-center">
                <div id="qrCodeContainer">
                    <!-- QR Code será inserido aqui -->
                </div>
                <div class="mt-3">
                    <p class="mb-1"><strong>Tap:</strong> <span id="tapName"></span></p>
                    <p class="mb-1"><strong>Dose:</strong> <span id="doseMl"></span>ml</p>
                    <p class="mb-1"><strong>Preço:</strong> R$ <span id="price"></span></p>
                    <p class="mb-1"><strong>Expira em:</strong> <span id="expiresAt"></span></p>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Countdown Timer

**Implementação:**
```javascript
function startCountdown(expiresAt) {
    const expirationTime = new Date(expiresAt).getTime();
    const countdownElement = document.getElementById('expiresAt');
    
    const timer = setInterval(() => {
        const now = new Date().getTime();
        const distance = expirationTime - now;
        
        if (distance < 0) {
            clearInterval(timer);
            countdownElement.innerHTML = '<span class="text-danger">Expirado</span>';
            return;
        }
        
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        countdownElement.innerHTML = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }, 1000);
}
```

## 🎨 Animações e Interações

### CSS Transitions

**Hover Effects:**
```css
.tap-card {
    transition: transform 0.2s ease-in-out;
    cursor: pointer;
}

.tap-card:hover {
    transform: translateY(-5px);
}
```

**Loading States:**
```css
.btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.fa-spinner {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
```

### Anime.js Integration

**Fade In Animation:**
```javascript
// Animação de entrada dos cards
anime({
    targets: '.tap-card',
    opacity: [0, 1],
    translateY: [20, 0],
    delay: anime.stagger(100),
    duration: 600,
    easing: 'easeOutExpo'
});
```

**Pulse Animation:**
```javascript
// Animação de pulse para saldo
anime({
    targets: '.balance-card',
    scale: [1, 1.05, 1],
    duration: 2000,
    loop: true,
    easing: 'easeInOutSine'
});
```

## 📊 Extrato de Transações

### Página de Extrato

**Localização:** `templates/wallet/statement.html`

**Funcionalidades:**
- Filtro por período (7, 30, 90 dias)
- Lista paginada de transações
- Resumo financeiro
- Exportação (futuro)

**Layout:**
```html
<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <h1 class="display-4 text-primary">
                <i class="fas fa-receipt me-3"></i>Extrato
            </h1>
        </div>
    </div>

    <!-- Filtros -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="btn-group" role="group">
                <a href="?days=7" class="btn btn-outline-primary">7 dias</a>
                <a href="?days=30" class="btn btn-outline-primary active">30 dias</a>
                <a href="?days=90" class="btn btn-outline-primary">90 dias</a>
            </div>
        </div>
    </div>

    <!-- Transações -->
    <div class="row">
        <div class="col-12">
            <div class="list-group">
                {% for transaction in transactions %}
                <div class="list-group-item transaction-item">
                    <!-- Conteúdo da transação -->
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</div>
```

### Item de Transação

**Estrutura:**
```html
<div class="list-group-item transaction-item {% if transaction.amount_cents > 0 %}credit{% else %}debit{% endif %}">
    <div class="d-flex justify-content-between align-items-start">
        <div class="flex-grow-1">
            <h6 class="mb-1">
                {% if transaction.amount_cents > 0 %}
                    <i class="fas fa-plus-circle text-success me-1"></i>
                {% else %}
                    <i class="fas fa-minus-circle text-danger me-1"></i>
                {% endif %}
                {{ transaction.description }}
            </h6>
            <small class="text-muted">
                {{ transaction.created_at|date:"d/m/Y H:i" }}
            </small>
        </div>
        <span class="badge bg-{% if transaction.amount_cents > 0 %}success{% else %}danger{% endif %} ms-2">
            R$ {{ transaction.amount_cents|cents_to_reais_with_sign }}
        </span>
    </div>
</div>
```

## 💳 Recarga de Créditos

### Página de Recarga

**Localização:** `templates/wallet/add_credits.html`

**Funcionalidades:**
- Valores pré-definidos
- Validação de valores
- Feedback visual
- Atualização de saldo em tempo real

**Layout:**
```html
<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <h1 class="display-4 text-primary">
                <i class="fas fa-plus-circle me-3"></i>Adicionar Créditos
            </h1>
        </div>
    </div>

    <!-- Saldo Atual -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card bg-primary text-white">
                <div class="card-body text-center">
                    <h5>Saldo Atual</h5>
                    <h2>R$ {{ wallet.get_balance_display }}</h2>
                </div>
            </div>
        </div>
    </div>

    <!-- Opções de Crédito -->
    <div class="row">
        {% for option in credit_options %}
        <div class="col-12 col-sm-6 col-md-4 col-lg-3 mb-3">
            <div class="card credit-card h-100" data-amount="{{ option.value }}">
                <div class="card-body text-center">
                    <h5 class="card-title">{{ option.display }}</h5>
                    <p class="card-text text-muted">{{ option.description }}</p>
                    <button class="btn btn-success">Adicionar</button>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

### Processamento de Créditos

**JavaScript:**
```javascript
document.addEventListener('DOMContentLoaded', function() {
    const creditCards = document.querySelectorAll('.credit-card');
    creditCards.forEach(card => {
        card.addEventListener('click', function() {
            const amount = this.getAttribute('data-amount');
            addCredits(amount);
        });
    });
});

function addCredits(amountCents) {
    const button = event.target;
    const originalText = button.innerHTML;
    
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processando...';
    button.disabled = true;

    fetch('/dashboard/process-credits/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: `amount_cents=${amountCents}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Atualizar saldo na tela
            updateBalance(data.new_balance);
            
            // Mostrar sucesso
            showSuccessMessage(data.message);
        } else {
            showErrorMessage(data.error);
        }
    })
    .finally(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    });
}
```

## 🧭 Navegação

### Navbar Responsiva

**Estrutura:**
```html
<nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container">
        <a class="navbar-brand" href="{% url 'wallet:dashboard' %}">
            <i class="fas fa-beer me-2"></i>LHC Tap
        </a>
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav me-auto">
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'wallet:dashboard' %}">
                        <i class="fas fa-tachometer-alt me-1"></i>Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'wallet:statement' %}">
                        <i class="fas fa-receipt me-1"></i>Extrato
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="{% url 'wallet:add_credits' %}">
                        <i class="fas fa-plus-circle me-1"></i>Recarregar
                    </a>
                </li>
            </ul>
            
            <ul class="navbar-nav">
                <li class="nav-item dropdown">
                    <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                        <i class="fas fa-user me-1"></i>{{ user.get_full_name|default:user.username }}
                    </a>
                    <ul class="dropdown-menu dropdown-menu-end">
                        <!-- Menu items -->
                    </ul>
                </li>
            </ul>
        </div>
    </div>
</nav>
```

### Breadcrumbs

**Implementação:**
```html
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{% url 'wallet:dashboard' %}">Dashboard</a></li>
        <li class="breadcrumb-item active" aria-current="page">Extrato</li>
    </ol>
</nav>
```

## 🔔 Sistema de Notificações

### Messages Framework

**Template:**
```html
{% if messages %}
<div class="container mt-3">
    {% for message in messages %}
    <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
        {{ message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

### Toast Notifications

**JavaScript:**
```javascript
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove após 5 segundos
    setTimeout(() => {
        toast.remove();
    }, 5000);
}
```

## 🎯 Performance Frontend

### Otimizações

**Lazy Loading:**
```javascript
// Carregar QR codes apenas quando necessário
function generateRealQRCode(token) {
    fetch(`/dashboard/qr-image/${token}/`)
        .then(response => response.json())
        .then(data => {
            if (data.qr_code) {
                showQRCode(data.qr_code);
            }
        });
}
```

**Debouncing:**
```javascript
// Debounce para pesquisas
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
```

**Caching:**
```javascript
// Cache de dados do dashboard
const dashboardCache = new Map();

function getDashboardData() {
    if (dashboardCache.has('dashboard')) {
        return Promise.resolve(dashboardCache.get('dashboard'));
    }
    
    return fetch('/dashboard/data/')
        .then(response => response.json())
        .then(data => {
            dashboardCache.set('dashboard', data);
            return data;
        });
}
```

## 🧪 Testes Frontend

### Testes de Interface

**Cypress (Recomendado):**
```javascript
describe('Dashboard', () => {
    it('should display user balance', () => {
        cy.visit('/dashboard/');
        cy.get('.balance-card').should('contain', 'R$');
    });
    
    it('should generate QR code', () => {
        cy.visit('/dashboard/');
        cy.get('.tap-card').first().click();
        cy.get('#qrModal').should('be.visible');
        cy.get('#qrCodeContainer').should('contain', 'QR Code');
    });
});
```

**Jest + Testing Library:**
```javascript
import { render, screen, fireEvent } from '@testing-library/react';

test('should show loading state when generating token', () => {
    render(<TapCard tap={mockTap} />);
    
    const button = screen.getByText('Gerar QR');
    fireEvent.click(button);
    
    expect(screen.getByText('Gerando...')).toBeInTheDocument();
});
```

## 🔧 Customização e Temas

### Variáveis CSS

**Custom Properties:**
```css
:root {
    --primary-color: #007bff;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
    
    --border-radius: 0.375rem;
    --box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    --transition: all 0.15s ease-in-out;
}
```

### Tema Escuro

**Implementação:**
```css
[data-bs-theme="dark"] {
    --bs-body-bg: #212529;
    --bs-body-color: #fff;
    --bs-primary: #0d6efd;
    --bs-success: #198754;
    --bs-danger: #dc3545;
}
```

## 📱 PWA (Progressive Web App)

### Manifest

**manifest.json:**
```json
{
    "name": "LHC Tap System",
    "short_name": "LHC Tap",
    "description": "Sistema de controle de consumo em taps",
    "start_url": "/dashboard/",
    "display": "standalone",
    "background_color": "#007bff",
    "theme_color": "#007bff",
    "icons": [
        {
            "src": "/static/icons/icon-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        }
    ]
}
```

### Service Worker

**sw.js:**
```javascript
const CACHE_NAME = 'lhctap-v1';
const urlsToCache = [
    '/',
    '/static/css/main.css',
    '/static/js/dashboard.js'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
```
