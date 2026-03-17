"""
Tela de Validação de Tags RFID
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Input
from textual.containers import Vertical, Container
from textual.binding import Binding
import logging

logger = logging.getLogger(__name__)


class ValidationScreen(Screen):
    """Tela de Validação - F1"""
    
    BINDINGS = [
        # Exibir somente F1 e F2 no footer para não poluir
        ("f1", "switch_screen('validation')", "Validação"),
        ("f2", "switch_screen('help')", "Ajuda"),
        Binding("f3", "switch_screen('users')", "Usuários", show=False),
        Binding("f4", "switch_screen('history')", "Histórico", show=False),
        Binding("f5", "switch_screen('profile')", "Admin", show=False),
    ]
    
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.countdown_value = 0
        self.countdown_timer = None
        
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Container(
                Static("🏷️  VALIDAÇÃO DE TAGS RFID", classes="title"),
                Static("AGUARDANDO LEITURA...", id="status_label", classes="status"),
                Static("Posicione o copo e passe a tag no leitor", id="name_label", classes="subtitle"),
                Input(placeholder="Digite ou escaneie a tag RFID...", id="tag_input"),
                id="validation_box"
            ),
            id="validation_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Focar no input ao montar a tela"""
        self.query_one("#tag_input", Input).focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handler quando o usuário submete uma tag"""
        tag_id = event.value.strip()
        event.input.value = ""
        
        if not tag_id:
            return
        
        tag_data = self.db.validate_tag(tag_id)
        if tag_data:
            self.db.add_history_entry(tag_id, tag_data['name'])
            self.show_result(True, tag_data['name'])
        else:
            self.show_result(False)
        
        # Refocus no input
        self.query_one("#tag_input", Input).focus()
    
    def show_result(self, is_valid: bool, name: str = None) -> None:
        """Exibe o resultado da validação"""
        status_label = self.query_one("#status_label", Static)
        name_label = self.query_one("#name_label", Static)
        validation_box = self.query_one("#validation_box", Container)
        
        if is_valid:
            status_label.update(f"✅ LIBERANDO TAP...")
            status_label.styles.color = "green"
            name_label.update(f"Olá, {name}! Aproveite seu Mate.")
            validation_box.styles.background = "#1e1e2e"
            validation_box.styles.border = ("thick", "green")
            #logger.info(f"Usuário {name} liberado")
            
            # Enviar comando para abrir TAP
            if hasattr(self.app, 'send_serial_command'):
                self.app.send_serial_command('1')
            
            # Iniciar countdown
            self.countdown_value = 10
            self.countdown_timer = self.set_interval(1, self.update_countdown)
        else:
            status_label.update("❌ ACESSO NEGADO")
            status_label.styles.color = "red"
            name_label.update("Tag não cadastrada.")
            validation_box.styles.background = "#331111"
            validation_box.styles.border = ("thick", "red")
            #@logger.error("Tag não cadastrada")
            
            # Reset após 3 segundos
            self.set_timer(3, self.reset_display)
    
    def update_countdown(self) -> None:
        """Atualiza o countdown"""
        if self.countdown_value > 0:
            status_label = self.query_one("#status_label", Static)
            status_label.update(f"✅ TAP LIBERADO: {self.countdown_value}s")
            self.countdown_value -= 1
        else:
            if self.countdown_timer:
                self.countdown_timer.stop()
            self.reset_display()
    
    def reset_display(self) -> None:
        """Reseta o display para estado inicial"""
        status_label = self.query_one("#status_label", Static)
        
        # Enviar comando para fechar TAP
        if hasattr(self.app, 'send_serial_command'):
            self.app.send_serial_command('0')
        name_label = self.query_one("#name_label", Static)
        validation_box = self.query_one("#validation_box", Container)
        
        status_label.update("AGUARDANDO LEITURA...")
        status_label.styles.color = "white"
        name_label.update("Posicione o copo e passe a tag no leitor")
        validation_box.styles.background = "#1e1e2e"
        validation_box.styles.border = ("thick", "#6c71c4")
