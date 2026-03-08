"""
Views do sistema - imports centralizados
"""
from .validation_view import ValidationScreen
from .login_view import LoginScreen
from .users_view import UserManagementScreen
from .history_view import HistoryScreen
from .admin_view import ProfileScreen

__all__ = [
    'ValidationScreen',
    'LoginScreen', 
    'UserManagementScreen',
    'HistoryScreen',
    'ProfileScreen'
]
