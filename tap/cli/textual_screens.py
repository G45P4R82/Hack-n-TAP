"""
textual_screens.py - Agregador de Views (MVC Pattern)

Este arquivo serve apenas para manter compatibilidade com imports antigos.
Todas as views foram separadas em arquivos individuais na pasta views/

Estrutura:
- views/validation_view.py  (~120 linhas)
- views/login_view.py (~70 linhas)
- views/users_view.py (~90 linhas)
- views/history_view.py (~60 linhas)
- views/admin_view.py (~120 linhas)
- modals/user_modals.py (~200 linhas)
"""

# Import all views from the refactored structure
from cli.views import (
    ValidationScreen,
    LoginScreen,
    UserManagementScreen,
    HistoryScreen,
    ProfileScreen
)

# Import all modals
from cli.modals import (
    AddUserModal,
    UserActionModal,
    EditUserModal,
    DeleteUserModal
)

__all__ = [
    # Views
    'ValidationScreen',
    'LoginScreen',
    'UserManagementScreen',
    'HistoryScreen',
    'ProfileScreen',
    # Modals
    'AddUserModal',
    'UserActionModal',
    'EditUserModal',
    'DeleteUserModal',
]
