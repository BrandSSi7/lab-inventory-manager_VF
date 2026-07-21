
"""
views/theme.py
--------------
Constantes de diseño (colores, fuentes, radios) compartidas por todas las vistas.
ajustar la estética de la aplicación

"""

import customtkinter as ctk

# ------------------------------------------------------------------
# Paleta de colores (índice 0 = Light, índice 1 = Dark)
# ------------------------------------------------------------------
BG_MAIN        = ("#F8FAFC", "#0B0F19")
BG_CARD        = ("#FFFFFF", "#151B2C")
BG_INPUT       = ("#FFFFFF", "#1A2236")
BORDER_INPUT   = ("#CBD5E1", "#374151")
TXT_INPUT      = ("#0F172A", "#F3F4F6")
TXT_PLACEHOLDER= ("#64748B", "#9CA3AF")
ACCENT_BLUE    = ("#2563EB", "#3B82F6")
ACCENT_HOVER   = ("#1D4ED8", "#1A56DB")
TXT_MAIN       = ("#0F172A", "#F9FAFB")
TXT_MUTED      = ("#64748B", "#9CA3AF")

# Panel de marca (login): un carril oscuro fijo que no cambia con el modo
# claro/oscuro, para dar identidad visual consistente al lienzo de entrada.
BRAND_BG       = ("#111827", "#0A0E1A")
BRAND_TEXT     = "#F9FAFB"
BRAND_MUTED    = "#94A3B8"
BRAND_ACCENT   = "#3B82F6"

# Valores planos para el ttk.Style (no soporta tuplas CTk)
BG_DARK_CARD   = "#151B2C"
TXT_DARK_MAIN  = "#F9FAFB"
BG_LIGHT_CARD  = "#FFFFFF"
TXT_LIGHT_MAIN = "#0F172A"

# ------------------------------------------------------------------
# Métricas de componentes
# ------------------------------------------------------------------
BTN_RADIUS  = 4
INPUT_H     = 36   # Altura estándar de campos de entrada
BTN_H       = 38   # Altura estándar de botones


# ------------------------------------------------------------------
# Helpers de fuente
# ------------------------------------------------------------------
def font_title():
    return ctk.CTkFont(size=24, weight="bold", family="Segoe UI")

def font_section():
    return ctk.CTkFont(size=12, weight="bold", family="Segoe UI")

def font_body():
    return ctk.CTkFont(size=12, family="Segoe UI")

def font_small():
    return ctk.CTkFont(size=11, family="Segoe UI")


# ------------------------------------------------------------------
# Panel de marca reutilizable (Login, Registro, Recuperación de cuenta)
# ------------------------------------------------------------------
def construir_panel_marca(panel):
    """
    Llena un contenedor ya ubicado (fg_color=BRAND_BG, grid en columna
    izquierda) con el contenido de marca compartido por las tres pantallas
    de autenticación: título XORTE, tagline, acento visual y lista de
    características del sistema. Centraliza el diseño para que las tres
    ventanas luzcan consistentes entre sí.
    """
    contenido = ctk.CTkFrame(panel, fg_color="transparent")
    contenido.place(relx=0.5, rely=0.5, anchor="center")

    font_hero    = ctk.CTkFont(size=46, weight="bold", family="Segoe UI")
    font_tagline = ctk.CTkFont(size=14, weight="bold", family="Segoe UI")
    font_feature = ctk.CTkFont(size=13, family="Segoe UI")

    ctk.CTkLabel(
        contenido, text="XORTE",
        font=font_hero, text_color=BRAND_TEXT
    ).pack(anchor="w")

    ctk.CTkLabel(
        contenido, text="SISTEMA CENTRAL DE CONTROL",
        font=font_tagline, text_color=BRAND_ACCENT
    ).pack(anchor="w", pady=(2, 0))

    ctk.CTkFrame(
        contenido, fg_color=BRAND_ACCENT, width=64, height=3,
        corner_radius=2
    ).pack(anchor="w", pady=(18, 28))

    caracteristicas = [
        "Control de equipos y activos de laboratorio",
        "Gestión de préstamos y asignaciones",
        "Alertas de mantenimiento preventivo",
        "Historial y auditoría completa",
    ]

    for texto in caracteristicas:
        fila = ctk.CTkFrame(contenido, fg_color="transparent")
        fila.pack(anchor="w", pady=6, fill="x")

        ctk.CTkFrame(
            fila, fg_color=BRAND_ACCENT, width=6, height=6,
            corner_radius=3
        ).pack(side="left", padx=(0, 12), pady=2)

        ctk.CTkLabel(
            fila, text=texto,
            font=font_feature, text_color=BRAND_MUTED
        ).pack(side="left")


