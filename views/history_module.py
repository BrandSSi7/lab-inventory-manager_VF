
"""
views/history_module.py
------------------------
Módulo visual del Historial de Auditoría del Sistema.
Este módulo es estrictamente de SOLO LECTURA: no hay botones de crear,
editar ni eliminar. El usuario puede buscar, filtrar y exportar los logs.

Filtros disponibles:
  - Búsqueda de texto libre (sobre acción, referencia, responsable, detalles)
  - Categoría: Todos | Equipos | Usuarios | Préstamos | Sistema
  - Orden: Más Recientes, Más Antiguos, A-Z por distintos campos

Autores: Equipo de Ingeniería Informática
Proyecto: Xorte - Lab Inventory Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from views.theme import (
    BG_CARD, BG_INPUT, BORDER_INPUT, TXT_INPUT, TXT_PLACEHOLDER,
    TXT_MAIN, TXT_MUTED, ACCENT_BLUE, ACCENT_HOVER,
    BTN_RADIUS, INPUT_H, BTN_H, font_title, font_section, font_small,
    BG_DARK_CARD, BG_LIGHT_CARD
)

CATEGORIAS   = ["Todos", "Equipos", "Usuarios", "Préstamos", "Sistema"]
ORDENES      = ["Más Recientes", "Más Antiguos", "A-Z (Acción)",
                "A-Z (Activo)", "A-Z (Usuario)", "A-Z (Detalles)"]


class HistoryModule(ctk.CTkFrame):
    """Frame del módulo de historial. Montado en el área principal del Dashboard."""

    def __init__(self, parent, history_controller):
        super().__init__(parent, fg_color="transparent")
        self.ctrl = history_controller

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._construir_header()
        self._construir_toolbar()
        self._construir_tabla()
        self._construir_footer()
        self._cargar_datos()

    # Construcción de la UI

    def _construir_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        ctk.CTkLabel(
            header, text="REGISTRO DE AUDITORÍA Y ACTIVIDAD DEL SISTEMA",
            font=font_title(), text_color=TXT_MAIN
        ).pack(side="left")

        # Indicador visual de que este módulo es de solo lectura
        ctk.CTkLabel(
            header, text="🔒 Solo lectura",
            font=font_small(), text_color=TXT_MUTED
        ).pack(side="right", padx=(0, 4))

    def _construir_toolbar(self):
        """
        Toolbar con dos filas:
          Fila 1: buscador + filtros de categoría (SegmentedButton)
          Fila 2: combo de ordenamiento
        """
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        # --- Fila 1: buscador y botón limpiar ---
        fila1 = ctk.CTkFrame(toolbar, fg_color="transparent")
        fila1.pack(fill="x", pady=(0, 8))

        self.ent_busqueda = ctk.CTkEntry(
            fila1,
            placeholder_text="🔍  Buscar en acción, referencia, responsable o detalles...",
            width=350, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_busqueda.pack(side="left", padx=(0, 12))
        self.ent_busqueda.bind("<KeyRelease>", lambda e: self._cargar_datos())

        ctk.CTkButton(
            fila1, text="Limpiar filtros",
            width=110, height=34,
            fg_color=("#CBD5E1", "#374151"), hover_color=("#94A3B8", "#4B5563"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._limpiar_filtros
        ).pack(side="left")

        # Contador de registros
        self.lbl_contador = ctk.CTkLabel(
            fila1, text="", font=font_small(), text_color=TXT_MUTED
        )
        self.lbl_contador.pack(side="right")

        # --- Fila 2: filtro por categoría (SegmentedButton) y orden ---
        fila2 = ctk.CTkFrame(toolbar, fg_color="transparent")
        fila2.pack(fill="x")

        self.seg_categoria = ctk.CTkSegmentedButton(
            fila2, values=CATEGORIAS,
            command=lambda _: self._cargar_datos(),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            height=34, corner_radius=6, border_width=2,
            selected_color=ACCENT_BLUE, selected_hover_color=ACCENT_HOVER,
            fg_color=BG_CARD, unselected_color=BG_CARD,
            unselected_hover_color=BORDER_INPUT, text_color=TXT_MAIN
        )
        self.seg_categoria.set("Todos")
        self.seg_categoria.pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            fila2, text="Ordenar por:", font=font_small(), text_color=TXT_MUTED
        ).pack(side="left", padx=(0, 6))

        self.combo_orden = ctk.CTkComboBox(
            fila2, values=ORDENES,
            width=180, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER,
            command=lambda _: self._cargar_datos()
        )
        self.combo_orden.set("Más Recientes")
        self.combo_orden.pack(side="left")

    def _construir_tabla(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.grid(row=2, column=0, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        self.scroll_y = ttk.Scrollbar(contenedor, orient="vertical")
        self.scroll_x = ttk.Scrollbar(contenedor, orient="horizontal")

        cols = ("id", "accion", "referencia", "responsable", "fecha", "detalles")
        self.tree = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)

        # Mismo ancho y centrado para todas las columnas (espaciado uniforme).
        ANCHO_COLUMNA = 189
        encabezados = {
            "id": "ID Log", "accion": "Tipo de acción",
            "referencia": "Activo / Ref.", "responsable": "Usuario ejecutivo",
            "fecha": "Fecha y hora", "detalles": "Detalles",
        }
        for col in cols:
            self.tree.heading(col, text=encabezados[col], anchor="center")
            self.tree.column(col, width=ANCHO_COLUMNA, anchor="center", stretch=True)

        # El historial es solo lectura: no hay doble clic para editar
        self.tree.bind("<Button-1>",  self._bloquear_resize)
        self.tree.bind("<B1-Motion>", self._bloquear_resize)

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
            footer, text="Exportar historial", width=145, height=BTN_H,
            fg_color=("#94A3B8", "#4B5563"), hover_color=("#64748B", "#374151"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._exportar
        ).pack(side="left")

        # Nota informativa al lado derecho del footer
        ctk.CTkLabel(
            footer,
            text="Los registros del historial no pueden ser modificados ni eliminados.",
            font=font_small(), text_color=TXT_MUTED
        ).pack(side="right")

    # Carga de datos

    def _cargar_datos(self):
        busqueda  = self.ent_busqueda.get().strip()
        categoria = self.seg_categoria.get()
        orden     = self.combo_orden.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        registros = self.ctrl.obtener_historial(busqueda, categoria, orden)

        for i, fila in enumerate(registros):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=fila, tags=(tag,))

        # Actualizar el contador de registros visibles
        n = len(registros)
        self.lbl_contador.configure(
            text=f"{n} registro{'s' if n != 1 else ''} encontrado{'s' if n != 1 else ''}"
        )

    def _limpiar_filtros(self):
        self.ent_busqueda.delete(0, tk.END)
        self.seg_categoria.set("Todos")
        self.combo_orden.set("Más Recientes")
        self._cargar_datos()

    # Exportación

    def _exportar(self):
        from views.asset_module import ExportarModal
        ExportarModal(self, self.tree, "Historial")

    # Helpers visuales

    def _bloquear_resize(self, event):
        if self.tree.identify_region(event.x, event.y) == "separator":
            return "break"

    def _aplicar_colores_filas(self):
        es_oscuro = ctk.get_appearance_mode() == "Dark"
        self.tree.tag_configure("par",   background=BG_DARK_CARD if es_oscuro else BG_LIGHT_CARD)
        self.tree.tag_configure("impar", background="#1E293B"     if es_oscuro else "#F1F5F9")

