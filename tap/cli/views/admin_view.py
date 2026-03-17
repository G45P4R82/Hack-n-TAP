"""
Tela Administrativa (Painel de Controle)
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.containers import Vertical, Container
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ProfileScreen(Screen):
    """Tela Administrativa - F4"""
    
    BINDINGS = [
        ("f1", "switch_screen('validation')", "Validação"),
        ("f2", "switch_screen('help')", "Ajuda"),
        ("f3", "switch_screen('users')", "Usuários"),
        ("f4", "switch_screen('history')", "Histórico"),
        ("f5", "switch_screen('profile')", "Admin"),
    ]
    
    def __init__(self, logout_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logout_callback = logout_callback
        self.com_port = "COM3"  # Porta padrão
        self.port_status = "Não configurado"
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Container(
                Static("⚙️  PAINEL ADMINISTRATIVO", classes="title"),
                Static("", id="admin_divider", classes="subtitle"),
                
                # Informações da sessão
                Static("📊 Informações da Sessão", classes="section_title"),
                Static(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", id="session_time", classes="info"),
                Static("Status: Ativo", classes="info"),
                
                Static("", classes="subtitle"),  # Espaçador
                
                # Configuração da porta COM
                Static("🔌 Configuração da Porta", classes="section_title"),
                Static("", id="port_status_label", classes="info"),
                Input(placeholder="Digite a porta COM (ex: COM3)", value="COM3", id="com_port_input"),
                Button("🔍 Verificar Porta", variant="primary", id="check_port_btn"),
                Button("💾 Salvar Configuração", variant="success", id="save_port_btn"),
                
                Static("", classes="subtitle"),  # Espaçador
                
                # Botão de logout
                Button("🚪 Sair do Sistema", variant="error", id="logout_btn"),
                
                id="admin_box"
            ),
            id="admin_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Atualiza status da porta ao montar"""
        if hasattr(self.app, 'serial_port'):
            self.com_port = self.app.serial_port
            self.query_one("#com_port_input", Input).value = self.com_port
        self.update_port_status()
    
    def update_port_status(self) -> None:
        """Atualiza o status da porta COM"""
        status_label = self.query_one("#port_status_label", Static)
        
        # Verificar conexão real no app
        if hasattr(self.app, 'serial_conn') and self.app.serial_conn and self.app.serial_conn.is_open:
            self.port_status = f"✅ Conectado em {self.app.serial_port}"
            status_label.styles.color = "green"
        else:
            self.port_status = f"❌ Desconectado ({self.com_port})"
            status_label.styles.color = "red"
            
        status_label.update(f"Status: {self.port_status}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "logout_btn":
            logger.info("Logout realizado")
            self.logout_callback()
        elif event.button.id == "check_port_btn" or event.button.id == "save_port_btn":
            # Tentar conectar na nova porta
            com_input = self.query_one("#com_port_input", Input)
            new_port = com_input.value.strip() or "COM3"
            
            if hasattr(self.app, 'connect_serial'):
                success, msg = self.app.connect_serial(new_port)
                if success:
                    self.com_port = new_port
                    self.port_status = f"✅ Conectado em {new_port}"
                    self.query_one("#port_status_label", Static).styles.color = "green"
                else:
                    self.port_status = f"❌ Erro: {msg}"
                    self.query_one("#port_status_label", Static).styles.color = "red"
                
                self.query_one("#port_status_label", Static).update(f"Status: {self.port_status}")
