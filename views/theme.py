"""
views/theme.py
--------------
Constantes de diseño (colores, fuentes, radios) compartidas por todas las vistas.
Un solo lugar para ajustar la estética de toda la aplicación.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
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
