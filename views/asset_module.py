
"""
views/asset_module.py
----------------------
Módulo visual de Inventario de Activos Tecnológicos.
Contiene la tabla principal, barra de búsqueda+filtro, botones de acción
y los modales de incorporación y edición de estado.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from datetime import datetime, timedelta

from views.theme import (
    BG_CARD, BG_INPUT, BORDER_INPUT, TXT_INPUT, TXT_PLACEHOLDER,
    TXT_MAIN, TXT_MUTED, ACCENT_BLUE, ACCENT_HOVER,
    BTN_RADIUS, INPUT_H, BTN_H, font_title, font_section, font_small, font_body,
    BG_DARK_CARD, BG_LIGHT_CARD, TXT_DARK_MAIN, TXT_LIGHT_MAIN
)


class AssetModule(ctk.CTkFrame):
    """Frame completo del módulo de equipos. Se monta en el área principal del Dashboard."""

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
            header, text="INVENTARIO DE ACTIVOS TECNOLÓGICOS",
            font=font_title(), text_color=TXT_MAIN
        ).pack(side="left")

        # Botón de tema (Light/Dark) en el extremo derecho del header
        self.btn_tema = ctk.CTkButton(
            header, text="🌙", width=38, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, border_width=1,
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._conmutar_tema
        )
        self.btn_tema.pack(side="right")

    def _construir_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        # Buscador
        self.ent_busqueda = ctk.CTkEntry(
            toolbar, placeholder_text="🔍  Buscar por nombre, serial, marca...",
            width=290, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT,
            text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
        )
        self.ent_busqueda.pack(side="left", padx=(0, 12))
        self.ent_busqueda.bind("<KeyRelease>", lambda e: self._cargar_datos())

        # Filtro por estado
        self.combo_filtro = ctk.CTkComboBox(
            toolbar,
            values=["ALL", "OPERATIVO", "MANTENIMIENTO", "ASIGNADO", "INACTIVO"],
            width=160, height=34,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER,
            command=lambda _: self._cargar_datos()
        )
        self.combo_filtro.set("ALL")
        self.combo_filtro.pack(side="left", padx=(0, 12))

        # Limpiar filtros
        ctk.CTkButton(
            toolbar, text="Limpiar filtros",
            width=110, height=34,
            fg_color=(("#CBD5E1", "#374151")), hover_color=("#94A3B8", "#4B5563"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._limpiar_filtros
        ).pack(side="left")

        # Importar CSV
        ctk.CTkButton(
            toolbar, text="Importar CSV",
            width=115, height=34,
            fg_color="#10B981", hover_color="#059669",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._importar_csv
        ).pack(side="right")

    def _construir_tabla(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.grid(row=2, column=0, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        self.scroll_y = ttk.Scrollbar(contenedor, orient="vertical")
        self.scroll_x = ttk.Scrollbar(contenedor, orient="horizontal")

        cols = ("id", "nombre", "marca", "modelo", "serial", "estado", "mantenimiento")
        self.tree = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)

        # Mismo ancho y centrado para todas las columnas (espaciado uniforme).
        ANCHO_COLUMNA = 231
        encabezados = {"id": "ID", "nombre": "Descripción del Activo",
                       "marca": "Fabricante", "modelo": "Modelo",
                       "serial": "Serial", "estado": "Estado",
                       "mantenimiento": "Próx. Revisión"}

        for col in cols:
            self.tree.heading(col, text=encabezados[col], anchor="center")
            self.tree.column(col, width=ANCHO_COLUMNA, anchor="center", stretch=True)

        # Bloquear redimensión de columnas con el mouse
        self.tree.bind("<Button-1>",   self._bloquear_resize)
        self.tree.bind("<B1-Motion>",  self._bloquear_resize)
        self.tree.bind("<Double-1>",   lambda e: self._abrir_editar_estado())

        # PARCHE QA: el árbol y las dos barras de desplazamiento se ubican
        # con grid() de forma consistente. Antes solo el árbol usaba pack()
        # y ninguna barra llegaba a mostrarse, por lo que columnas que no
        # entraban en el ancho visible (Estado, Próx. Revisión) quedaban
        # inaccesibles sin ninguna forma de desplazarse hasta ellas.
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
            footer, text="Exportar datos", width=120, height=BTN_H,
            fg_color=("#94A3B8", "#4B5563"), hover_color=("#64748B", "#374151"),
            text_color=TXT_MAIN, corner_radius=BTN_RADIUS,
            command=self._exportar
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="Alterar estado", width=130, height=BTN_H,
            fg_color="#D97706", hover_color="#B45309",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._abrir_editar_estado
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="Remover activo", width=130, height=BTN_H,
            fg_color="#DC2626", hover_color="#B91C1C",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._eliminar
        ).pack(side="left")

        ctk.CTkButton(
            footer, text="+ Incorporar nuevo activo", width=180, height=BTN_H,
            font=font_section(),
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._abrir_incorporar
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Carga y filtrado de datos
    # ------------------------------------------------------------------

    def _cargar_datos(self):
        busqueda = self.ent_busqueda.get().strip()
        filtro   = self.combo_filtro.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for i, fila in enumerate(self.ctrl.obtener_activos(busqueda, filtro)):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=fila, tags=(tag,))

    def _limpiar_filtros(self):
        self.ent_busqueda.delete(0, tk.END)
        self.combo_filtro.set("ALL")
        self._cargar_datos()

    # ------------------------------------------------------------------
    # Acciones de los botones
    # ------------------------------------------------------------------

    def _abrir_incorporar(self):
        IncorporarActivoModal(self, self.ctrl, self._cargar_datos)

    def _abrir_editar_estado(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Atención", "Selecciona un activo de la tabla primero.", parent=self)
            return
        valores = self.tree.item(seleccion[0])["values"]
        EditarEstadoModal(self, self.ctrl, valores[0], valores[5], self._cargar_datos)

    def _eliminar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Atención", "Selecciona un activo de la tabla primero.", parent=self)
            return

        valores = self.tree.item(seleccion[0])["values"]
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el activo '{valores[1]}' (Serial: {valores[4]}) del inventario?\n\n"
            "Esta acción es irreversible.",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.eliminar_activo(valores[0])
        if exito:
            messagebox.showinfo("Eliminado", msg, parent=self)
            self._cargar_datos()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _importar_csv(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo CSV",
            filetypes=[("Archivos CSV", "*.csv")],
            parent=self
        )
        if not filepath:
            return
        exito, msg = self.ctrl.importar_desde_csv(filepath)
        if exito:
            messagebox.showinfo("Importación completada", msg, parent=self)
            self._cargar_datos()
        else:
            messagebox.showerror("Error al importar", msg, parent=self)

    def _exportar(self):
        ExportarModal(self, self.tree, "Equipos")

    # ------------------------------------------------------------------
    # Helpers visuales
    # ------------------------------------------------------------------

    def _bloquear_resize(self, event):
        if self.tree.identify_region(event.x, event.y) == "separator":
            return "break"

    def _aplicar_colores_filas(self):
        es_oscuro = ctk.get_appearance_mode() == "Dark"
        self.tree.tag_configure("par",   background=BG_DARK_CARD  if es_oscuro else BG_LIGHT_CARD)
        self.tree.tag_configure("impar", background="#1E293B"      if es_oscuro else "#F1F5F9")

    def _conmutar_tema(self):
        # El dashboard expone el método; lo buscamos subiendo por el árbol de widgets
        dashboard = self.winfo_toplevel()
        if hasattr(dashboard, "conmutar_tema"):
            nuevo = dashboard.conmutar_tema()
            self.btn_tema.configure(text="☀️" if nuevo == "Dark" else "🌙")
            self._aplicar_colores_filas()
            self._cargar_datos()


# ------------------------------------------------------------------
# Modal: Incorporar nuevo activo
# ------------------------------------------------------------------

class IncorporarActivoModal(ctk.CTkToplevel):

    def __init__(self, parent, controller, on_saved):
        super().__init__(parent)
        self.ctrl     = controller
        self.on_saved = on_saved

        self.title("Incorporar nuevo activo")
        self.geometry("460x560")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()

        self._construir_ui()

    def _construir_ui(self):
        ctk.CTkLabel(
            self, text="REGISTRO TÉCNICO DE ACTIVO",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(20, 5))

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=22, pady=(0, 10))

        def entrada(placeholder):
            e = ctk.CTkEntry(
                scroll, placeholder_text=placeholder,
                width=390, height=INPUT_H,
                fg_color=BG_INPUT, border_color=BORDER_INPUT,
                text_color=TXT_INPUT, placeholder_text_color=TXT_PLACEHOLDER
            )
            e.pack(pady=6)
            return e

        ctk.CTkLabel(scroll, text="ESPECIFICACIONES", font=font_small(),
                     text_color=ACCENT_BLUE).pack(anchor="w", pady=(8, 2))

        self.ent_nombre = entrada("Tipo de activo (ej: Osciloscopio, Servidor)")
        self.ent_marca  = entrada("Fabricante / Marca")
        self.ent_modelo = entrada("Modelo de fábrica")
        self.ent_serial = entrada("Número de serial único")

        # Estado inicial: siempre OPERATIVO. No se expone como campo editable
        # porque CTkComboBox disabled no preserva el valor al llamar .get().
        # El valor "OPERATIVO" se inyecta directamente en _guardar().
        # PARCHE QA: se elimina el recuadro vacío decorativo que simulaba
        # un campo deshabilitado sin contener ningún widget real; el texto
        # informativo ya comunica la regla de negocio por sí solo.
        ctk.CTkLabel(
            scroll,
            text="Estado inicial: OPERATIVO  (solo modificable desde el inventario)",
            font=ctk.CTkFont(size=11), text_color=TXT_MUTED
        ).pack(anchor="w", pady=(10, 4))

        ctk.CTkLabel(scroll, text="LOGÍSTICA", font=font_small(),
                     text_color=ACCENT_BLUE).pack(anchor="w", pady=(14, 2))

        ctk.CTkLabel(
            scroll, text="Fecha de próxima revisión (DD/MM/AAAA):",
            font=font_small(), text_color=TXT_MUTED
        ).pack(anchor="w", pady=(4, 2))

        # Campo siempre habilitado: CTkEntry disabled no devuelve valor con .get()
        self.ent_fecha = ctk.CTkEntry(
            scroll, width=390, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT
        )
        self.ent_fecha.pack(pady=(0, 6))
        self.ent_fecha.insert(0, (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y"))
        self.ent_fecha.bind("<KeyRelease>", self._autocompletar_fecha)

        ctk.CTkButton(
            scroll, text="Completar incorporación",
            font=font_section(), height=42, width=390,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._guardar
        ).pack(pady=(20, 15))

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
        datos = {
            "nombre":        self.ent_nombre.get().strip(),
            "marca":         self.ent_marca.get().strip(),
            "modelo":        self.ent_modelo.get().strip(),
            "serial":        self.ent_serial.get().strip(),
            "estado":        "OPERATIVO",
            "mantenimiento": self.ent_fecha.get().strip(),
        }

        confirmar = messagebox.askyesno(
            "Confirmar incorporación",
            f"¿Registrar el activo '{datos['nombre'].upper()}' en el inventario?",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.incorporar_activo(datos)

        if exito:
            messagebox.showinfo("Incorporación exitosa",
                                "El activo fue registrado en el inventario.", parent=self)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error de validación", msg, parent=self)


# ------------------------------------------------------------------
# Modal: Editar estado de un activo
# ------------------------------------------------------------------

class EditarEstadoModal(ctk.CTkToplevel):

    def __init__(self, parent, controller, id_activo, estado_actual, on_saved):
        super().__init__(parent)
        self.ctrl      = controller
        self.id_activo = id_activo
        self.on_saved  = on_saved

        self.title(f"Editar estado — ID {id_activo}")
        self.geometry("340x210")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()

        ctk.CTkLabel(
            self, text=f"Modificar estado (ID: {id_activo})",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(24, 12))

        self.combo = ctk.CTkComboBox(
            self,
            values=["OPERATIVO", "MANTENIMIENTO", "ASIGNADO", "INACTIVO"],
            width=240, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER
        )
        self.combo.set(estado_actual)
        self.combo.pack(pady=8)

        ctk.CTkButton(
            self, text="Actualizar estado",
            font=font_section(), height=BTN_H, width=240,
            fg_color="#10B981", hover_color="#059669",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._guardar
        ).pack(pady=16)

    def _guardar(self):
        nuevo_estado = self.combo.get()
        confirmar = messagebox.askyesno(
            "Confirmar cambio",
            f"¿Cambiar el estado a '{nuevo_estado}'?",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.cambiar_estado(self.id_activo, nuevo_estado)
        if exito:
            messagebox.showinfo("Estado actualizado", msg, parent=self)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error", msg, parent=self)


# ------------------------------------------------------------------
# Modal: Exportar datos de la tabla activa
# ------------------------------------------------------------------

class ExportarModal(ctk.CTkToplevel):
    """Modal de exportación reutilizable por todos los módulos."""

    def __init__(self, parent, tree: ttk.Treeview, nombre_modulo: str):
        super().__init__(parent)
        self.tree          = tree
        self.nombre_modulo = nombre_modulo

        self.title("Exportar datos")
        self.geometry("360x230")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()

        ctk.CTkLabel(
            self, text=f"EXPORTAR: {nombre_modulo.upper()}",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(22, 6))

        ctk.CTkLabel(
            self, text="Selecciona el formato de exportación.",
            font=font_small(), text_color=TXT_MUTED
        ).pack(pady=(0, 14))

        self.combo_fmt = ctk.CTkComboBox(
            self,
            values=["Excel (.csv)", "Texto plano (.txt)", "Reporte web (.html)"],
            width=280, height=INPUT_H,
            fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT,
            button_color=BG_INPUT, button_hover_color=ACCENT_HOVER
        )
        self.combo_fmt.pack(pady=6)

        ctk.CTkButton(
            self, text="Generar archivo",
            font=font_section(), width=280, height=BTN_H,
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._exportar
        ).pack(pady=14)

    def _exportar(self):
        import csv, os
        from datetime import datetime

        filas    = [self.tree.item(i)["values"] for i in self.tree.get_children()]
        columnas = [self.tree.heading(c)["text"] for c in self.tree["columns"]]

        if not filas:
            messagebox.showwarning("Sin datos", "La tabla no tiene datos para exportar.", parent=self)
            return

        fmt = self.combo_fmt.get()

        if "csv" in fmt:
            path = filedialog.asksaveasfilename(
                defaultextension=".csv", filetypes=[("CSV", "*.csv")], parent=self)
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f, delimiter=";")
                w.writerow(columnas)
                w.writerows(filas)

        elif "txt" in fmt:
            path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("Texto", "*.txt")], parent=self)
            if not path:
                return
            with open(path, "w", encoding="utf-8") as f:
                f.write(" | ".join(columnas) + "\n" + "-" * 100 + "\n")
                for fila in filas:
                    f.write(" | ".join(str(v) for v in fila) + "\n")

        elif "html" in fmt:
            path = filedialog.asksaveasfilename(
                defaultextension=".html", filetypes=[("HTML", "*.html")], parent=self)
            if not path:
                return
            filas_html = "".join(
                "<tr>" + "".join(f"<td>{v}</td>" for v in fila) + "</tr>" for fila in filas
            )
            encabezado_html = "".join(f"<th>{c}</th>" for c in columnas)
            html = (
                f"<html><head><meta charset='utf-8'>"
                f"<title>Reporte {self.nombre_modulo}</title>"
                f"<style>body{{font-family:Arial;margin:40px}}"
                f"table{{width:100%;border-collapse:collapse;margin-top:20px}}"
                f"th,td{{border:1px solid #ddd;padding:10px;text-align:left}}"
                f"th{{background:#0B0F19;color:white}}"
                f"tr:nth-child(even){{background:#f2f2f2}}"
                f"h2{{color:#2563EB}}"
                f"@media print{{button{{display:none}}}}</style></head><body>"
                f"<h2>REPORTE: {self.nombre_modulo.upper()}</h2>"
                f"<p>Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>"
                f"<table><tr>{encabezado_html}</tr>{filas_html}</table>"
                f"<br><button onclick='window.print()' style='padding:12px 24px;"
                f"font-size:16px;background:#10B981;color:white;border:none;"
                f"border-radius:5px;cursor:pointer'>Guardar como PDF</button>"
                f"</body></html>"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            os.startfile(path)

        messagebox.showinfo("Exportación exitosa", f"Archivo guardado en:\n{path}", parent=self)
        self.destroy()
