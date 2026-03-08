from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.clock import Clock
from model.database import SQLiteDatabase
from view.screens import ValidationTab, UserManagementTab, HistoryTab, AdminLoginView, ProfileTab, NavMenu

class RFIDController(App):
    def build(self):
        self.title = 'RFID Reader System - LHC Mate Tap'
        self.db = SQLiteDatabase()
        self.is_authenticated = False
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        Window.size = (1280, 720)  # 720p resolution

        # Main Layout
        self.root_layout = FloatLayout()

        # Screen Manager
        self.sm = ScreenManager(transition=FadeTransition())

        # Screens
        # 1. Validation (Home)
        screen_val = Screen(name='validation')
        self.validation_view = ValidationTab(self.db)
        screen_val.add_widget(self.validation_view)
        screen_val.bind(on_enter=self.on_validation_enter)
        self.sm.add_widget(screen_val)

        # 2. Login
        screen_login = Screen(name='login')
        self.login_view = AdminLoginView(self.db, self.on_login_success)
        screen_login.add_widget(self.login_view)
        self.sm.add_widget(screen_login)

        # 3. Users (Protected)
        screen_users = Screen(name='users')
        self.users_view = UserManagementTab(self.db)
        screen_users.add_widget(self.users_view)
        self.sm.add_widget(screen_users)

        # 4. History (Protected)
        screen_history = Screen(name='history')
        self.history_view = HistoryTab(self.db)
        screen_history.add_widget(self.history_view)
        self.sm.add_widget(screen_history)

        # 5. Profile (Protected)
        screen_profile = Screen(name='profile')
        self.profile_view = ProfileTab(self.logout_admin)
        screen_profile.add_widget(self.profile_view)
        self.sm.add_widget(screen_profile)

        # Add ScreenManager to Layout
        self.root_layout.add_widget(self.sm)

        # Add Navigation Menu (Overlay)
        self.nav_menu = NavMenu(nav_callback=self.navigate_to)
        self.root_layout.add_widget(self.nav_menu)

        self.target_screen = None # Where to go after login

        return self.root_layout

    def navigate_to(self, screen_name):
        # Handle protected routes
        if screen_name in ['users', 'history', 'profile']:
            if not self.is_authenticated:
                self.target_screen = screen_name
                self.sm.current = 'login'
                return
            else:
                # Refresh data if needed
                if screen_name == 'users':
                    self.users_view.refresh_data()
                elif screen_name == 'history':
                    self.history_view.refresh_data()
        
        self.sm.current = screen_name
        self.nav_menu.close_menu()
    
    def on_validation_enter(self, instance):
        # Restore focus to scan input when returning to validation tab
        if hasattr(self.validation_view.ids, 'scan_input'):
            Clock.schedule_once(lambda dt: setattr(self.validation_view.ids.scan_input, 'focus', True), 0.2)

    def on_login_success(self):
        self.is_authenticated = True
        target = self.target_screen if self.target_screen else 'users'
        self.navigate_to(target)
        self.target_screen = None

    def logout_admin(self):
        self.is_authenticated = False
        self.sm.current = 'validation'

    def update_history_tab(self):
        if self.history_view:
            self.history_view.refresh_data()
