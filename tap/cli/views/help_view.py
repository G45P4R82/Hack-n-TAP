"""
Tela de Ajuda (Comandos)
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, DataTable
from textual.containers import Container, Vertical
import logging

logger = logging.getLogger(__name__)


class HelpScreen(Screen):
    """Tela de Ajuda - F2"""
    
    BINDINGS = [
        ("f1", "switch_screen('validation')", "Validação"),
        ("f2", "switch_screen('help')", "Ajuda"),
        ("f3", "switch_screen('users')", "Usuários"),
        ("f4", "switch_screen('history')", "Histórico"),
        ("f5", "switch_screen('profile')", "Admin"),
        ("a", "add_user_help", "Add Usuário"),
        ("q", "quit", "Sair"),
    ]
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Container(
                Static("ℹ️  AJUDA E COMANDOS", classes="title"),
                Static("Lista de atalhos e comandos disponíveis", classes="subtitle"),
                Container(
                    DataTable(id="help_table"),
                    id="help_table_inner"
                ),
                id="help_box"
            ),
            id="help_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Configura a tabela ao montar a tela"""
        table = self.query_one(DataTable)
        table.add_column("Tecla", width=15)
        table.add_column("Descrição")
        
        table.add_row("F1", "Tela de Validação\n(Aguarda Tag/Copo)")
        table.add_row("F2", "Tela de Ajuda\n(Esta tela)")
        table.add_row("F3", "Gerenciar Usuários\n(Ver, Add, Histórico)")
        table.add_row("F4", "Histórico de Acessos")
        table.add_row("F5", "Painel Admin\n(Status COM, Sair)")
        table.add_row("a", "apenas no painel de usuários\nAdicionar usuário\n(Apenas na tela F3)")
        table.add_row("q", "Sair do aplicativo")
        
    def action_add_user_help(self) -> None:
        """ Ação dummy só para mostrar que o botão 'A' é para adicioanr """
        pass
