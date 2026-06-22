"""
main.py
-------
Punto de entrada del sistema Xorte - Lab Inventory Manager.
Se encarga de:
  1. Inicializar la base de datos (crear tablas y admin por defecto).
  2. Lanzar la ventana de login.
  3. Controlar el ciclo de sesión: login → dashboard → logout → login.

Autores: Equipo de Ingeniería Informática - 
Proyecto: Xorte - Lab Inventory Manager
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
    Cuando el login es exitoso, destruye esa ventana y abre el dashboard.
    Cuando el usuario cierra sesión desde el dashboard, vuelve a llamar
    esta misma función (ciclo de re-autenticación).
    """
    auth_ctrl = AuthController()

    # Creamos la ventana de login y le pasamos el controlador + callback de éxito
    login_window = LoginView(
        auth_controller=auth_ctrl,
        on_login_success=lambda: abrir_dashboard(auth_ctrl, login_window)
    )
    login_window.mainloop()


def abrir_dashboard(auth_ctrl, login_window):
    """
    Destruye el login y abre la ventana principal del sistema (dashboard).
    Cuando el usuario cierra sesión, se vuelve a llamar iniciar_sesion().
    """
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
