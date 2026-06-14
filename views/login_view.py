"""
views/login_view.py
--------------------
Vista de autenticación. Contiene tres pantallas en una sola ventana:
  1. Formulario de login principal.
  2. Modal de cambio de contraseña obligatorio (primer ingreso).
  3. Modal de recuperación de cuenta por preguntas de seguridad.

Toda lógica real está delegada al AuthController.
Esta vista solo captura inputs y muestra resultados.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from views.theme import (
    BG_MAIN, BG_CARD, BG_INPUT, BORDER_INPUT,
    TXT_INPUT, TXT_PLACEHOLDER, TXT_MAIN, TXT_MUTED,
    ACCENT_BLUE, ACCENT_HOVER, BTN_RADIUS, BTN_H, INPUT_H,
    font_title, font_section, font_body, font_small
)


class LoginView(ctk.CTk):
    """Ventana principal de inicio de sesión del sistema Xorte."""

    def __init__(self, auth_controller, on_login_success):
        super().__init__()
        self.auth = auth_controller
        self.on_login_success = on_login_success

        self.title("Xorte — Autenticación")
        self.geometry("420x520")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)

        self._construir_ui()
        # Permitir login con Enter desde cualquier campo
        self.bind("<Return>", lambda e: self._intentar_login())

    def _construir_ui(self):
        card = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=12,
            border_width=1, border_color=BORDER_INPUT
        )
        card.pack(fill="both", expand=True, padx=30, pady=35)

        # Encabezado
        ctk.CTkLabel(
            card, text="XORTE",
            font=font_title(), text_color=TXT_MAIN
        ).pack(pady=(40, 4))

        ctk.CTkLabel(
            card, text="SISTEMA CENTRAL DE CONTROL",
            font=font_section(), text_color=ACCENT_BLUE
        ).pack(pady=(0, 35))

        # Campos de credenciales
        self.ent_usuario = ctk.CTkEntry(
            card, placeholder_text="Nombre de usuario",
            width=290, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_usuario.pack(pady=8)
        self.ent_usuario.focus()

        self.ent_password = ctk.CTkEntry(
            card, placeholder_text="Contraseña",
            show="*", width=290, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_password.pack(pady=8)

        # Botón de login
        ctk.CTkButton(
            card, text="INGRESAR AL SISTEMA",
            font=font_section(), width=290, height=42,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._intentar_login
        ).pack(pady=28)

        # Links secundarios
        lbl_registro = ctk.CTkLabel(
            card, text="Registrar nuevo operador del sistema",
            font=font_small(), text_color=TXT_MUTED, cursor="hand2"
        )
        lbl_registro.pack(pady=3)
        lbl_registro.bind("<Button-1>", lambda e: self._abrir_registro())

        lbl_recuperar = ctk.CTkLabel(
            card, text="Olvidé mi contraseña",
            font=font_small(), text_color="#EF4444", cursor="hand2"
        )
        lbl_recuperar.pack(pady=3)
        lbl_recuperar.bind("<Button-1>", lambda e: self._abrir_recuperacion())

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _intentar_login(self):
        username = self.ent_usuario.get().strip()
        password = self.ent_password.get()

        exito, resultado = self.auth.intentar_login(username, password)

        if not exito:
            messagebox.showerror("Acceso Denegado", resultado, parent=self)
            self.ent_password.delete(0, tk.END)
            return

        if resultado == "CAMBIO_REQUERIDO":
            CambiarPasswordModal(self, self.auth, self.on_login_success)
        else:
            self.on_login_success()

    def _abrir_registro(self):
        from views.register_user_view import RegisterUserModal
        # Importación diferida para evitar ciclos al inicio
        RegisterUserModal(self, self.auth)

    def _abrir_recuperacion(self):
        RecuperacionModal(self, self.auth)


# ------------------------------------------------------------------
# Modal: Cambio de contraseña obligatorio en primer ingreso
# ------------------------------------------------------------------

class CambiarPasswordModal(ctk.CTkToplevel):
    """
    Fuerza al usuario a crear una contraseña personal antes de entrar
    al dashboard. No puede cerrarse sin completar el proceso.
    """

    def __init__(self, parent, auth_controller, on_success):
        super().__init__(parent)
        self.auth       = auth_controller
        self.on_success = on_success

        self.title("Actualización de seguridad requerida")
        self.geometry("380x340")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # Bloquear cierre manual

        ctk.CTkLabel(
            self, text="ACTUALIZACIÓN REQUERIDA",
            font=font_section(), text_color="#EF4444"
        ).pack(pady=(28, 6))

        ctk.CTkLabel(
            self,
            text="Debes crear una contraseña personal antes\nde ingresar al sistema por primera vez.",
            font=font_body(), text_color=TXT_MUTED, justify="center"
        ).pack(pady=(0, 22))

        self.ent_nueva = ctk.CTkEntry(
            self, placeholder_text="Nueva contraseña",
            show="*", width=300, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_nueva.pack(pady=8)

        self.ent_confirmar = ctk.CTkEntry(
            self, placeholder_text="Confirmar nueva contraseña",
            show="*", width=300, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_confirmar.pack(pady=8)

        ctk.CTkButton(
            self, text="Guardar y entrar",
            font=font_section(), width=300, height=42,
            fg_color="#10B981", hover_color="#059669",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._guardar
        ).pack(pady=22)

        self.bind("<Return>", lambda e: self._guardar())

    def _guardar(self):
        nueva    = self.ent_nueva.get()
        confirma = self.ent_confirmar.get()

        exito, msg = self.auth.cambiar_password(nueva, confirma)
        if not exito:
            messagebox.showerror("Error", msg, parent=self)
            return

        messagebox.showinfo(
            "Contraseña actualizada",
            "Tu contraseña fue guardada correctamente. ¡Bienvenido a Xorte!",
            parent=self
        )
        self.destroy()
        self.on_success()


# ------------------------------------------------------------------
# Modal: Recuperación de cuenta por preguntas de seguridad
# ------------------------------------------------------------------

class RecuperacionModal(ctk.CTkToplevel):
    """
    Flujo de dos pasos para recuperar una cuenta:
    Paso 1 → buscar usuario por nombre o correo.
    Paso 2 → responder las tres preguntas de seguridad.
    """

    def __init__(self, parent, auth_controller):
        super().__init__(parent)
        self.auth = auth_controller
        self.usuario_encontrado = None

        self.title("Recuperación de cuenta")
        self.geometry("400x480")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()

        self._construir_paso1()

    # --- Paso 1: búsqueda ---

    def _construir_paso1(self):
        self.frame_paso1 = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_paso1.pack(fill="both", expand=True, padx=25, pady=20)

        ctk.CTkLabel(
            self.frame_paso1, text="RECUPERACIÓN DE CUENTA",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(10, 20))

        ctk.CTkLabel(
            self.frame_paso1,
            text="Ingresa tu nombre de usuario o correo electrónico:",
            font=font_small(), text_color=TXT_MUTED
        ).pack(pady=(0, 8))

        self.ent_busqueda = ctk.CTkEntry(
            self.frame_paso1, placeholder_text="Usuario o correo",
            width=340, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_busqueda.pack(pady=8)
        self.ent_busqueda.focus()

        ctk.CTkButton(
            self.frame_paso1, text="Buscar cuenta",
            font=font_section(), width=340, height=BTN_H,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._buscar_usuario
        ).pack(pady=18)

        self.frame_paso1.bind("<Return>", lambda e: self._buscar_usuario())

    def _buscar_usuario(self):
        busqueda = self.ent_busqueda.get().strip()
        if not busqueda:
            messagebox.showwarning("Campo vacío", "Ingresa tu usuario o correo.", parent=self)
            return

        resultado = self.auth.buscar_cuenta_recuperacion(busqueda)

        if not resultado:
            messagebox.showerror(
                "No encontrado",
                "No existe ninguna cuenta asociada a ese dato.",
                parent=self
            )
            return

        # Verificar que tenga preguntas de seguridad configuradas
        # Los índices 9, 11, 13 son q1, q2, q3 en la fila de usuario
        if not resultado[9]:
            messagebox.showwarning(
                "Sin preguntas de seguridad",
                "Esta cuenta no tiene preguntas de seguridad configuradas.\n"
                "Contacta al Administrador del sistema.",
                parent=self
            )
            return

        self.usuario_encontrado = resultado
        self.frame_paso1.pack_forget()
        self._construir_paso2()

    # --- Paso 2: respuestas de seguridad ---

    def _construir_paso2(self):
        self.frame_paso2 = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_paso2.pack(fill="both", expand=True, padx=25, pady=15)

        ctk.CTkLabel(
            self.frame_paso2,
            text=f"Cuenta: {self.usuario_encontrado[6]}",
            font=font_section(), text_color=ACCENT_BLUE
        ).pack(pady=(0, 15))

        # Pregunta 1
        ctk.CTkLabel(
            self.frame_paso2, text=self.usuario_encontrado[9],
            font=font_small(), text_color=TXT_MUTED, wraplength=340
        ).pack(anchor="w")
        self.ent_r1 = ctk.CTkEntry(
            self.frame_paso2, placeholder_text="Tu respuesta",
            width=340, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_r1.pack(pady=(2, 12))

        # Pregunta 2
        ctk.CTkLabel(
            self.frame_paso2, text=self.usuario_encontrado[11],
            font=font_small(), text_color=TXT_MUTED, wraplength=340
        ).pack(anchor="w")
        self.ent_r2 = ctk.CTkEntry(
            self.frame_paso2, placeholder_text="Tu respuesta",
            width=340, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_r2.pack(pady=(2, 12))

        # Pregunta 3
        ctk.CTkLabel(
            self.frame_paso2, text=self.usuario_encontrado[13],
            font=font_small(), text_color=TXT_MUTED, wraplength=340
        ).pack(anchor="w")
        self.ent_r3 = ctk.CTkEntry(
            self.frame_paso2, placeholder_text="Tu respuesta",
            width=340, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_r3.pack(pady=(2, 18))

        ctk.CTkButton(
            self.frame_paso2, text="Verificar identidad",
            font=font_section(), width=340, height=BTN_H,
            fg_color="#10B981", hover_color="#059669",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._verificar
        ).pack()

    def _verificar(self):
        exito, resultado = self.auth.verificar_respuestas_seguridad(
            self.usuario_encontrado,
            self.ent_r1.get(),
            self.ent_r2.get(),
            self.ent_r3.get()
        )

        if exito:
            messagebox.showinfo(
                "Identidad verificada",
                f"Verificación exitosa.\n\nTu contraseña actual es:\n\n  {resultado}\n\n"
                "Te recomendamos cambiarla después de ingresar.",
                parent=self
            )
            self.destroy()
        else:
            messagebox.showerror("Verificación fallida", resultado, parent=self)
