
"""
views/loan_module.py
---------------------
Módulo visual de Trazabilidad de Préstamos.
Muestra todos los préstamos activos e históricos, permite modificar
fechas/estado y eliminar registros con confirmación previa.

Autores: Equipo de Ingeniería Informática - 4to Semestre
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


class LoanModule(ctk.CTkFrame):
    """Frame del módulo de préstamos. Montado en el área principal del Dashboard."""

    def __init__(self, parent, loan_controller, auth_controller):
        super().__init__(parent, fg_color="transparent")
        self.ctrl = loan_controller
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
            header, text="TRAZABILIDAD LOGÍSTICA DE PRÉSTAMOS",
            font=font_title(), text_color=TXT_MAIN
        ).pack(side="left")

    def _construir_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        # El buscador ahora filtra también por fecha y serial (reparado)
        self.ent_busqueda = ctk.CTkEntry(
            toolbar,
            placeholder_text="🔍  Buscar por equipo, serial, prestatario, fecha...",
            width=320, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_busqueda.pack(side="left", padx=(0, 12))
        self.ent_busqueda.bind("<KeyRelease>", lambda e: self._cargar_datos())

        self.combo_filtro = ctk.CTkComboBox(
            toolbar, values=["ALL", "ASIGNADOS", "EN DEVOLUCIÓN", "DEVUELTO"],
            width=160, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER,
            command=lambda _: self._cargar_datos()
        )
        self.combo_filtro.set("ALL")
        self.combo_filtro.pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            toolbar, text="Limpiar filtros",
            width=110, height=34,
            fg_color=("#CBD5E1", "#374151"), hover_color=("#94A3B8", "#4B5563"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._limpiar_filtros
        ).pack(side="left")

    def _construir_tabla(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.grid(row=2, column=0, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        self.scroll_y = ttk.Scrollbar(contenedor, orient="vertical")
        self.scroll_x = ttk.Scrollbar(contenedor, orient="horizontal")

        cols = ("id", "equipo", "serial", "prestatario", "fecha_p", "fecha_d", "estado", "ubicacion")
        self.tree = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)

        # Mismo ancho y centrado para todas las columnas (espaciado uniforme).
        ANCHO_COLUMNA = 191
        encabezados = {
            "id": "ID", "equipo": "Equipo", "serial": "Serial",
            "prestatario": "Prestatario", "fecha_p": "Fecha Préstamo",
            "fecha_d": "Fecha Devolución", "estado": "Estado",
            "ubicacion": "Ubicación",
        }
        for col in cols:
            self.tree.heading(col, text=encabezados[col], anchor="center")
            self.tree.column(col, width=ANCHO_COLUMNA, anchor="center", stretch=True)

        self.tree.bind("<Button-1>",  self._bloquear_resize)
        self.tree.bind("<B1-Motion>", self._bloquear_resize)
        self.tree.bind("<Double-1>",  lambda e: self._abrir_modificar())

        # PARCHE QA: el árbol y las dos barras de desplazamiento se ubican
        # con grid() de forma consistente. Antes solo el árbol usaba pack()
        # y ninguna barra llegaba a mostrarse, por lo que las columnas que
        # no entraban en el ancho visible (Estado, Ubicación) quedaban
        # inaccesibles sin ninguna forma de desplazarse hasta ellas.
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="ew")

        self._aplicar_colores_filas()

    def _construir_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", pady=(16, 0))

        ctk.CTkButton(
            footer, text="Sincronizar", width=100, height=BTN_H,
            fg_color=("#CBD5E1", "#4B5563"), hover_color=("#94A3B8", "#374151"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._cargar_datos
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="Exportar datos", width=120, height=BTN_H,
            fg_color=("#94A3B8", "#4B5563"), hover_color=("#64748B", "#374151"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._exportar
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="✔ Devolver equipo", width=140, height=BTN_H,
            font=font_section(),
            fg_color="#10B981", hover_color="#059669",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._procesar_devolucion
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="Modificar préstamo", width=145, height=BTN_H,
            fg_color="#D97706", hover_color="#B45309",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._abrir_modificar
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="Eliminar préstamo", width=145, height=BTN_H,
            fg_color="#DC2626", hover_color="#B91C1C",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._eliminar
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def _cargar_datos(self):
        busqueda = self.ent_busqueda.get().strip()
        filtro   = self.combo_filtro.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, fila in enumerate(self.ctrl.obtener_prestamos(busqueda, filtro)):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=fila, tags=(tag,))

    def _limpiar_filtros(self):
        self.ent_busqueda.delete(0, tk.END)
        self.combo_filtro.set("ALL")
        self._cargar_datos()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _procesar_devolucion(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Atención", "Selecciona un préstamo de la tabla primero.", parent=self)
            return

        valores = self.tree.item(seleccion[0])["values"]
        estado_actual = str(valores[6]).upper()

        if estado_actual == "DEVUELTO":
            messagebox.showinfo("Ya devuelto", "Este préstamo ya fue marcado como devuelto.", parent=self)
            return

        confirmar = messagebox.askyesno(
            "Confirmar devolución",
            f"¿Registrar la devolución del equipo '{valores[1]}'?\n\n"
            f"• El préstamo quedará marcado como DEVUELTO.\n"
            f"• El equipo volverá al estado OPERATIVO automáticamente.",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.procesar_devolucion(valores[0])
        if exito:
            messagebox.showinfo("Devolución registrada", msg, parent=self)
            self._cargar_datos()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _abrir_modificar(self):
        # PARCHE QA: solo Operadores de Laboratorio o Administradores pueden
        # modificar fecha/estado de un préstamo.
        if not self.auth.es_operador():
            messagebox.showerror(
                "Permiso denegado",
                "Tu rol no tiene permiso para modificar préstamos.\n"
                "Esta acción está reservada a Operadores de Laboratorio "
                "y Administradores.",
                parent=self
            )
            return

        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Atención", "Selecciona un préstamo de la tabla primero.", parent=self)
            return
        valores = self.tree.item(seleccion[0])["values"]
        ModificarPrestamoModal(self, self.ctrl, valores, self._cargar_datos)

    def _eliminar(self):
        # PARCHE QA: solo Operadores de Laboratorio o Administradores pueden
        # eliminar préstamos. Un Propietario no debe poder hacerlo.
        if not self.auth.es_operador():
            messagebox.showerror(
                "Permiso denegado",
                "Tu rol no tiene permiso para eliminar préstamos.\n"
                "Esta acción está reservada a Operadores de Laboratorio "
                "y Administradores.",
                parent=self
            )
            return

        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Atención", "Selecciona un préstamo de la tabla primero.", parent=self)
            return

        valores = self.tree.item(seleccion[0])["values"]
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el registro del préstamo de '{valores[1]}' a '{valores[3]}'?\n\n"
            "Esta acción es irreversible.",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.eliminar_prestamo(valores[0])
        if exito:
            messagebox.showinfo("Eliminado", msg, parent=self)
            self._cargar_datos()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _exportar(self):
        from views.asset_module import ExportarModal
        ExportarModal(self, self.tree, "Préstamos")

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
# Modal: Modificar un préstamo existente
# ------------------------------------------------------------------

class ModificarPrestamoModal(ctk.CTkToplevel):

    def __init__(self, parent, controller, datos_prestamo, on_saved):
        super().__init__(parent)
        self.ctrl        = controller
        self.on_saved    = on_saved
        self.id_prestamo = datos_prestamo[0]

        self.title(f"Modificar préstamo — ID {self.id_prestamo}")
        self.geometry("420x340")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()

        ctk.CTkLabel(
            self, text=f"MODIFICAR PRÉSTAMO (ID: {self.id_prestamo})",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(22, 8))

        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=22, pady=5)

        ctk.CTkLabel(
            frame,
            text=f"Equipo: {datos_prestamo[1]}  |  Prestatario: {datos_prestamo[3]}",
            font=font_small(), text_color=ACCENT_BLUE
        ).pack(anchor="w", pady=(0, 14))

        # Fecha de devolución con autocompletado
        ctk.CTkLabel(frame, text="Nueva fecha de devolución:",
                     font=font_small(), text_color=TXT_MUTED).pack(anchor="w")
        self.ent_fecha = ctk.CTkEntry(
            frame, width=360, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT
        )
        self.ent_fecha.pack(pady=(3, 14))
        self.ent_fecha.insert(0, datos_prestamo[5])
        self.ent_fecha.bind("<KeyRelease>", self._autocompletar_fecha)

        ctk.CTkLabel(frame, text="Estado del préstamo:",
                     font=font_small(), text_color=TXT_MUTED).pack(anchor="w")
        self.combo_estado = ctk.CTkComboBox(
            frame, values=["ASIGNADOS", "EN DEVOLUCIÓN"],
            width=360, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER
        )
        estado_actual = datos_prestamo[6] if datos_prestamo[6] in ["ASIGNADOS", "EN DEVOLUCIÓN"] else "ASIGNADOS"
        self.combo_estado.set(estado_actual)
        self.combo_estado.pack(pady=(3, 20))

        ctk.CTkButton(
            self, text="Guardar cambios",
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
            "Confirmar modificación",
            f"¿Actualizar el préstamo ID {self.id_prestamo}?\n\n"
            f"Nueva devolución: {nueva_fecha}\nEstado: {nuevo_estado}",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.modificar_prestamo(
            self.id_prestamo, nueva_fecha, nuevo_estado
        )
        if exito:
            messagebox.showinfo("Actualizado", msg, parent=self)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)

