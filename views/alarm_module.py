
"""
views/alarm_module.py
----------------------
Módulo visual del Panel de Alarmas e Incidencias.
Muestra los equipos que requieren atención inmediata: revisiones vencidas
y activos marcados como INACTIVO.

El modal de atención delega toda la lógica al AssetController.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from datetime import datetime, timedelta

from views.theme import (
    BG_MAIN, BG_CARD, BG_INPUT, BORDER_INPUT, TXT_INPUT, TXT_PLACEHOLDER,
    TXT_MAIN, TXT_MUTED, ACCENT_BLUE, ACCENT_HOVER,
    BTN_RADIUS, INPUT_H, BTN_H, font_title, font_section, font_small,
    BG_DARK_CARD, BG_LIGHT_CARD
)


class AlarmModule(ctk.CTkFrame):
    """Frame del panel de alarmas. Montado en el área principal del Dashboard."""

    def __init__(self, parent, asset_controller, auth_controller):
        super().__init__(parent, fg_color="transparent")
        self.ctrl = asset_controller
        self.auth = auth_controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._construir_header()
        self._construir_toolbar()
        self._construir_tabla()
        self._construir_footer()
        self._cargar_datos()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _construir_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        ctk.CTkLabel(
            header, text="PANEL DE CONTROL OPERATIVO E INCIDENCIAS",
            font=font_title(), text_color=TXT_MAIN
        ).pack(side="left")

    def _construir_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        self.ent_busqueda = ctk.CTkEntry(
            toolbar,
            placeholder_text="🔍  Buscar por nombre, modelo, serial...",
            width=290, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_busqueda.pack(side="left", padx=(0, 12))
        self.ent_busqueda.bind("<KeyRelease>", lambda e: self._cargar_datos())

        ctk.CTkButton(
            toolbar, text="Limpiar filtros",
            width=110, height=34,
            fg_color=("#CBD5E1", "#374151"), hover_color=("#94A3B8", "#4B5563"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._limpiar_filtros
        ).pack(side="left")

        # Contador de alarmas activas
        self.lbl_contador = ctk.CTkLabel(
            toolbar, text="",
            font=font_small(), text_color="#EF4444"
        )
        self.lbl_contador.pack(side="right")

    def _construir_tabla(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.grid(row=2, column=0, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        self.scroll_y = ttk.Scrollbar(contenedor, orient="vertical")
        self.scroll_x = ttk.Scrollbar(contenedor, orient="horizontal")

        cols = ("id", "equipo", "estado", "descripcion", "modelo", "fecha", "severidad")
        self.tree = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)

        # PARCHE: se oculta la columna "id" de la vista (a petición del
        # profesor). Se conserva como columna de datos (valores[0] sigue
        # siendo el id_activo, usado internamente por _abrir_atender), pero
        # se excluye de "displaycolumns".
        cols_visibles = tuple(c for c in cols if c != "id")

        # Mismo ancho y centrado para todas las columnas visibles (espaciado uniforme).
        ANCHO_COLUMNA = 265
        encabezados = {
            "id": "ID Incidencia", "equipo": "Activo Comprometido",
            "estado": "Estado Crítico", "descripcion": "Diagnóstico",
            "modelo": "Modelo", "fecha": "Fecha Límite", "severidad": "Severidad",
        }
        for col in cols_visibles:
            self.tree.heading(col, text=encabezados[col], anchor="center")
            self.tree.column(col, width=ANCHO_COLUMNA, anchor="center", stretch=True)

        self.tree.column("id", width=0, minwidth=0, stretch=False)
        self.tree["displaycolumns"] = cols_visibles

        self.tree.bind("<Button-1>",  self._bloquear_resize)
        self.tree.bind("<B1-Motion>", self._bloquear_resize)
        self.tree.bind("<Double-1>",  lambda e: self._abrir_atender())

        # PARCHE QA: el árbol y las dos barras de desplazamiento se ubican
        # con grid() de forma consistente. Antes solo el árbol usaba pack()
        # y ninguna barra llegaba a mostrarse, por lo que columnas que no
        # entraban en el ancho visible quedaban inaccesibles.
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")

        self._aplicar_colores_filas()

    def _construir_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", pady=(16, 0))

        ctk.CTkButton(
            footer, text="Actualizar", width=100, height=BTN_H,
            fg_color=("#CBD5E1", "#4B5563"), hover_color=("#94A3B8", "#374151"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._cargar_datos
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="Atender incidencia", width=150, height=BTN_H,
            font=font_section(),
            fg_color="#D97706", hover_color="#B45309",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._abrir_atender
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def _cargar_datos(self):
        busqueda = self.ent_busqueda.get().strip()

        for item in self.tree.get_children():
            self.tree.delete(item)

        alarmas = self.ctrl.obtener_alarmas(busqueda)

        for i, fila in enumerate(alarmas):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=fila, tags=(tag,))

        # Actualizar el contador en la toolbar
        n = len(alarmas)
        self.lbl_contador.configure(
            text=f"⚠  {n} incidencia{'s' if n != 1 else ''} activa{'s' if n != 1 else ''}"
            if n > 0 else "✔  Sin incidencias activas",
            text_color="#EF4444" if n > 0 else "#10B981"
        )

    def _limpiar_filtros(self):
        self.ent_busqueda.delete(0, tk.END)
        self._cargar_datos()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _abrir_atender(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo(
                "Atención", "Selecciona una incidencia de la tabla primero.", parent=self
            )
            return
        valores = self.tree.item(seleccion[0])["values"]
        # valores[0] = id_activo, valores[1] = nombre_equipo
        AtenderAlarmaModal(self, self.ctrl, valores[0], valores[1], self._cargar_datos)

    # ------------------------------------------------------------------
    # Helpers visuales
    # ------------------------------------------------------------------

    def _bloquear_resize(self, event):
        if self.tree.identify_region(event.x, event.y) == "separator":
            return "break"

    def _aplicar_colores_filas(self):
        es_oscuro = ctk.get_appearance_mode() == "Dark"
        self.tree.tag_configure("par",   background=BG_DARK_CARD if es_oscuro else BG_LIGHT_CARD)
        self.tree.tag_configure("impar", background="#1E293B"     if es_oscuro else "#F1F5F9")


# ------------------------------------------------------------------
# Modal: Atender una incidencia de mantenimiento
# ------------------------------------------------------------------

class AtenderAlarmaModal(ctk.CTkToplevel):

    def __init__(self, parent, controller, id_activo, nombre_equipo, on_saved):
        super().__init__(parent)
        self.ctrl         = controller
        self.id_activo    = id_activo
        self.nombre_equipo = nombre_equipo
        self.on_saved     = on_saved

        # Obtener el custodio actual del equipo para mostrarlo en el modal
        # Buscamos el serial primero a través del controlador
        self.custodio = self.ctrl.obtener_custodio(self._obtener_serial())

        self.title(f"Atender incidencia — ID {id_activo}")
        self.geometry("500x460")
        self.resizable(False, False)
        self.configure(fg_color=BG_MAIN)
        self.grab_set()

        self._construir_ui()

    def _obtener_serial(self) -> str:
        """Obtiene el serial del equipo consultando directamente los activos."""
        activos = self.ctrl.obtener_activos()
        for a in activos:
            if a[0] == self.id_activo:
                return a[4]  # índice 4 = serial
        return ""

    def _construir_ui(self):
        # PARCHE: tarjeta central proporcional (tamaño relativo, sin panel
        # de marca) para acciones internas rápidas dentro de la app.
        card = ctk.CTkFrame(
            self, fg_color=BG_CARD, corner_radius=12,
            border_width=1, border_color=BORDER_INPUT
        )
        card.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.88)

        ctk.CTkLabel(
            card, text=f"RESOLUCIÓN DE INCIDENCIA (ID: {self.id_activo})",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(22, 8))

        frame = ctk.CTkFrame(card, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=22, pady=5)

        # Información del activo
        ctk.CTkLabel(
            frame,
            text=f"Activo: {self.nombre_equipo}",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=ACCENT_BLUE
        ).pack(anchor="w", pady=(0, 2))

        ctk.CTkLabel(
            frame,
            text=f"Custodio actual: {self.custodio}",
            font=font_small(), text_color=TXT_MUTED
        ).pack(anchor="w", pady=(0, 18))

        # Nueva fecha de revisión con autocompletado
        ctk.CTkLabel(
            frame, text="Nueva fecha de próxima revisión:",
            font=font_small(), text_color=TXT_MUTED
        ).pack(anchor="w")

        self.ent_fecha = ctk.CTkEntry(
            frame, width=420, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT
        )
        self.ent_fecha.pack(pady=(3, 16))
        # Sugerir 30 días hacia adelante como fecha por defecto
        self.ent_fecha.insert(0, (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"))
        self.ent_fecha.bind("<KeyRelease>", self._autocompletar_fecha)

        # Nuevo estado del equipo
        ctk.CTkLabel(
            frame, text="Actualizar estado del activo:",
            font=font_small(), text_color=TXT_MUTED
        ).pack(anchor="w")

        self.combo_estado = ctk.CTkComboBox(
            frame,
            values=["OPERATIVO", "MANTENIMIENTO", "ASIGNADO", "INACTIVO"],
            width=420, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER
        )
        self.combo_estado.set("OPERATIVO")
        self.combo_estado.pack(pady=(3, 22))

        ctk.CTkButton(
            card, text="Guardar y resolver incidencia",
            font=font_section(), height=42,
            fg_color="#10B981", hover_color="#059669",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._guardar
        ).pack(pady=(0, 18), padx=22, fill="x")

    def _autocompletar_fecha(self, event):
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return
        texto = "".join(c for c in self.ent_fecha.get() if c.isdigit())[:8]
        formateado = ""
        for i, c in enumerate(texto):
            if i in (2, 4):
                formateado += "/"
            formateado += c
        self.ent_fecha.delete(0, tk.END)
        self.ent_fecha.insert(0, formateado)

    def _guardar(self):
        nueva_fecha  = self.ent_fecha.get().strip()
        nuevo_estado = self.combo_estado.get()

        confirmar = messagebox.askyesno(
            "Confirmar resolución",
            f"¿Marcar la incidencia del activo '{self.nombre_equipo}' como resuelta?\n\n"
            f"Nueva fecha de revisión: {nueva_fecha}\n"
            f"Nuevo estado: {nuevo_estado}",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.resolver_alarma(self.id_activo, nueva_fecha, nuevo_estado)

        if exito:
            messagebox.showinfo("Incidencia resuelta", msg, parent=self)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error de validación", msg, parent=self)

