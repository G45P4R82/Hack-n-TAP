"""
Tela de Login Administrativo
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input, Button
from textual.containers import Vertical, Horizontal, Container
import logging
from model.database import SQLiteDatabase

logger = logging.getLogger(__name__)


class LoginScreen(Screen):
    """Tela de Login - Acesso Administrativo"""
    
    def __init__(self, login_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.login_callback = login_callback
        self.db = SQLiteDatabase()
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Container(
                Static("🔐 LOGIN ADMINISTRATIVO", classes="title"),
                Input(placeholder="Usuário", id="username_input"),
                Input(placeholder="Senha", password=True, id="password_input"),
                Static("", id="error_label", classes="error"),
                Horizontal(
                    Button("Entrar", variant="primary", id="login_btn"),
                    Button("Cancelar", variant="default", id="cancel_btn"),
                    classes="button_row"
                ),
                id="login_box"
            ),
            id="login_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Focar no campo de usuário ao montar"""
        self.query_one("#username_input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login_btn":
            self.attempt_login()
        elif event.button.id == "cancel_btn":
            self.app.switch_mode("validation")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handler para Enter nos inputs"""
        if event.input.id == "username_input":
            self.query_one("#password_input", Input).focus()
        else:
            self.attempt_login()
    
    def attempt_login(self) -> None:
        """Tenta realizar o login"""
        username = self.query_one("#username_input", Input).value
        password = self.query_one("#password_input", Input).value
        error_label = self.query_one("#error_label", Static)
        if self.db.check_credentials(username, password):
            logger.info(f"Login realizado com sucesso: {username}")
            error_label.update("✅ Sucesso!")
            error_label.styles.color = "green"
            self.login_callback()
        else:
            logger.error(f"Login falhou: {username}")
            error_label.update("❌ Acesso Negado!")
            error_label.styles.color = "red"
            self.query_one("#password_input", Input).value = ""
