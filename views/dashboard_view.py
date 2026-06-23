
"""
views/dashboard_view.py
------------------------
Ventana principal del sistema (Dashboard). Construye la estructura
con menú lateral (sidebar) y un área de contenido central intercambiable.

Esta vista NO contiene ningún módulo directamente: actúa como contenedor
y enruta la navegación a cada módulo visual según el botón pulsado.

Los módulos internos (activos, préstamos, usuarios, historial) se importan
de forma diferida para mantener los tiempos de carga bajos.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

from tkinter import messagebox
import customtkinter as ctk
from tkinter.ttk import Style   # Solo para el estilo de los Treeview

from controllers.asset_controller   import AssetController
from controllers.loan_controller    import LoanController
from controllers.user_controller    import UserController
from controllers.history_controller import HistoryController

from views.theme import (
    BG_MAIN, BG_CARD, BORDER_INPUT, TXT_MAIN, TXT_MUTED,
    ACCENT_BLUE, ACCENT_HOVER, BTN_RADIUS,
    BG_DARK_CARD, BG_LIGHT_CARD, TXT_DARK_MAIN, TXT_LIGHT_MAIN,
    font_title, font_section, font_small
)


# Definición del menú lateral: (id_módulo, emoji, etiqueta, método)
MENU_ITEMS = [
    ("equipos",   "💻", "Equipos"),
    ("prestamos", "🤝", "Préstamos"),
    ("asignacion","➕", "Asignación"),
    ("alarmas",   "⏰", "Alarmas"),
    ("usuarios",  "👥", "Usuarios"),
    ("historial", "📜", "Historial"),
]


class DashboardView(ctk.CTk):
    """
    Ventana raíz del panel de control. Instancia todos los controladores
    y aloja los módulos de vista en un frame central intercambiable.
    """

    def __init__(self, auth_controller, on_logout):
        super().__init__()
        self.auth      = auth_controller
        self.on_logout = on_logout

        # Instanciar controladores una sola vez y compartirlos con los módulos
        self.asset_ctrl   = AssetController(auth_controller)
        self.loan_ctrl    = LoanController(auth_controller)
        self.user_ctrl    = UserController(auth_controller)
        self.history_ctrl = HistoryController(auth_controller)

        self.modulo_activo = ""       # ID del módulo que se muestra ahora
        self._frame_modulo = None     # Referencia al frame del módulo actual

        self.title(f"Xorte — Panel de Control  |  {auth_controller.usuario_actual}")
        self.geometry("1300x780")
        self.configure(fg_color=BG_MAIN)

        # Grid: columna 0 = sidebar fija, columna 1 = contenido flexible
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._construir_sidebar()
        self._construir_area_principal()
        self._configurar_estilo_treeview()

        # Abrir por defecto el primer módulo permitido para el rol activo
        # PARCHE QA: antes navegaba siempre a "equipos", inaccesible para
        # roles como PROPIETARIO.
        modulos_disponibles = self.auth.modulos_permitidos()
        if modulos_disponibles:
            self._navegar(modulos_disponibles[0])

    # ------------------------------------------------------------------
    # Construcción de la UI base
    # ------------------------------------------------------------------

    def _construir_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=115, corner_radius=0,
            fg_color=BG_CARD, border_width=1, border_color=BORDER_INPUT
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.pack_propagate(False)

        # Espaciador superior
        ctk.CTkLabel(self.sidebar, text="", height=20).pack()

        # Botones de navegación
        self._btn_sidebar = {}
        self._lbl_sidebar = {}

        for id_mod, emoji, etiqueta in MENU_ITEMS:
            # PARCHE QA: Control de Acceso Basado en Roles (RBAC).
            # Si el rol de la sesión activa no tiene permiso para este módulo,
            # ni siquiera se construye el botón correspondiente.
            if not self.auth.tiene_acceso_modulo(id_mod):
                continue

            contenedor = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            contenedor.pack(pady=10, fill="x", padx=10)

            btn = ctk.CTkButton(
                contenedor, text=emoji,
                font=ctk.CTkFont(size=20),
                width=78, height=48, corner_radius=24,
                fg_color="transparent", text_color=TXT_MUTED,
                hover_color=("#E2E8F0", "#1E293B"),
                command=lambda m=id_mod: self._navegar(m)
            )
            btn.pack(anchor="center")
            self._btn_sidebar[id_mod] = btn

            lbl = ctk.CTkLabel(
                contenedor, text=etiqueta,
                font=font_small(), text_color=TXT_MUTED
            )
            lbl.pack(pady=(3, 0), anchor="center")
            self._lbl_sidebar[id_mod] = lbl

        # Botón de cierre de sesión al fondo del sidebar
        ctk.CTkButton(
            self.sidebar, text="Cerrar sesión",
            font=font_small(), height=36,
            fg_color="#DC2626", hover_color="#B91C1C",
            text_color="white", corner_radius=BTN_RADIUS,
            command=self._cerrar_sesion
        ).pack(side="bottom", pady=20, padx=10, fill="x")

        # Indicador del usuario activo
        ctk.CTkLabel(
            self.sidebar,
            text=f"{self.auth.usuario_actual}\n{self.auth.rol_actual.split()[0].title()}",
            font=font_small(), text_color=TXT_MUTED,
            justify="center", wraplength=100
        ).pack(side="bottom", pady=(0, 6))

    def _construir_area_principal(self):
        """Frame contenedor del lado derecho. Los módulos se montan aquí."""
        self.area_principal = ctk.CTkFrame(
            self, corner_radius=0, fg_color="transparent"
        )
        self.area_principal.grid(row=0, column=1, padx=30, pady=28, sticky="nsew")
        self.area_principal.grid_columnconfigure(0, weight=1)
        self.area_principal.grid_rowconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Navegación entre módulos
    # ------------------------------------------------------------------

    def _navegar(self, id_modulo: str):
        """
        Destruye el módulo actual y monta el nuevo en el área principal.
        Importación diferida: cada módulo se importa solo cuando se necesita.
        """
        # PARCHE QA: Control de Acceso Basado en Roles (RBAC).
        # Aunque el botón esté oculto, esta verificación impide navegar al
        # módulo por cualquier otra vía (por ejemplo, una llamada directa).
        if not self.auth.tiene_acceso_modulo(id_modulo):
            messagebox.showerror(
                "Acceso denegado",
                f"Tu rol ({self.auth.rol_actual}) no tiene permiso para "
                f"acceder a este módulo.",
                parent=self
            )
            return

        if self.modulo_activo == id_modulo:
            return  # Ya estamos aquí, nada que hacer

        # Destruir el frame del módulo anterior si existe
        if self._frame_modulo and self._frame_modulo.winfo_exists():
            self._frame_modulo.destroy()

        self.modulo_activo = id_modulo
        self._actualizar_resaltado_sidebar()

        # Importación diferida para no cargar todo al arrancar
        if id_modulo == "equipos":
            from views.asset_module   import AssetModule
            self._frame_modulo = AssetModule(self.area_principal, self.asset_ctrl, self.auth)

        elif id_modulo == "prestamos":
            from views.loan_module    import LoanModule
            self._frame_modulo = LoanModule(self.area_principal, self.loan_ctrl, self.auth)

        elif id_modulo == "asignacion":
            from views.assign_module  import AssignModule
            self._frame_modulo = AssignModule(
                self.area_principal, self.loan_ctrl,
                self.asset_ctrl, self.user_ctrl, self.auth
            )

        elif id_modulo == "alarmas":
            from views.alarm_module   import AlarmModule
            self._frame_modulo = AlarmModule(self.area_principal, self.asset_ctrl, self.auth)

        elif id_modulo == "usuarios":
            from views.user_module    import UserModule
            self._frame_modulo = UserModule(self.area_principal, self.user_ctrl, self.auth)

        elif id_modulo == "historial":
            from views.history_module import HistoryModule
            self._frame_modulo = HistoryModule(self.area_principal, self.history_ctrl)

        if self._frame_modulo:
            self._frame_modulo.grid(row=0, column=0, sticky="nsew")

    def _actualizar_resaltado_sidebar(self):
        """Resalta el botón activo y opaca los demás."""
        for id_mod, btn in self._btn_sidebar.items():
            lbl = self._lbl_sidebar[id_mod]
            if id_mod == self.modulo_activo:
                btn.configure(fg_color=ACCENT_BLUE, text_color="white")
                lbl.configure(
                    text_color=TXT_MAIN,
                    font=ctk.CTkFont(size=11, weight="bold", family="Segoe UI")
                )
            else:
                btn.configure(fg_color="transparent", text_color=TXT_MUTED)
                lbl.configure(
                    text_color=TXT_MUTED,
                    font=ctk.CTkFont(size=11, family="Segoe UI")
                )

    # ------------------------------------------------------------------
    # Cierre de sesión
    # ------------------------------------------------------------------

    def _cerrar_sesion(self):
        confirmar = messagebox.askyesno(
            "Cerrar sesión",
            "¿Estás seguro de que deseas salir de tu cuenta?",
            parent=self
        )
        if not confirmar:
            return

        self.auth.cerrar_sesion()
        self.destroy()
        if self.on_logout:
            self.on_logout()

    # ------------------------------------------------------------------
    # Estilo del Treeview (compartido por todos los módulos)
    # ------------------------------------------------------------------

    def _configurar_estilo_treeview(self):
        """
        Aplica estilos al widget ttk.Treeview según el modo de color actual.
        Se llama una vez al iniciar y puede llamarse de nuevo al cambiar tema.
        """
        self.ttk_style = Style()
        self.ttk_style.theme_use("clam")
        self.actualizar_estilo_treeview()

    def actualizar_estilo_treeview(self):
        """Reaplica colores del Treeview al conmutar entre Light y Dark."""
        es_oscuro = ctk.get_appearance_mode() == "Dark"
        bg   = BG_DARK_CARD   if es_oscuro else BG_LIGHT_CARD
        fg   = TXT_DARK_MAIN  if es_oscuro else TXT_LIGHT_MAIN
        bg_h = "#1E293B"      if es_oscuro else "#E2E8F0"
        sel  = "#3B82F6"      if es_oscuro else "#2563EB"
        odd  = "#1E293B"      if es_oscuro else "#F1F5F9"

        self.ttk_style.configure(
            "Treeview",
            background=bg, foreground=fg, fieldbackground=bg,
            rowheight=38, font=("Segoe UI", 11), borderwidth=0
        )
        self.ttk_style.map(
            "Treeview",
            background=[("selected", sel)],
            foreground=[("selected", "white")]
        )
        self.ttk_style.configure(
            "Treeview.Heading",
            background=bg_h, foreground=fg,
            relief="flat", font=("Segoe UI", 11, "bold")
        )
        self.ttk_style.map(
            "Treeview.Heading",
            background=[("active", bg_h)],
            foreground=[("active", fg)]
        )
        self.ttk_style.configure("Treeview", oddrow=odd)

    def conmutar_tema(self):
        """Alterna entre Dark y Light. Llamado por los módulos que tienen botón de tema."""
        nuevo = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(nuevo)
        self.actualizar_estilo_treeview()
        self._actualizar_resaltado_sidebar()
        return nuevo  # Los módulos lo usan para cambiar el ícono del botón
