"""
Modais para gerenciamento de usuários (CRUD)
"""
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static, Input, Button
from textual.containers import Vertical, Horizontal, Container
import logging

logger = logging.getLogger(__name__)


class AddUserModal(Screen):
    """Modal para adicionar novo usuário"""
    
    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]
    
    def __init__(self, db, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("➕ ADICIONAR USUÁRIO", classes="modal_title"),
            Input(placeholder="Tag ID", id="tag_id_input"),
            Input(placeholder="Nome do Usuário", id="name_input"),
            Static("", id="modal_error", classes="error"),
            Horizontal(
                Button("Salvar", variant="primary", id="save_btn"),
                Button("Cancelar", variant="default", id="cancel_btn"),
                classes="button_row"
            ),
            id="modal_container",
            classes="modal"
        )
    
    def on_mount(self) -> None:
        self.query_one("#tag_id_input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            tag_id = self.query_one("#tag_id_input", Input).value.strip()
            name = self.query_one("#name_input", Input).value.strip()
            error_label = self.query_one("#modal_error", Static)
            
            if not tag_id or not name:
                error_label.update("⚠️  Preencha todos os campos")
                error_label.styles.color = "yellow"
                return
                
            success, msg = self.db.add_tag(tag_id, name)
            if success:
                logger.info(f"Usuário adicionado: {name} ({tag_id})")
                self.callback()
                self.app.pop_screen()
            else:
                error_label.update(f"❌ {msg}")
                error_label.styles.color = "red"
        elif event.button.id == "cancel_btn":
            self.app.pop_screen()


class UserActionModal(Screen):
    """Modal com ações para um usuário específico"""
    
    BINDINGS = [("escape", "app.pop_screen", "Fechar")]
    
    def __init__(self, db, tag_id, name, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.tag_id = tag_id
        self.user_name = name
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"👤 {self.user_name}", classes="modal_title"),
            Static(f"Tag ID: {self.tag_id}", classes="modal_subtitle"),
            Vertical(
                Button("✏️  Editar Nome", id="edit_btn", variant="primary"),
                Button("🗑️  Excluir Usuário", id="delete_btn", variant="error"),
                Button("❌ Fechar", id="close_btn", variant="default"),
                classes="button_column"
            ),
            id="modal_container",
            classes="modal"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "edit_btn":
            self.app.pop_screen()
            self.app.push_screen(EditUserModal(self.db, self.tag_id, self.user_name, self.callback))
        elif event.button.id == "delete_btn":
            self.app.pop_screen()
            self.app.push_screen(DeleteUserModal(self.db, self.tag_id, self.user_name, self.callback))
        elif event.button.id == "close_btn":
            self.app.pop_screen()


class EditUserModal(Screen):
    """Modal para editar nome do usuário"""
    
    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]
    
    def __init__(self, db, tag_id, current_name, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.tag_id = tag_id
        self.current_name = current_name
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("✏️  EDITAR USUÁRIO", classes="modal_title"),
            Static(f"Tag ID: {self.tag_id}", classes="modal_subtitle"),
            Input(placeholder="Novo nome", value=self.current_name, id="new_name_input"),
            Static("", id="modal_error", classes="error"),
            Horizontal(
                Button("Salvar", variant="primary", id="save_btn"),
                Button("Cancelar", variant="default", id="cancel_btn"),
                classes="button_row"
            ),
            id="modal_container",
            classes="modal"
        )
    
    def on_mount(self) -> None:
        name_input = self.query_one("#new_name_input", Input)
        name_input.focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            new_name = self.query_one("#new_name_input", Input).value.strip()
            error_label = self.query_one("#modal_error", Static)
            
            if not new_name:
                error_label.update("⚠️  Nome não pode estar vazio")
                error_label.styles.color = "yellow"
                return
            
            success, msg = self.db.update_tag(self.tag_id, new_name)
            if success:
                logger.info(f"Nome atualizado: {self.current_name} → {new_name}")
                self.callback()
                self.app.pop_screen()
            else:
                error_label.update(f"❌ {msg}")
                error_label.styles.color = "red"
        elif event.button.id == "cancel_btn":
            self.app.pop_screen()


class DeleteUserModal(Screen):
    """Modal para confirmar exclusão de usuário"""
    
    BINDINGS = [("escape", "app.pop_screen", "Cancelar")]
    
    def __init__(self, db, tag_id, name, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.tag_id = tag_id
        self.user_name = name
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("⚠️  CONFIRMAR EXCLUSÃO", classes="modal_title"),
            Static(f"Tem certeza que deseja excluir:", classes="modal_text"),
            Static(f"{self.user_name}?", classes="modal_text_highlight"),
            Static(f"Tag ID: {self.tag_id}", classes="modal_subtitle"),
            Horizontal(
                Button("Sim, Excluir", variant="error", id="confirm_btn"),
                Button("Cancelar", variant="default", id="cancel_btn"),
                classes="button_row"
            ),
            id="modal_container",
            classes="modal"
        )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm_btn":
            success, msg = self.db.remove_tag(self.tag_id)
            if success:
                logger.info(f"Usuário excluído: {self.user_name} ({self.tag_id})")
                self.callback()
                self.app.pop_screen()
        elif event.button.id == "cancel_btn":
            self.app.pop_screen()
