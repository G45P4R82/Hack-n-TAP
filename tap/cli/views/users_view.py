"""
Tela de Gerenciamento de Usuários
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, Button, DataTable
from textual.containers import Container
import logging

logger = logging.getLogger(__name__)


class UserManagementScreen(Screen):
    """Tela de Gerenciamento de Usuários - F2"""
    
    BINDINGS = [
        ("f1", "switch_screen('validation')", "Validação"),
        ("f2", "switch_screen('help')", "Ajuda"),
        ("f3", "switch_screen('users')", "Usuários"),
        ("f4", "switch_screen('history')", "Histórico"),
        ("f5", "switch_screen('profile')", "Admin"),
        ("r", "refresh", "Atualizar"),
        ("a", "add_user", "Adicionar"),
    ]
    
    def __init__(self, db, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("👥 GERENCIAMENTO DE USUÁRIOS", classes="title"),
            Static("Total de usuários: 0", id="count_label"),
            DataTable(id="users_table"),
            Button("➕ Adicionar Usuário (A)", variant="primary", id="add_user_btn"),
            id="users_container"
        )
        yield Footer()
    
    def on_mount(self) -> None:
        """Configura a tabela ao montar a tela"""
        table = self.query_one(DataTable)
        table.add_column("Tag ID", width=15)
        table.add_column("Nome", width=30)
        table.add_column("Data de Registro", width=20)
        table.cursor_type = "row"
        self.refresh_data()
    
    def refresh_data(self) -> None:
        """Atualiza os dados da tabela"""
        table = self.query_one(DataTable)
        table.clear()
        
        data = self.db.get_all_tags()
        for tag_id, info in data.items():
            table.add_row(
                tag_id,
                info['name'],
                info['registered_at'],
            )
        
        # Atualizar contador
        count_label = self.query_one("#count_label", Static)
        count_label.update(f"Total de usuários: {len(data)}")
    
    def action_add_user(self) -> None:
        """Abre modal para adicionar usuário"""
        from cli.modals import AddUserModal
        self.app.push_screen(AddUserModal(self.db, self.refresh_data))
    
    def action_refresh(self) -> None:
        """Atualiza os dados da tabela (F5)"""
        self.refresh_data()
    
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Quando uma linha é selecionada"""
        row_key = event.row_key
        row_data = event.data_table.get_row(row_key)
        
        tag_id = row_data[0]
        name = row_data[1]
        
        # Mostrar opções de editar/excluir
        from cli.modals import UserActionModal
        self.app.push_screen(UserActionModal(self.db, tag_id, name, self.refresh_data))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "add_user_btn":
            self.action_add_user()
