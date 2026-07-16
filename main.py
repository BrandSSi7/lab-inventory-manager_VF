"""
main.py
-------
"""

import customtkinter as ctk

from database import inicializar_base_de_datos
from controllers.auth_controller import AuthController
from views.login_view import LoginView
from views.dashboard_view import DashboardView


# Tema inicial de la aplicación
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def iniciar_sesion():
    """
    Lanza la ventana de inicio de sesión.
    """
    auth_ctrl = AuthController()

    # Creamos la ventana de login y le pasamos el controlador + callback de éxito
    login_window = LoginView(
        auth_controller=auth_ctrl,
        on_login_success=lambda: abrir_dashboard(auth_ctrl, login_window)
    )
    login_window.mainloop()

def abrir_dashboard(auth_ctrl, login_window):
    
    login_window.destroy()

    dashboard = DashboardView(
        auth_controller=auth_ctrl,
        on_logout=iniciar_sesion
    )
    dashboard.mainloop()


if __name__ == "__main__":
    # Paso 1: Asegurar que la BD y todas las tablas existen
    inicializar_base_de_datos()

    # Paso 2: Arrancar el ciclo de autenticación
    iniciar_sesion()
