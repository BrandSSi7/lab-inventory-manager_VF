
"""
views/register_user_view.py
----------------------------
Modal de registro de un nuevo operador del sistema.
El formulario vive dentro de un CTkScrollableFrame para garantizar
que el botón 'Guardar' sea siempre visible sin importar la resolución.

Autocompletado de '/' en la fecha de nacimiento con evento <KeyRelease>.
Validación de preguntas de seguridad distintas en tiempo real.

Autores: Equipo de Ingeniería Informática
Proyecto: Xorte - Lab Inventory Manager
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from controllers.user_controller import UserController
from views.theme import (
    BG_CARD, BG_INPUT, BORDER_INPUT, TXT_INPUT, TXT_PLACEHOLDER,
    TXT_MAIN, TXT_MUTED, ACCENT_BLUE, ACCENT_HOVER,
    BTN_RADIUS, INPUT_H, BTN_H, font_section, font_body, font_small
)

PREGUNTAS = [
    "¿Cuál es el nombre de tu universidad o instituto?",
    "¿Cuál es el nombre de tu primera mascota?",
    "¿En qué ciudad naciste?",
    "¿Cuál fue el modelo de tu primer vehículo?",
    "¿Cuál es tu comida favorita?",
]


class RegisterUserModal(ctk.CTkToplevel):
    """
    Modal de alta de usuario con ScrollableFrame interno.
    Puede ser abierto desde el Login o desde el módulo de Usuarios.
    Recibe un callback opcional para refrescar la tabla al cerrar.
    """

    def __init__(self, parent, auth_controller, on_saved=None):
        super().__init__(parent)
        self.ctrl     = UserController(auth_controller)
        self.on_saved = on_saved

        self.title("Registro de nuevo operador")
        self.geometry("460x680")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()

        self._construir_ui()

    def _construir_ui(self):
        ctk.CTkLabel(
            self, text="REGISTRO DEL SISTEMA",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(20, 5))

        # ScrollableFrame: soluciona el bug donde el botón desaparecía
        # en pantallas con resolución menor a 768px de alto
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def entry(placeholder, show=""):
            e = ctk.CTkEntry(
                scroll, placeholder_text=placeholder,
                show=show, width=390, height=INPUT_H,
                fg_color=BG_INPUT, border_color=BORDER_INPUT,
                text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
            )
            e.pack(pady=6)
            return e

        # --- Datos personales ---
        ctk.CTkLabel(
            scroll, text="DATOS PERSONALES",
            font=font_small(), text_color=ACCENT_BLUE
        ).pack(anchor="w", pady=(10, 2))

        self.ent_nombre   = entry("Nombres y apellidos")
        self.ent_cedula   = entry("Cédula / Documento (solo números, ej: 12345678)")
        self.ent_fnac     = entry("Fecha de nacimiento (DD/MM/AAAA)")
        self.ent_fnac.bind("<KeyRelease>", self._autocompletar_fecha)
        self.ent_correo   = entry("Correo electrónico")
        self.ent_telefono = entry("Teléfono (solo números)")

        # --- Credenciales ---
        ctk.CTkLabel(
            scroll, text="CREDENCIALES DE ACCESO",
            font=font_small(), text_color=ACCENT_BLUE
        ).pack(anchor="w", pady=(18, 2))

        self.ent_usuario = entry("Nombre de usuario (login)")
        self.ent_pwd     = entry("Contraseña temporal", show="*")

        # --- Preguntas de seguridad ---
        ctk.CTkLabel(
            scroll, text="PREGUNTAS DE SEGURIDAD",
            font=font_small(), text_color=ACCENT_BLUE
        ).pack(anchor="w", pady=(18, 2))

        ctk.CTkLabel(
            scroll,
            text="Las tres preguntas y sus respuestas deben ser distintas entre sí.",
            font=font_small(), text_color=TXT_MUTED, wraplength=390
        ).pack(anchor="w", pady=(0, 8))

        self.combo_q1 = self._combo_pregunta(scroll, PREGUNTAS[0])
        self.ent_a1   = entry("Respuesta 1")

        self.combo_q2 = self._combo_pregunta(scroll, PREGUNTAS[1])
        self.ent_a2   = entry("Respuesta 2")

        self.combo_q3 = self._combo_pregunta(scroll, PREGUNTAS[2])
        self.ent_a3   = entry("Respuesta 3")

        # --- Botón guardar (dentro del scroll = siempre visible) ---
        ctk.CTkButton(
            scroll, text="Registrar operador",
            font=font_section(), height=42, width=390,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._guardar
        ).pack(pady=(20, 15))

    def _combo_pregunta(self, parent, default):
        combo = ctk.CTkComboBox(
            parent, values=PREGUNTAS, width=390, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, button_color=BG_INPUT,
            button_hover_color=ACCENT_HOVER,
            command=self._actualizar_opciones_preguntas
        )
        combo.set(default)
        combo.pack(pady=(6, 0))
        return combo

    def _autocompletar_fecha(self, event):
        """Inserta '/' automáticamente en la posición correcta al escribir."""
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return
        texto = self.ent_fnac.get().replace("/", "")
        texto = "".join(c for c in texto if c.isdigit())[:8]

        formateado = ""
        for i, c in enumerate(texto):
            if i in (2, 4):
                formateado += "/"
            formateado += c

        self.ent_fnac.delete(0, tk.END)
        self.ent_fnac.insert(0, formateado)

    def _actualizar_opciones_preguntas(self, _=None):
        """
        Recalcula las opciones de cada ComboBox para que no permita
        seleccionar la misma pregunta en dos campos distintos.
        """
        v1 = self.combo_q1.get()
        v2 = self.combo_q2.get()
        v3 = self.combo_q3.get()

        self.combo_q1.configure(values=[q for q in PREGUNTAS if q == v1 or q not in (v2, v3)])
        self.combo_q2.configure(values=[q for q in PREGUNTAS if q == v2 or q not in (v1, v3)])
        self.combo_q3.configure(values=[q for q in PREGUNTAS if q == v3 or q not in (v1, v2)])

    def _guardar(self):
        datos = {
            "nombres":   self.ent_nombre.get().strip(),
            "cedula":    self.ent_cedula.get().strip(),
            "fecha_nac": self.ent_fnac.get().strip(),
            "correo":    self.ent_correo.get().strip(),
            "telefono":  self.ent_telefono.get().strip(),
            "username":  self.ent_usuario.get().strip(),
            "password":  self.ent_pwd.get().strip(),
            "q1": self.combo_q1.get(), "a1": self.ent_a1.get().strip(),
            "q2": self.combo_q2.get(), "a2": self.ent_a2.get().strip(),
            "q3": self.combo_q3.get(), "a3": self.ent_a3.get().strip(),
        }

        # Defensa en profundidad — capa Vista: validar formato de identificación
        # antes de enviar al controlador para dar retroalimentación inmediata.
        cedula = datos["cedula"]
        if not cedula.isdigit() or len(cedula) < 3:
            messagebox.showerror(
                "Identificación inválida",
                "La identificación solo puede contener números y debe tener al menos 3 dígitos.\n"
                "Ejemplo correcto: 12345678",
                parent=self
            )
            self.ent_cedula.focus_set()
            return

        exito, msg = self.ctrl.registrar_usuario(datos)

        if not exito:
            messagebox.showerror("Error de validación", msg, parent=self)
            return

        messagebox.showinfo(
            "Registro exitoso",
            f"El operador '{datos['nombres'].title()}' fue registrado correctamente.\n"
            "Deberá cambiar su contraseña temporal en el primer inicio de sesión.",
            parent=self
        )
        if self.on_saved:
            self.on_saved()
        self.destroy()


