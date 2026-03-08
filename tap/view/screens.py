from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.app import App
from kivy.utils import get_color_from_hex
from kivy.properties import StringProperty, ObjectProperty

import serial
import logging

logger = logging.getLogger(__name__)

from kivy.animation import Animation
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen

class ValidationTab(BoxLayout):
    def __init__(self, db, **kwargs):
        super().__init__(**kwargs)
        self.db = db
        self.ser = None
        try:
            self.ser = serial.Serial('COM15', 115200, timeout=1)
        except Exception as e:
            logger.error(f"Erro ao conectar na porta serial COM15: {e}")

        # Bind focus logic
        Clock.schedule_once(lambda dt: self.ids.scan_input.bind(focus=self.on_focus), 1)
        # Set focus on startup
        Clock.schedule_once(lambda dt: setattr(self.ids.scan_input, 'focus', True), 0.5)


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

    def send_serial(self, command):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(command.encode())
                logger.info(f"Comando serial enviado: {command}")
            except Exception as e:
                logger.error(f"Erro ao enviar comando serial: {e}")

    def show_result(self, is_valid, name=None):
        if is_valid:
            self.send_serial('1') # 1 para aberto
            self.ids.result_label.text = "LIBERANDO TAP..."
            logger.info(f"Usuário {name} liberado")
            self.ids.result_label.color = get_color_from_hex('#2ecc71')
            self.ids.name_label.text = f"Olá, {name}! Aproveite seu Mate."
            logger.info(f"Olá, {name}! Aproveite seu Mate.")
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
            logger.info(f"TAP LIBERADO: {self.countdown_val}s")
            self.countdown_val -= 1
        else:
            Clock.unschedule(self.update_countdown)
            self.reset_display(dt)

    def reset_display(self, dt):
        self.send_serial('0') # 0 para fechado
        self.ids.result_label.text = "AGUARDANDO LEITURA..."
        logger.info("AGUARDANDO LEITURA...")
        self.ids.result_label.color = (1, 1, 1, 1)
        self.ids.name_label.text = "Posicione o copo e passe a tag no leitor"
        logger.info("Posicione o copo e passe a tag no leitor")


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

class AddUserPopupContent(BoxLayout):
    def __init__(self, save_callback, cancel_callback, **kwargs):
        super().__init__(**kwargs)
        self.save_callback = save_callback
        self.cancel_callback = cancel_callback

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
        content = AddUserPopupContent(save_callback=lambda: None, cancel_callback=lambda: None)
        popup = Popup(title='Adicionar Novo Usuário', content=content, size_hint=(None, None), size=(400, 350))
        logger.info("Adicionar Novo Usuário")
        # Override callbacks to close popup
        def save():
            tag_id = content.ids.input_tag.text.strip()
            name = content.ids.input_name.text.strip()
            if not tag_id or not name: return
            success, msg = self.db.add_tag(tag_id, name)
            if success:
                self.refresh_data()
                popup.dismiss()
        
        content.save_callback = save
        content.cancel_callback = popup.dismiss
        
        popup.open()
        Clock.schedule_once(lambda dt: setattr(content.ids.input_tag, 'focus', True), 0.1)

    def open_edit_popup(self, tag_id, current_name):
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
            logger.info(f"Editar Usuário: {tag_id}")
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
            logger.info(f"Excluir Usuário: {tag_id}")
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
            logger.info(f"Login realizado com sucesso: {username}")
            self.ids.error_label.text = "Sucesso!"
            self.ids.error_label.color = get_color_from_hex('#2ecc71')
            Clock.schedule_once(lambda dt: self.success_callback(), 0.5)
        else:
            logger.error(f"Login falhou: {username}")
            self.ids.error_label.text = "Acesso Negado!"
            self.ids.pass_input.text = ""
            self.ids.pass_input.focus = True

class ProfileTab(BoxLayout):
    def __init__(self, logout_callback, **kwargs):
        super().__init__(**kwargs)
        self.logout_callback = logout_callback

class HoverButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_hover_enter')
        self.register_event_type('on_hover_leave')
        Window.bind(mouse_pos=self.on_mouse_pos)
        self.hovering = False
        self.orig_font_size = "15sp"

    def on_mouse_pos(self, window, pos):
        if not self.get_root_window():
            return
        
        # Check if widget is visible and not hidden by parent
        if self.parent and self.parent.x < 0: # Assuming parent is the side menu
             return

        if self.collide_point(*self.to_widget(*pos)):
            if not self.hovering:
                self.hovering = True
                self.dispatch('on_hover_enter')
        else:
            if self.hovering:
                self.hovering = False
                self.dispatch('on_hover_leave')

    def on_hover_enter(self):
        Animation(font_size=20, duration=0.1).start(self)
        self.background_color = (0.2, 0.6, 1, 1)

    def on_hover_leave(self):
        Animation(font_size=15, duration=0.1).start(self)
        self.background_color = (0.2, 0.45, 0.86, 1)

class NavMenu(BoxLayout):
    def __init__(self, nav_callback, **kwargs):
        super().__init__(**kwargs)
        self.nav_callback = nav_callback
        self.orientation = 'vertical'
        self.size_hint_x = None
        self.width = 200
        self.pos_hint = {'x': -0.19} # 95% hidden (200 * 0.95 = 190 hidden) logic handled in pos
        # Actually in FloatLayout we use pos or pos_hint. 
        # Let's say -190 px.
        
        self.is_open = False
        Window.bind(mouse_pos=self.on_mouse_pos)
        
        # Add buttons
        self.add_widget(Label(text="MENU", size_hint_y=None, height=50, bold=True, color=(0, 0.82, 0.7, 1)))
        
        btn_data = [
            ('Validação', 'validation'),
            ('Usuários', 'users'),
            ('Histórico', 'history'),
            ('Perfil', 'profile')
        ]
        
        for text, screen_name in btn_data:
            btn = HoverButton(text=text, size_hint_y=None, height=50)
            btn.bind(on_release=lambda x, s=screen_name: self.nav_callback(s))
            self.add_widget(btn)
            
        self.add_widget(Label(size_hint_y=1)) # Spacer

    def on_mouse_pos(self, window, pos):
        # Open if mouse is near left edge (e.g., < 50px)
        if pos[0] < 50:
            if not self.is_open:
                self.open_menu()
        
        # Close if mouse leaves the menu width (e.g. > 220px)
        if pos[0] > 220:
             if self.is_open:
                 self.close_menu()

    def open_menu(self):
        self.is_open = True
        Animation(pos_hint={'x': 0}, duration=0.3, t='out_quad').start(self)

    def close_menu(self):
        self.is_open = False
        # Calculate -180px in pos_hint terms if needed, or just use pos logic if parent is relative
        # Assuming FloatLayout with width 800, 200px is 0.25. 
        # Simpler: just set x position if we weren't using pos_hint.
        # But let's stick to pos_hint for responsive.
        # However, hard to map -190px to pos_hint without keeping track of window width.
        # Let's switch to using 'x' not pos_hint for the animation target if possible, 
        # OR just use a fixed small visible strip.
        # Let's try pos_hint -0.0 for open, and -0.2 for closed? 
        # If width is 200, screen is approx 1000+, 0.2 is 200.
        Animation(pos_hint={'x': -0.18}, duration=0.3, t='in_quad').start(self)
