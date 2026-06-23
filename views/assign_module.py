"""
views/assign_module.py
-----------------------
Módulo visual de Asignación de Préstamos.
El responsable se elige EXCLUSIVAMENTE desde un CTkComboBox alimentado por el
UserController. No hay campos de texto libre para el prestatario.

Layout: tabla de equipos operativos (izquierda) + formulario de asignación (derecha).

Autores: Equipo de Ingeniería Informática
Proyecto: Xorte - Lab Inventory Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime

from views.theme import (
    BG_CARD, BG_INPUT, BORDER_INPUT, TXT_INPUT, TXT_PLACEHOLDER,
    TXT_MAIN, TXT_MUTED, ACCENT_BLUE, ACCENT_HOVER,
    BTN_RADIUS, INPUT_H, BTN_H, font_title, font_section, font_small,
    BG_DARK_CARD, BG_LIGHT_CARD
)


class AssignModule(ctk.CTkFrame):
    """Frame del módulo de asignación. Montado en el área principal del Dashboard."""

    def __init__(self, parent, loan_controller, asset_controller,
                 user_controller, auth_controller):
        super().__init__(parent, fg_color="transparent")
        self.loan_ctrl  = loan_controller
        self.asset_ctrl = asset_controller
        self.user_ctrl  = user_controller
        self.auth       = auth_controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._construir_header()
        self._construir_cuerpo()
        self._cargar_equipos_disponibles()
        self._recargar_combo_prestatarios()

    # Construcción de la UI

    def _construir_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        ctk.CTkLabel(
            header, text="NUEVA ASIGNACIÓN DE PRÉSTAMO",
            font=font_title(), text_color=TXT_MAIN
        ).pack(side="left")

    def _construir_cuerpo(self):
        """Layout de dos columnas: tabla de equipos | formulario."""
        cuerpo = ctk.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew")
        cuerpo.grid_columnconfigure(0, weight=3)
        cuerpo.grid_columnconfigure(1, weight=2)
        cuerpo.grid_rowconfigure(0, weight=1)

        self._construir_panel_equipos(cuerpo)
        self._construir_panel_formulario(cuerpo)

    def _construir_panel_equipos(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel, text="1. Selecciona el equipo a prestar",
            font=font_section(), text_color=TXT_MUTED
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        # Tabla de equipos OPERATIVOS (los únicos que se pueden prestar)
        cols = ("id", "nombre", "serial", "estado")
        self.tree_equipos = ttk.Treeview(
            panel, columns=cols, show="headings",
            selectmode="browse", height=16
        )
        config = {
            "id":     ("ID",       45,  False),
            "nombre": ("Equipo",  220,  True),
            "serial": ("Serial",  130,  True),
            "estado": ("Estado",   90,  False),
        }
        for col, (texto, ancho, stretch) in config.items():
            self.tree_equipos.heading(col, text=texto, anchor="w")
            self.tree_equipos.column(col, width=ancho, anchor="w", stretch=stretch)

        self.tree_equipos.grid(row=1, column=0, sticky="nsew")
        self._aplicar_colores_tabla()

        ctk.CTkButton(
            panel, text="↻ Actualizar lista de equipos",
            height=30, width=200,
            fg_color=("#CBD5E1", "#374151"), hover_color=("#94A3B8", "#4B5563"),
            text_color=TXT_MUTED, corner_radius=BTN_RADIUS,
            command=self._cargar_equipos_disponibles
        ).grid(row=2, column=0, pady=(8, 0), sticky="w")

    def _construir_panel_formulario(self, parent):
        panel = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10,
                             border_width=1, border_color=BORDER_INPUT)
        panel.grid(row=0, column=1, sticky="nsew")

        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=18, pady=18)

        ctk.CTkLabel(
            scroll, text="2. Completa los datos del préstamo",
            font=font_section(), text_color=TXT_MUTED
        ).pack(anchor="w", pady=(0, 14))

        # --- Prestatario: SOLO ComboBox, sin texto libre ni alta rápida ---
        ctk.CTkLabel(scroll, text="Responsable del préstamo: *",
                     font=font_small(), text_color=TXT_MUTED).pack(anchor="w")
        ctk.CTkLabel(
            scroll,
            text="Solo se puede elegir un usuario ya registrado en el sistema.",
            font=ctk.CTkFont(size=10), text_color="#EF4444"
        ).pack(anchor="w", pady=(0, 4))

        self.combo_prestatario = ctk.CTkComboBox(
            scroll, values=[], width=300, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER
        )
        self.combo_prestatario.pack(pady=(0, 12), anchor="w")

        # --- Fechas con autocompletado ---
        ctk.CTkLabel(scroll, text="Fecha del préstamo: *",
                     font=font_small(), text_color=TXT_MUTED).pack(anchor="w")
        self.ent_fecha_p = ctk.CTkEntry(
            scroll, width=300, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT
        )
        self.ent_fecha_p.pack(pady=(3, 12), anchor="w")
        self.ent_fecha_p.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_fecha_p.bind("<KeyRelease>", lambda e: self._autocompletar(self.ent_fecha_p, e))

        ctk.CTkLabel(scroll, text="Fecha de devolución: *",
                     font=font_small(), text_color=TXT_MUTED).pack(anchor="w")
        self.ent_fecha_d = ctk.CTkEntry(
            scroll, width=300, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT
        )
        self.ent_fecha_d.pack(pady=(3, 12), anchor="w")
        self.ent_fecha_d.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_fecha_d.bind("<KeyRelease>", lambda e: self._autocompletar(self.ent_fecha_d, e))

        # --- Ubicación y observación ---
        ctk.CTkLabel(scroll, text="Ubicación / Destino: *",
                     font=font_small(), text_color=TXT_MUTED).pack(anchor="w")
        self.ent_ubicacion = ctk.CTkEntry(
            scroll, placeholder_text="Ej: Laboratorio Central A",
            width=300, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_ubicacion.pack(pady=(3, 12), anchor="w")

        ctk.CTkLabel(scroll, text="Observación (opcional):",
                     font=font_small(), text_color=TXT_MUTED).pack(anchor="w")
        self.ent_observacion = ctk.CTkEntry(
            scroll, placeholder_text="Motivo, notas...",
            width=300, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_observacion.pack(pady=(3, 20), anchor="w")

        ctk.CTkButton(
            scroll, text="🔒 Confirmar préstamo",
            font=font_section(), height=44,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._procesar_prestamo
        ).pack(fill="x", pady=(0, 8))

    # Carga de datos

    def _cargar_equipos_disponibles(self):
        for item in self.tree_equipos.get_children():
            self.tree_equipos.delete(item)

        for i, eq in enumerate(self.asset_ctrl.obtener_activos_operativos()):
            tag = "par" if i % 2 == 0 else "impar"
            # Columnas mostradas: id, nombre, serial, estado
            self.tree_equipos.insert("", "end",
                                     values=(eq[0], eq[1], eq[4], eq[5]),
                                     tags=(tag,))

    def _recargar_combo_prestatarios(self, preseleccionar=None):
        """Recarga la lista del ComboBox desde el UserController."""
        nombres = self.user_ctrl.obtener_nombres_para_combo()
        self.combo_prestatario.configure(values=nombres)
        if preseleccionar and preseleccionar in nombres:
            self.combo_prestatario.set(preseleccionar)
        elif nombres:
            self.combo_prestatario.set(nombres[0])
        else:
            self.combo_prestatario.set("")

    # Acciones

    def _procesar_prestamo(self):
        seleccion = self.tree_equipos.selection()
        if not seleccion:
            messagebox.showerror(
                "Sin equipo seleccionado",
                "Haz clic en un equipo de la tabla izquierda antes de confirmar.",
                parent=self
            )
            return

        valores_eq  = self.tree_equipos.item(seleccion[0])["values"]
        id_activo   = valores_eq[0]
        nombre_eq   = valores_eq[1]
        prestatario = self.combo_prestatario.get().strip()

        if not prestatario:
            messagebox.showerror(
                "Sin prestatario",
                "Debes seleccionar un responsable de la lista desplegable.",
                parent=self
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar asignación",
            f"¿Asignar '{nombre_eq}' a '{prestatario}'?\n\n"
            f"Fecha préstamo: {self.ent_fecha_p.get()}\n"
            f"Fecha devolución: {self.ent_fecha_d.get()}\n"
            f"Ubicación: {self.ent_ubicacion.get()}",
            parent=self
        )
        if not confirmar:
            return

        datos = {
            "id_activo":        id_activo,
            "prestatario":      prestatario,
            "fecha_prestamo":   self.ent_fecha_p.get().strip(),
            "fecha_devolucion": self.ent_fecha_d.get().strip(),
            "ubicacion":        self.ent_ubicacion.get().strip(),
        }

        exito, msg = self.loan_ctrl.registrar_prestamo(datos)

        if exito:
            messagebox.showinfo("Préstamo registrado", msg, parent=self)
            self._limpiar_formulario()
            self._cargar_equipos_disponibles()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _limpiar_formulario(self):
        self.ent_fecha_d.delete(0, tk.END)
        self.ent_fecha_d.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_ubicacion.delete(0, tk.END)
        self.ent_observacion.delete(0, tk.END)

    # Helpers visuales

    def _autocompletar(self, campo: ctk.CTkEntry, event):
        """Inserta '/' en las posiciones 2 y 4 al escribir una fecha."""
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return
        texto = "".join(c for c in campo.get() if c.isdigit())[:8]
        formateado = ""
        for i, c in enumerate(texto):
            if i in (2, 4):
                formateado += "/"
            formateado += c
        campo.delete(0, tk.END)
        campo.insert(0, formateado)

    def _aplicar_colores_tabla(self):
        es_oscuro = ctk.get_appearance_mode() == "Dark"
        self.tree_equipos.tag_configure("par",   background=BG_DARK_CARD if es_oscuro else BG_LIGHT_CARD)
        self.tree_equipos.tag_configure("impar", background="#1E293B"     if es_oscuro else "#F1F5F9")

