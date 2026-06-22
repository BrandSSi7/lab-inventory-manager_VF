
"""
views/user_module.py
---------------------
Módulo visual de Control de Personal Autorizado.
Permite ver, registrar, editar y eliminar usuarios del sistema.

El modal de edición usa CTkScrollableFrame para garantizar que los botones
de 'Guardar' y 'Resetear Clave' sean siempre visibles, incluso en laptops
con pantallas de 768px de alto.

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


class UserModule(ctk.CTkFrame):
    """Frame del módulo de usuarios. Montado en el área principal del Dashboard."""

    def __init__(self, parent, user_controller, auth_controller):
        super().__init__(parent, fg_color="transparent")
        self.ctrl = user_controller
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
            header, text="CONTROL DE PERSONAL AUTORIZADO",
            font=font_title(), text_color=TXT_MAIN
        ).pack(side="left")

    def _construir_toolbar(self):
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        self.ent_busqueda = ctk.CTkEntry(
            toolbar,
            placeholder_text="🔍  Buscar por nombre, cédula, correo, usuario...",
            width=320, height=34,
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

    def _construir_tabla(self):
        contenedor = ctk.CTkFrame(self, fg_color="transparent")
        contenedor.grid(row=2, column=0, sticky="nsew")
        contenedor.grid_columnconfigure(0, weight=1)
        contenedor.grid_rowconfigure(0, weight=1)

        self.scroll_y = ttk.Scrollbar(contenedor, orient="vertical")
        self.scroll_x = ttk.Scrollbar(contenedor, orient="horizontal")

        cols = ("id", "nombres", "cedula", "fecha_nac", "correo", "telefono", "username", "rol")
        self.tree = ttk.Treeview(
            contenedor, columns=cols, show="headings",
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set
        )
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)

        config = {
            "id":       ("ID",              50,  False),
            "nombres":  ("Personal",       200,  True),
            "cedula":   ("Identificación", 120,  True),
            "fecha_nac":("F. Nacimiento",  110,  False),
            "correo":   ("Correo",         200,  True),
            "telefono": ("Contacto",       120,  True),
            "username": ("Usuario",        110,  False),
            "rol":      ("Rol del sistema",170,  True),
        }
        for col, (texto, ancho, stretch) in config.items():
            self.tree.heading(col, text=texto, anchor="w")
            self.tree.column(col, width=ancho, anchor="w", stretch=stretch)

        self.tree.bind("<Button-1>",  self._bloquear_resize)
        self.tree.bind("<B1-Motion>", self._bloquear_resize)
        self.tree.bind("<Double-1>",  lambda e: self._abrir_editar())

        self.tree.pack(side="left", fill="both", expand=True)
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
            footer, text="Modificar perfil", width=130, height=BTN_H,
            fg_color="#D97706", hover_color="#B45309",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._abrir_editar
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            footer, text="Remover usuario", width=130, height=BTN_H,
            fg_color="#DC2626", hover_color="#B91C1C",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._eliminar
        ).pack(side="left")

        ctk.CTkButton(
            footer, text="+ Dar de alta operador", width=180, height=BTN_H,
            font=font_section(),
            fg_color=ACCENT_BLUE, hover_color=ACCENT_HOVER,
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._abrir_registro
        ).pack(side="right")

    # ------------------------------------------------------------------
    # Carga de datos
    # ------------------------------------------------------------------

    def _cargar_datos(self):
        busqueda = self.ent_busqueda.get().strip()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, fila in enumerate(self.ctrl.obtener_usuarios(busqueda)):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=fila, tags=(tag,))

    def _limpiar_filtros(self):
        self.ent_busqueda.delete(0, tk.END)
        self._cargar_datos()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _abrir_registro(self):
        from views.register_user_view import RegisterUserModal
        RegisterUserModal(self, self.auth, on_saved=self._cargar_datos)

    def _abrir_editar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Atención", "Selecciona un usuario de la tabla primero.", parent=self)
            return
        valores = self.tree.item(seleccion[0])["values"]
        EditarUsuarioModal(self, self.ctrl, self.auth, valores, self._cargar_datos)

    def _eliminar(self):
        seleccion = self.tree.selection()
        if not seleccion:
            messagebox.showinfo("Atención", "Selecciona un usuario de la tabla primero.", parent=self)
            return

        valores = self.tree.item(seleccion[0])["values"]
        confirmar = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el usuario '{valores[1]}' (Login: {valores[6]})?\n\n"
            "Se revocarán todos sus accesos al sistema. Esta acción es irreversible.",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.eliminar_usuario(valores[0])
        if exito:
            messagebox.showinfo("Usuario eliminado", msg, parent=self)
            self._cargar_datos()
        else:
            messagebox.showerror("Error", msg, parent=self)

    def _exportar(self):
        from views.asset_module import ExportarModal
        ExportarModal(self, self.tree, "Usuarios")

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
# Modal: Editar perfil de usuario
# ------------------------------------------------------------------

class EditarUsuarioModal(ctk.CTkToplevel):
    """
    Modal de edición de perfil. Usa CTkScrollableFrame para que los botones
    de acción sean visibles en cualquier resolución de pantalla.
    """

    def __init__(self, parent, user_controller, auth_controller, datos_usuario, on_saved):
        super().__init__(parent)
        self.ctrl       = user_controller
        self.auth       = auth_controller
        self.on_saved   = on_saved
        self.id_usuario = datos_usuario[0]
        # Guardamos el rol original para devolverlo intacto si el editor no es admin
        self.rol_original = str(datos_usuario[7]) if len(datos_usuario) > 7 else "PRESTATARIO EXTERNO"

        self.title(f"Editar perfil — ID {self.id_usuario}")
        self.geometry("430x680")
        self.resizable(False, False)
        self.configure(fg_color=BG_CARD)
        self.grab_set()

        self._construir_ui(datos_usuario)

    def _construir_ui(self, datos):
        ctk.CTkLabel(
            self, text=f"EDICIÓN DE PERFIL (ID: {self.id_usuario})",
            font=font_section(), text_color=TXT_MAIN
        ).pack(pady=(20, 5))

        # ScrollableFrame: garantiza que los botones del footer siempre sean visibles
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        def campo(label, valor_inicial):
            ctk.CTkLabel(scroll, text=label, font=font_small(),
                         text_color=TXT_MUTED).pack(anchor="w", pady=(10, 2))
            e = ctk.CTkEntry(
                scroll, width=370, height=INPUT_H,
                fg_color=BG_INPUT, border_color=BORDER_INPUT, text_color=TXT_INPUT
            )
            e.pack()
            e.insert(0, valor_inicial)
            return e

        self.ent_nombre   = campo("Nombre y apellido:", datos[1])
        self.ent_cedula   = campo("Identificación (Cédula/ID):", datos[2])
        self.ent_fnac     = campo("Fecha de nacimiento:", datos[3])
        self.ent_fnac.bind("<KeyRelease>", self._autocompletar_fecha)
        self.ent_correo   = campo("Correo electrónico:", datos[4])
        self.ent_telefono = campo("Número de contacto:", datos[5])

        # Sección de roles
        es_admin = self.auth.es_administrador()

        ctk.CTkLabel(
            scroll, text="ROLES Y PERMISOS DEL SISTEMA",
            font=font_small(), text_color=ACCENT_BLUE
        ).pack(anchor="w", pady=(20, 8))

        # Los checkboxes de rol solo son editables para Administradores Ejecutivos.
        # Para cualquier otro rol, se muestran como referencia pero bloqueados.
        estado_chk = "normal" if es_admin else "disabled"

        self.chk_admin = ctk.CTkCheckBox(
            scroll, text="Administrador Ejecutivo",
            fg_color=ACCENT_BLUE, text_color=TXT_MAIN,
            state=estado_chk
        )
        self.chk_operador = ctk.CTkCheckBox(
            scroll, text="Operador de Laboratorio",
            fg_color=ACCENT_BLUE, text_color=TXT_MAIN,
            state=estado_chk
        )
        self.chk_prestatario = ctk.CTkCheckBox(
            scroll, text="Prestatario Externo",
            fg_color=ACCENT_BLUE, text_color=TXT_MAIN,
            state=estado_chk
        )

        for chk in (self.chk_admin, self.chk_operador, self.chk_prestatario):
            chk.pack(anchor="w", padx=10, pady=5)

        # Nota visible para usuarios sin permisos de administración
        if not es_admin:
            ctk.CTkLabel(
                scroll,
                text="🔒 Solo un Administrador puede modificar roles del sistema.",
                font=ctk.CTkFont(size=10), text_color="#EF4444"
            ).pack(anchor="w", padx=10, pady=(0, 4))

        # Marcar el rol actual
        rol_actual = str(datos[7]).upper() if len(datos) > 7 else ""
        if "ADMINISTRADOR" in rol_actual:
            self.chk_admin.select()
        if "OPERADOR" in rol_actual:
            self.chk_operador.select()
        if "PRESTATARIO" in rol_actual:
            self.chk_prestatario.select()

        # Botones de acción (dentro del scroll = siempre visibles)
        ctk.CTkButton(
            scroll, text="Guardar modificaciones",
            font=font_section(), height=42, width=370,
            fg_color="#10B981", hover_color="#059669",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._guardar
        ).pack(pady=(22, 8))

        # El botón de reset solo aparece para administradores
        if self.auth.es_administrador():
            ctk.CTkButton(
                scroll, text="Resetear contraseña",
                font=font_section(), height=BTN_H, width=370,
                fg_color="#EF4444", hover_color="#B91C1C",
                text_color="white", corner_radius=BTN_RADIUS,
                command=self._resetear_password
            ).pack(pady=(0, 16))

    def _autocompletar_fecha(self, event):
        if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Tab"):
            return
        texto = "".join(c for c in self.ent_fnac.get() if c.isdigit())[:8]
        formateado = ""
        for i, c in enumerate(texto):
            if i in (2, 4):
                formateado += "/"
            formateado += c
        self.ent_fnac.delete(0, tk.END)
        self.ent_fnac.insert(0, formateado)

    def _construir_rol_final(self) -> str:
        """
        Construye el string de rol a guardar.

        Si el usuario activo NO es administrador, devuelve el rol original
        almacenado al abrir el modal. Esto ignora completamente el estado
        de los checkboxes, que pueden estar pre-marcados aunque bloqueados
        (bug de CTkCheckBox: .get() devuelve 1 aunque state='disabled').

        Solo si el usuario activo ES administrador se leen los checkboxes.
        """
        if not self.auth.es_administrador():
            return self.rol_original

        roles = []
        if self.chk_admin.get():
            roles.append("ADMINISTRADOR EJECUTIVO")
        if self.chk_operador.get():
            roles.append("OPERADOR DE LABORATORIO")
        if self.chk_prestatario.get():
            roles.append("PRESTATARIO EXTERNO")
        return " / ".join(roles) if roles else "SIN ACCESO"

    def _guardar(self):
        datos = {
            "nombres":   self.ent_nombre.get().strip(),
            "cedula":    self.ent_cedula.get().strip(),
            "fecha_nac": self.ent_fnac.get().strip(),
            "correo":    self.ent_correo.get().strip(),
            "telefono":  self.ent_telefono.get().strip(),
            "rol":       self._construir_rol_final(),
        }

        # Defensa en profundidad — capa Vista: validar formato de identificación
        # antes de abrir el diálogo de confirmación para no interrumpir un flujo
        # ya confirmado con un error que pudo detectarse antes.
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

        confirmar = messagebox.askyesno(
            "Confirmar cambios",
            f"¿Guardar los cambios en el perfil de '{datos['nombres']}'?",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.actualizar_usuario(self.id_usuario, datos)
        if exito:
            messagebox.showinfo("Perfil actualizado",
                                "Los datos del usuario fueron guardados correctamente.",
                                parent=self)
            self.on_saved()
            self.destroy()
        else:
            messagebox.showerror("Error de validación", msg, parent=self)

    def _resetear_password(self):
        dialog = ctk.CTkInputDialog(
            text="Ingresa la contraseña temporal que le asignarás al usuario:",
            title="Resetear contraseña"
        )
        temp_pwd = dialog.get_input()
        if not temp_pwd:
            return

        confirmar = messagebox.askyesno(
            "Confirmar reset",
            f"¿Resetear la contraseña del usuario?\nDeberá cambiarla en su próximo inicio de sesión.",
            parent=self
        )
        if not confirmar:
            return

        exito, msg = self.ctrl.resetear_password_usuario(self.id_usuario, temp_pwd)
        if exito:
            messagebox.showinfo("Reset exitoso", msg, parent=self)
        else:
            messagebox.showerror("Error", msg, parent=self)

