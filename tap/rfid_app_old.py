
import os
import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.utils import get_color_from_hex

# --- Configuration ---
DB_FILE = "rfid_system.db"

# --- Database Manager (SQLite) ---
class SQLiteDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.initialize_admin()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                registered_at TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id TEXT,
                name TEXT,
                timestamp TEXT,
                display_date TEXT,
                display_time TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        ''')
        self.conn.commit()

    def initialize_admin(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", ("capivara",))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("capivara", "tijolo22"))
            self.conn.commit()

    def check_credentials(self, username, password):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
        return cursor.fetchone() is not None

    def get_all_tags(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tags ORDER BY registered_at DESC")
        rows = cursor.fetchall()
        return {row['id']: {'name': row['name'], 'registered_at': row['registered_at']} for row in rows}

    def validate_tag(self, tag_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tags WHERE id = ?", (tag_id,))
        row = cursor.fetchone()
        if row:
            return {'name': row['name'], 'registered_at': row['registered_at']}
        return None

    def add_tag(self, tag_id, name, registered_at=None, skip_check=False):
        if not skip_check and self.validate_tag(tag_id):
            return False, "Tag já cadastrada!"
        if not registered_at:
            registered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO tags (id, name, registered_at) VALUES (?, ?, ?)", (tag_id, name, registered_at))
            self.conn.commit()
            return True, "Tag cadastrada com sucesso!"
        except sqlite3.Error as e:
            return False, f"Erro ao cadastrar: {e}"

    def update_tag(self, tag_id, new_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute("UPDATE tags SET name = ? WHERE id = ?", (new_name, tag_id))
            self.conn.commit()
            if cursor.rowcount > 0:
                return True, "Nome atualizado!"
            return False, "Tag não encontrada!"
        except sqlite3.Error as e:
            return False, str(e)

    def remove_tag(self, tag_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
            self.conn.commit()
            return True, "Tag removida!"
        except sqlite3.Error as e:
            return False, str(e)

    def add_history_entry(self, tag_id, name, timestamp=None, display_date=None, display_time=None):
        now = datetime.now()
        if not timestamp: timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        if not display_date: display_date = now.strftime("%d/%m/%Y")
        if not display_time: display_time = now.strftime("%H:%M:%S")
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO history (tag_id, name, timestamp, display_date, display_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (tag_id, name, timestamp, display_date, display_time))
        self.conn.commit()

    def get_history_entries(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM history ORDER BY id DESC")
        return [dict(row) for row in cursor.fetchall()]

# --- KV Language (Bulma Dark Theme) ---
KV = '''
#:set color_bg (0.1, 0.1, 0.1, 1)
#:set color_card (0.14, 0.14, 0.14, 1)
#:set color_primary (0, 0.82, 0.7, 1)  # Turquoise
#:set color_link (0.2, 0.45, 0.86, 1)     # Blue
#:set color_text (0.71, 0.71, 0.71, 1)    # Grey Light
#:set color_title (1, 1, 1, 1)            # White
#:set color_danger (0.75, 0.22, 0.17, 1)
#:set color_success (0.15, 0.68, 0.38, 1)

<Label>:
    color: color_text

<Button>:
    background_normal: ''
    background_color: color_link
    color: color_title
    bold: True

<TextInput>:
    background_normal: ''
    background_active: ''
    background_color: (0.2, 0.2, 0.2, 1)
    foreground_color: color_title
    cursor_color: color_primary
    padding: [10, 10]

<ValidationTab>:
    orientation: 'vertical'
    padding: 40
    spacing: 20
    canvas.before:
        Color:
            rgba: color_bg
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "MODO DE VALIDAÇÃO"
        font_size: 20
        size_hint_y: None
        height: 40
        color: color_primary

    TextInput:
        id: scan_input
        multiline: False
        hint_text: "Clique aqui e passe o cartão..."
        size_hint_y: None
        height: 50
        halign: 'center'
        font_size: 18
        on_text_validate: root.validate_tag(self)

    BoxLayout:
        orientation: 'vertical'
        size_hint_y: 1
        Label:
            id: result_label
            text: "AGUARDANDO LEITURA..."
            font_size: 32
            bold: True
            color: color_title
        Label:
            id: name_label
            text: "Posicione o copo e passe a tag no leitor"
            font_size: 24

<TagRow>:
    size_hint_y: None
    height: 50
    padding: [10, 5]
    spacing: 10
    canvas.before:
        Color:
            rgba: color_card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [5,]
            
    Label:
        text: root.tag_id
        size_hint_x: 0.25
        color: color_title
    Label:
        text: root.name
        size_hint_x: 0.35
        color: color_text
    Label:
        text: root.date
        size_hint_x: 0.2
        font_size: 12
        
    BoxLayout:
        size_hint_x: 0.2
        spacing: 5
        Button:
            text: "Editar"
            background_color: (0.95, 0.61, 0.07, 1) # Warning
            font_size: 12
            on_release: root.edit_callback(root.tag_id, root.name)
        Button:
            text: "X"
            background_color: color_danger
            font_size: 12
            on_release: root.delete_callback(root.tag_id, root.name)

<UserManagementTab>:
    orientation: 'vertical'
    padding: 20
    spacing: 10
    canvas.before:
        Color:
            rgba: color_bg
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "GESTÃO DE USUÁRIOS"
        font_size: 20
        size_hint_y: None
        height: 40
        color: color_primary

    BoxLayout:
        size_hint_y: None
        height: 30
        Label:
            text: "ID / Tag"
            bold: True
            size_hint_x: 0.25
            color: color_primary
        Label:
            text: "Nome"
            bold: True
            size_hint_x: 0.35
            color: color_primary
        Label:
            text: "Data"
            bold: True
            size_hint_x: 0.2
            color: color_primary
        Label:
            text: "Ações"
            bold: True
            size_hint_x: 0.2
            color: color_primary

    Label:
        id: count_label
        text: "Total: 0"
        size_hint_y: None
        height: 20
        font_size: 12

    ScrollView:
        BoxLayout:
            id: list_layout
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: 5

    BoxLayout:
        size_hint_y: None
        height: 50
        spacing: 10
        Button:
            text: "Adicionar Usuário"
            background_color: color_success
            on_press: root.open_add_user_popup(self)
        Button:
            text: "Atualizar Lista"
            background_color: color_link
            on_press: root.refresh_data()

<HistoryRow>:
    size_hint_y: None
    height: 40
    canvas.before:
        Color:
            rgba: color_card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [5,]
    Label:
        text: root.name
        size_hint_x: 0.4
        color: color_title
    Label:
        text: root.display_date
        size_hint_x: 0.3
    Label:
        text: root.display_time
        size_hint_x: 0.3

<HistoryTab>:
    orientation: 'vertical'
    padding: 20
    spacing: 10
    canvas.before:
        Color:
            rgba: color_bg
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "HISTÓRICO DE USO"
        font_size: 20
        size_hint_y: None
        height: 40
        color: color_primary

    BoxLayout:
        size_hint_y: None
        height: 30
        Label:
            text: "Nome"
            bold: True
            size_hint_x: 0.4
            color: color_primary
        Label:
            text: "Data"
            bold: True
            size_hint_x: 0.3
            color: color_primary
        Label:
            text: "Hora"
            bold: True
            size_hint_x: 0.3
            color: color_primary

    ScrollView:
        BoxLayout:
            id: list_layout
            orientation: 'vertical'
            size_hint_y: None
            height: self.minimum_height
            spacing: 5

    Button:
        text: "Atualizar Histórico"
        size_hint_y: None
        height: 50
        background_color: (0.55, 0.27, 0.67, 1) # Purple
        on_press: root.refresh_data()

<AdminLoginView>:
    anchor_x: 'center'
    anchor_y: 'center'
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20
        size_hint: None, None
        size: 350, 400
        canvas.before:
            Color:
                rgba: color_card
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [15,]
        
        Label:
            text: "🔐 ACESSO RESTRITO"
            font_size: 24
            bold: True
            color: color_danger
            size_hint_y: None
            height: 40
        Label:
            text: "Autenticação necessária"
            font_size: 16
            size_hint_y: None
            height: 20
        
        Label:
            size_hint_y: None
            height: 10

        TextInput:
            id: user_input
            multiline: False
            hint_text: "Usuário"
            size_hint_y: None
            height: 45
            
        TextInput:
            id: pass_input
            multiline: False
            hint_text: "Senha"
            password: True
            size_hint_y: None
            height: 45
            on_text_validate: root.check_login(self)
            
        Button:
            text: "ENTRAR"
            size_hint_y: None
            height: 50
            background_color: color_link
            on_press: root.check_login(self)
        
        Label:
            id: error_label
            text: ""
            color: color_danger
            size_hint_y: None
            height: 30
            font_size: 14

<ProfileTab>:
    orientation: 'vertical'
    padding: 50
    spacing: 20
    canvas.before:
        Color:
            rgba: color_bg
        Rectangle:
            pos: self.pos
            size: self.size

    Label:
        text: "👤 PERFIL ADMIN"
        font_size: 24
        bold: True
        size_hint_y: None
        height: 50
        color: color_primary
    
    Label:
        text: "Você está logado como Administrador"
        font_size: 18

    AnchorLayout:
        anchor_x: 'center'
        anchor_y: 'center'
        Button:
            text: "SAIR (LOGOUT)"
            size_hint: None, None
            size: 200, 50
            background_color: color_danger
            on_press: root.logout_callback()
'''

Builder.load_string(KV)

# --- Python Classes ---

class ValidationTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        # Bind focus logic
        self.ids.scan_input.bind(focus=self.on_focus)

    def on_focus(self, instance, value):
        pass

    def validate_tag(self, instance):
        tag_id = self.ids.scan_input.text.strip()
        self.ids.scan_input.text = ""
        
        if not tag_id:
            return

        tag_data = self.db.validate_tag(tag_id)
        if tag_data:
            self.db.add_history_entry(tag_id, tag_data['name'])
            self.show_result(True, tag_data['name'])
        else:
            self.show_result(False)
        
        Clock.schedule_once(lambda dt: setattr(self.ids.scan_input, 'focus', True), 0.1)

    def show_result(self, is_valid, name=None):
        if is_valid:
            self.ids.result_label.text = "LIBERANDO TAP..."
            self.ids.result_label.color = get_color_from_hex('#2ecc71')
            self.ids.name_label.text = f"Olá, {name}! Aproveite seu Mate."
            self.countdown_val = 10
            Clock.schedule_interval(self.update_countdown, 1)
            App.get_running_app().update_history_tab()
        else:
            self.ids.result_label.text = "ACESSO NEGADO"
            self.ids.result_label.color = get_color_from_hex('#e74c3c')
            self.ids.name_label.text = "Tag não cadastrada."
            Clock.schedule_once(self.reset_display, 3)

    def update_countdown(self, dt):
        if self.countdown_val > 0:
            self.ids.result_label.text = f"TAP LIBERADO: {self.countdown_val}s"
            self.countdown_val -= 1
        else:
            Clock.unschedule(self.update_countdown)
            self.reset_display(dt)

    def reset_display(self, dt):
        self.ids.result_label.text = "AGUARDANDO LEITURA..."
        self.ids.result_label.color = (1, 1, 1, 1)
        self.ids.name_label.text = "Posicione o copo e passe a tag no leitor"

class TagRow(BoxLayout):
    tag_id = StringProperty("")
    name = StringProperty("")
    date = StringProperty("")
    
    def __init__(self, tag_id, name, date, edit_callback, delete_callback, **kwargs):
        super().__init__(**kwargs)
        self.tag_id = tag_id
        self.name = name
        self.date = date
        self.edit_callback = edit_callback
        self.delete_callback = delete_callback

class UserManagementTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db

    def refresh_data(self, *args):
        self.ids.list_layout.clear_widgets()
        data = self.db.get_all_tags()
        for k, v in data.items():
            row = TagRow(k, v['name'], v['registered_at'], self.open_edit_popup, self.open_delete_popup)
            self.ids.list_layout.add_widget(row)
        self.ids.count_label.text = f"Total: {len(data)}"

    def open_add_user_popup(self, instance):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text="1. Passe o cartão (ID):"))
        input_tag = TextInput(multiline=False, hint_text="ID da Tag", size_hint_y=None, height=40)
        content.add_widget(input_tag)
        content.add_widget(Label(text="2. Nome:"))
        input_name = TextInput(multiline=False, hint_text="Nome", size_hint_y=None, height=40)
        content.add_widget(input_name)
        
        def focus_name(*args): input_name.focus = True
        input_tag.bind(on_text_validate=focus_name)
        
        buttons = BoxLayout(size_hint_y=None, height=40, spacing=10)
        save_btn = Button(text="CADASTRAR", background_color=get_color_from_hex('#27ae60'))
        cancel_btn = Button(text="Cancelar", background_color=get_color_from_hex('#95a5a6'))
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        
        popup = Popup(title='Adicionar Novo Usuário', content=content, size_hint=(None, None), size=(400, 300))
        
        def save(*args):
            tag_id = input_tag.text.strip()
            name = input_name.text.strip()
            if not tag_id or not name: return
            success, msg = self.db.add_tag(tag_id, name)
            if success:
                self.refresh_data()
                popup.dismiss()
        
        input_name.bind(on_text_validate=save)
        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()
        Clock.schedule_once(lambda dt: setattr(input_tag, 'focus', True), 0.1)

    def open_edit_popup(self, tag_id, current_name):
        pass # Reuse previous logic if needed, or re-implement simple popup here or in KV? 
        # Since Popups are transient, good to keep in python or defined as class in KV
        # Let's keep it simple python for now to avoid huge KV
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        input_name = TextInput(text=current_name, multiline=False, size_hint_y=None, height=40)
        content.add_widget(Label(text=f"Novo nome para ID {tag_id}:"))
        content.add_widget(input_name)
        buttons = BoxLayout(size_hint_y=None, height=40, spacing=10)
        save_btn = Button(text="Salvar", background_color=get_color_from_hex('#2ecc71'))
        cancel_btn = Button(text="Cancelar", background_color=get_color_from_hex('#95a5a6'))
        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)
        content.add_widget(buttons)
        popup = Popup(title='Editar Usuário', content=content, size_hint=(None, None), size=(400, 200))
        def save(instance):
            new_name = input_name.text.strip()
            if new_name:
                self.db.update_tag(tag_id, new_name)
                self.refresh_data()
                popup.dismiss()
        save_btn.bind(on_press=save)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def open_delete_popup(self, tag_id, name):
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=f"Tem certeza que deseja excluir\n{name}?"))
        buttons = BoxLayout(size_hint_y=None, height=40, spacing=10)
        yes_btn = Button(text="Sim, Excluir", background_color=get_color_from_hex('#c0392b'))
        no_btn = Button(text="Cancelar", background_color=get_color_from_hex('#95a5a6'))
        buttons.add_widget(yes_btn)
        buttons.add_widget(no_btn)
        content.add_widget(buttons)
        popup = Popup(title='Confirmar Exclusão', content=content, size_hint=(None, None), size=(300, 200))
        def delete(instance):
            self.db.remove_tag(tag_id)
            self.refresh_data()
            popup.dismiss()
        yes_btn.bind(on_press=delete)
        no_btn.bind(on_press=popup.dismiss)
        popup.open()

class HistoryRow(BoxLayout):
    name = StringProperty("")
    display_date = StringProperty("")
    display_time = StringProperty("")
    def __init__(self, name, d_date, d_time, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.display_date = d_date
        self.display_time = d_time

class HistoryTab(BoxLayout):
    def __init__(self, history_manager, **kwargs):
        super().__init__(**kwargs)
        self.history_manager = history_manager

    def refresh_data(self, *args):
        self.ids.list_layout.clear_widgets()
        data = self.history_manager.get_history_entries()
        for entry in data:
            row = HistoryRow(entry['name'], entry['display_date'], entry['display_time'])
            self.ids.list_layout.add_widget(row)

class AdminLoginView(AnchorLayout):
    def __init__(self, db, success_callback, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.success_callback = success_callback

    def check_login(self, instance):
        username = self.ids.user_input.text.strip()
        password = self.ids.pass_input.text.strip()
        
        if self.db.check_credentials(username, password):
            self.ids.error_label.text = "Sucesso!"
            self.ids.error_label.color = get_color_from_hex('#2ecc71')
            Clock.schedule_once(lambda dt: self.success_callback(), 0.5)
        else:
            self.ids.error_label.text = "Acesso Negado!"
            self.ids.pass_input.text = ""
            self.ids.pass_input.focus = True

class ProfileTab(BoxLayout):
    def __init__(self, logout_callback, **kwargs):
        super().__init__(**kwargs)
        self.logout_callback = logout_callback

# --- Main App ---
class RFIDApp(App):
    def build(self):
        self.title = 'RFID Reader System - LHC Mate Tap'
        self.db = SQLiteDatabase()
        self.is_authenticated = False
        Window.clearcolor = (0.1, 0.1, 0.1, 1)

        self.tabs = TabbedPanel()
        self.tabs.do_default_tab = False
        self.tabs.tab_width = 180

        self.tab_validate = TabbedPanelItem(text='Validação')
        self.validation_view = ValidationTab(self.db)
        self.tab_validate.add_widget(self.validation_view)
        
        self.tab_list = TabbedPanelItem(text='Gestão de Usuários')
        self.tab_list.add_widget(AdminLoginView(self.db, self.unlock_admin))
        
        self.tab_history = TabbedPanelItem(text='Histórico')
        self.tab_history.add_widget(AdminLoginView(self.db, self.unlock_admin))
        
        self.tab_profile = TabbedPanelItem(text='Perfil')
        self.tab_profile.add_widget(AdminLoginView(self.db, self.unlock_admin))
        
        self.tabs.add_widget(self.tab_validate)
        self.tabs.add_widget(self.tab_list)
        self.tabs.add_widget(self.tab_history)
        self.tabs.add_widget(self.tab_profile)

        self.list_view = None
        self.history_view = None
        self.tabs.default_tab = self.tab_validate
        Clock.schedule_once(self.set_default_tab, 0)
        return self.tabs

    def set_default_tab(self, dt):
        self.tabs.switch_to(self.tab_validate)

    def unlock_admin(self):
        if self.is_authenticated: return
        self.is_authenticated = True
        
        self.tab_list.clear_widgets()
        self.list_view = UserManagementTab(self.db)
        self.list_view.refresh_data()
        self.tab_list.add_widget(self.list_view)
        
        self.tab_history.clear_widgets()
        self.history_view = HistoryTab(self.db)
        self.history_view.refresh_data()
        self.tab_history.add_widget(self.history_view)
        
        self.tab_profile.clear_widgets()
        self.tab_profile.add_widget(ProfileTab(self.logout_admin))

    def logout_admin(self):
        self.is_authenticated = False
        self.tab_list.clear_widgets()
        self.tab_list.add_widget(AdminLoginView(self.db, self.unlock_admin))
        self.list_view = None
        self.tab_history.clear_widgets()
        self.tab_history.add_widget(AdminLoginView(self.db, self.unlock_admin))
        self.history_view = None
        self.tab_profile.clear_widgets()
        self.tab_profile.add_widget(AdminLoginView(self.db, self.unlock_admin))
        self.set_default_tab(0)

    def update_list_tab(self):
        if self.list_view: self.list_view.refresh_data()
        
    def update_history_tab(self):
        if self.history_view: self.history_view.refresh_data()

if __name__ == '__main__':
    RFIDApp().run()
