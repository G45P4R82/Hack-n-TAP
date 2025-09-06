class TapDashboard {
    constructor() {
        this.qrModal = new bootstrap.Modal(document.getElementById('qrModal'));
        this.countdownInterval = null;
        this.init();
    }
    
    init() {
        // Event listeners para botões de gerar QR
        document.querySelectorAll('.generate-qr-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tapId = e.target.dataset.tapId;
                const tapName = e.target.dataset.tapName;
                const price = e.target.dataset.price;
                this.generateQRCode(tapId, tapName, price);
            });
        });
        
        // Animações de entrada para cards
        this.animateCards();
        
        // Auto-refresh do saldo a cada 30 segundos
        setInterval(() => this.refreshBalance(), 30000);
    }
    
    async generateQRCode(tapId, tapName, price) {
        try {
            // Mostrar loading
            this.showQRLoading();
            
            const response = await fetch('/dashboard/generate-token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: `tap_id=${tapId}`
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.displayQRCode(data.token, tapName, data.expires_at);
                this.startCountdown(data.expires_at);
            } else {
                this.showError(data.error || 'Erro ao gerar QR code');
            }
        } catch (error) {
            console.error('Erro:', error);
            this.showError('Erro de conexão. Tente novamente.');
        }
    }
    
    displayQRCode(token, tapName, expiresAt) {
        // Limpar container anterior
        const container = document.getElementById('qr-container');
        container.innerHTML = '';
        
        // Gerar QR code
        QRCode.toCanvas(container, token, {
            width: 200,
            height: 200,
            colorDark: '#000000',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.M
        });
        
        // Atualizar título do modal
        document.getElementById('modal-tap-name').textContent = tapName;
        
        // Mostrar modal
        this.qrModal.show();
        
        // Animação de entrada do QR
        anime({
            targets: container.querySelector('canvas'),
            scale: [0, 1],
            rotate: [180, 0],
            duration: 600,
            easing: 'easeOutElastic(1, .8)'
        });
    }
    
    startCountdown(expiresAt) {
        const expirationTime = new Date(expiresAt).getTime();
        const totalDuration = 30000; // 30 segundos
        
        this.countdownInterval = setInterval(() => {
            const now = new Date().getTime();
            const timeLeft = expirationTime - now;
            
            if (timeLeft <= 0) {
                this.expireQRCode();
                return;
            }
            
            const secondsLeft = Math.ceil(timeLeft / 1000);
            const progressPercent = (timeLeft / totalDuration) * 100;
            
            // Atualizar timer
            document.getElementById('countdown-timer').textContent = secondsLeft;
            
            // Atualizar progress bar
            const progressBar = document.getElementById('countdown-progress');
            progressBar.style.width = `${progressPercent}%`;
            
            // Mudar cor quando restam poucos segundos
            if (secondsLeft <= 10) {
                progressBar.classList.remove('bg-success');
                progressBar.classList.add('bg-warning');
            }
            if (secondsLeft <= 5) {
                progressBar.classList.remove('bg-warning');
                progressBar.classList.add('bg-danger');
            }
        }, 100);
    }
    
    expireQRCode() {
        clearInterval(this.countdownInterval);
        
        // Animação de expiração
        anime({
            targets: '#qr-container canvas',
            opacity: [1, 0.3],
            scale: [1, 0.8],
            duration: 500
        });
        
        // Mostrar mensagem de expiração
        const container = document.getElementById('qr-container');
        const expiredMsg = document.createElement('div');
        expiredMsg.className = 'alert alert-danger mt-2';
        expiredMsg.innerHTML = '<i class="fas fa-clock"></i> QR Code expirado. Gere um novo.';
        container.appendChild(expiredMsg);
        
        // Desabilitar progress bar
        document.getElementById('countdown-progress').style.width = '0%';
        document.getElementById('countdown-timer').textContent = '0';
    }
    
    showQRLoading() {
        document.getElementById('modal-tap-name').textContent = 'Gerando...';
        document.getElementById('qr-container').innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
        `;
        this.qrModal.show();
    }
    
    showError(message) {
        const container = document.getElementById('qr-container');
        container.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> ${message}
            </div>
        `;
    }
    
    animateCards() {
        // Animação de entrada para cards dos taps
        anime({
            targets: '.tap-card',
            translateY: [50, 0],
            opacity: [0, 1],
            delay: anime.stagger(100),
            duration: 600,
            easing: 'easeOutQuad'
        });
        
        // Hover effect para cards
        document.querySelectorAll('.tap-card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                anime({
                    targets: card,
                    scale: 1.05,
                    duration: 200,
                    easing: 'easeOutQuad'
                });
            });
            
            card.addEventListener('mouseleave', () => {
                anime({
                    targets: card,
                    scale: 1,
                    duration: 200,
                    easing: 'easeOutQuad'
                });
            });
        });
    }
    
    async refreshBalance() {
        try {
            // Simular atualização do saldo (será implementado endpoint específico)
            const balanceElement = document.getElementById('current-balance');
            if (balanceElement) {
                // Animação de pulse para indicar atualização
                anime({
                    targets: balanceElement,
                    scale: [1, 1.05, 1],
                    duration: 400
                });
            }
        } catch (error) {
            console.error('Erro ao atualizar saldo:', error);
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new TapDashboard();
});
