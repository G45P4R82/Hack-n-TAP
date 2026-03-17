"""
Textual Controller - Main Application Controller
Gerencia a aplicação Textual, autenticação e navegação
"""
from textual.app import App
from textual.binding import Binding
from model.database import SQLiteDatabase
from cli.textual_screens import (
    ValidationScreen,
    LoginScreen,
    UserManagementScreen,
    HistoryScreen,
    ProfileScreen,
    HelpScreen
)
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rfid_terminal.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class RFIDTextualApp(App):
    """Aplicação Principal Textual - RFID System"""
    
    CSS = """
    /* Global Styles */
    Screen {
        background: $surface;
    }
    
    .title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        padding: 1;
        background: $boost;
    }
    
    .subtitle {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        padding: 1;
    }
    
    .status {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        padding: 1;
        background: $panel;
        height: 5;
        text-align: center;
    }
    
    .info {
        width: 100%;
        padding: 1;
        color: $text;
    }
    
    .error {
        width: 100%;
        content-align: center middle;
        color: $error;
        padding: 1;
    }
    
    /* Containers */
    #validation_container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #validation_box {
        width: 60;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }
    
    #validation_box Input {
        width: 90%;
    }
    
    #users_container, #history_container {
        width: 100%;
        height: 100%;
        align: center middle;
        padding: 2;
    }
    
    #admin_container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #admin_box {
        width: 70;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }
    
    #admin_box Input {
        width: 90%;
        margin: 1 0;
    }
    
    #admin_box Button {
        width: 90%;
        margin: 1 0;
    }
    
    #help_container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #help_box {
        width: 80%;
        height: 80%;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }
    
    #help_table_inner {
        width: 100%;
        height: 1fr;
        margin: 1 0;
    }
    
    .section_title {
        width: 100%;
        content-align: left middle;
        text-style: bold;
        color: $accent;
        padding: 1 0;
        margin-top: 1;
    }
    
    #login_container {
        width: 100%;
        height: 100%;
        align: center middle;
    }
    
    #login_box {
        width: 50;
        height: auto;
        background: $panel;
        border: thick $primary;
        padding: 2;
    }
    
    #tag_input, #username_input, #password_input {
        width: 60%;
        margin: 1 0;
    }
    
    /* Tables */
    DataTable {
        height: 1fr;
        margin: 1 0;
    }
    
    #count_label {
        width: 100%;
        content-align: right middle;
        padding: 1;
        color: $text-muted;
    }
    
    /* Buttons */
    Button {
        margin: 1;
    }
    
    #add_user_btn {
        width: auto;
        margin: 1 0;
    }
    
    .button_row {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1;
    }
    
    .button_column {
        width: 100%;
        height: auto;
        align: center middle;
    }
    
    .button_column Button {
        width: 80%;
        margin: 1;
    }
    
    /* Modals */
    AddUserModal, EditUserModal, DeleteUserModal, UserActionModal {
        align: center middle;
    }
    
    .modal {
        align: center middle;
        background: $surface;
        border: thick $primary;
        width: 60;
        height: auto;
        padding: 2;
    }
    
    .modal_title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $accent;
        padding: 1;
    }
    
    .modal_subtitle {
        width: 100%;
        content-align: center middle;
        color: $text-muted;
        padding: 1;
    }
    
    .modal_text {
        width: 100%;
        content-align: center middle;
        padding: 1;
    }
    
    .modal_text_highlight {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: $warning;
        padding: 1;
    }
    
    #modal_error {
        width: 100%;
        content-align: center middle;
        padding: 1;
        height: auto;
        min-height: 3;
    }
    
    #modal_container Input {
        width: 90%;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("f1", "switch_screen('validation')", "F1: Validação", priority=True),
        Binding("f2", "switch_screen('help')", "F2: Ajuda", priority=True),
        Binding("f3", "switch_screen('users')", "F3: users", priority=True, show=False),
        Binding("f4", "switch_screen('history')", "F4: history", priority=True, show=False),
        Binding("f5", "switch_screen('profile')", "F5: profile", priority=True, show=False),
        Binding("q", "quit", "Sair"),
    ]
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = SQLiteDatabase()
        self.is_authenticated = False
        self.target_screen = None  # Para onde ir após login
        self.serial_conn = None
        
        # Detectar porta padrão baseada no SO
        import platform
        import glob
        
        system_os = platform.system()
        if system_os == "Windows":
            self.serial_port = "COM15" # Padrão Windows conforme referência
            logger.info(f"Sistema Windows detectado, usando porta padrão: {self.serial_port}")
        else:
            # Linux/Unix - Tentar encontrar /dev/ttyACM*
            acm_ports = glob.glob('/dev/ttyACM*')
            if acm_ports:
                # Ordenar para pegar o menor número (ex: ttyACM0 antes de ttyACM1)
                acm_ports.sort()
                self.serial_port = acm_ports[0]
                logger.info(f"Porta serial Linux detectada: {self.serial_port}")
            else:
                self.serial_port = "/dev/ttyACM0" # Fallback Linux
                logger.info(f"Nenhuma porta ACM encontrada, usando fallback Linux: {self.serial_port}")

        logger.info("Aplicação Textual iniciada")
        
    def connect_serial(self, port=None):
        if port: self.serial_port = port
        try:
            import serial
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            
            self.serial_conn = serial.Serial(self.serial_port, 9600, timeout=1)
            logger.info(f"Conectado à porta serial {self.serial_port}")
            return True, "Conectado"
        except Exception as e:
            logger.error(f"Erro ao conectar serial {self.serial_port}: {e}")
            return False, str(e)

    def send_serial_command(self, command):
        if self.serial_conn and self.serial_conn.is_open:
            try:
                self.serial_conn.write(command.encode())
                logger.info(f"Serial enviado: {command}")
            except Exception as e:
                logger.error(f"Erro ao enviar serial: {e}")
    
    def on_unmount(self) -> None:
        if self.serial_conn and self.serial_conn.is_open:
            #self.serial_conn.close()
            logger.info("Serial desconectado")
    
    def on_mount(self) -> None:
        """Inicializa a aplicação"""
        self.title = "RFID Reader System - LHC Mate Tap"
        self.sub_title = "Terminal Interface"
        
        # Tentar conectar na serial
        self.connect_serial()
        
        # Instalar todas as screens
        self.install_screen(ValidationScreen(self.db), name="validation")
        self.install_screen(HelpScreen(), name="help")
        self.install_screen(LoginScreen(self.on_login_success), name="login")
        self.install_screen(UserManagementScreen(self.db), name="users")
        self.install_screen(HistoryScreen(self.db), name="history")
        self.install_screen(ProfileScreen(self.logout_admin), name="profile")
        
        # Começar na tela de validação
        self.push_screen("validation")
        logger.info("Telas instaladas, iniciando na validação")
    
    def action_switch_screen(self, screen_name: str) -> None:
        """Ação global para trocar de tela via teclas de função"""
        logger.info(f"Tentando navegar para: {screen_name}")
        
        # Verificar se precisa de autenticação
        protected_screens = ['users', 'history', 'profile']
        
        if screen_name in protected_screens and not self.is_authenticated:
            logger.warning(f"Acesso negado a {screen_name} - não autenticado")
            self.target_screen = screen_name
            self.switch_screen("login")
            return
        
        # Navegar normalmente
        self.switch_screen(screen_name)
    
    def switch_screen(self, screen_name: str) -> None:
        """Troca de tela (helper method)"""
        try:
            self.pop_screen()
        except:
            pass
        self.push_screen(screen_name)
        logger.info(f"Navegado para: {screen_name}")
    
    def on_login_success(self) -> None:
        """Callback quando login é bem-sucedido"""
        self.is_authenticated = True
        logger.info("Login bem-sucedido")
        
        # Ir para a tela que o usuário queria acessar
        target = self.target_screen if self.target_screen else 'users'
        self.action_switch_screen(target)
        self.target_screen = None
    
    def logout_admin(self) -> None:
        """Callback para logout"""
        self.is_authenticated = False
        logger.info("Logout realizado")
        self.switch_screen("validation")


def main():
    """Função principal para executar a aplicação"""
    app = RFIDTextualApp()
    app.run()


if __name__ == "__main__":
    main()
