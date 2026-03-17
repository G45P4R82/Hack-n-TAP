"""
Tela de Histórico de Acessos
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Container
import logging

logger = logging.getLogger(__name__)


class HistoryScreen(Screen):
    """Tela de Histórico - F3"""
    
    BINDINGS = [
        ("f1", "switch_screen('validation')", "Validação"),
        ("f2", "switch_screen('help')", "Ajuda"),
        ("f3", "switch_screen('users')", "Usuários"),
        ("f4", "switch_screen('history')", "Histórico"),
        ("f5", "switch_screen('profile')", "Admin"),
        ("r", "refresh", "Atualizar"),
    ]
    
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("📜 HISTÓRICO DE ACESSOS", classes="title"),
            Static("Últimos acessos registrados", classes="subtitle"),
            DataTable(id="history_table"),
            id="history_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Configura a tabela ao montar a tela"""
        table = self.query_one(DataTable)
        table.add_column("Nome", width=30)
        table.add_column("Data", width=15)
        table.add_column("Hora", width=15)
        self.refresh_data()
    
    def refresh_data(self) -> None:
        """Atualiza os dados da tabela"""
        table = self.query_one(DataTable)
        table.clear()
        
        entries = self.db.get_history_entries()
        for entry in entries:
            table.add_row(
                entry['name'],
                entry['display_date'],
                entry['display_time']
            )
    
    def action_refresh(self) -> None:
        """Atualiza os dados da tabela (F5)"""
        self.refresh_data()
