"""
database.py
-----------
Módulo de inicialización de la base de datos SQLite para Lab-Inventory Manager.
Se encarga únicamente de crear las tablas y la conexión compartida.

Autores: Equipo de Ingeniería Informática - 3er Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import sqlite3
from datetime import datetime

# Nombre del archivo de base de datos. Un solo lugar para cambiarlo si hace falta.
DB_NAME = "xorte_database.db"


def get_connection():
    """Devuelve una conexión activa a la base de datos SQLite."""
    return sqlite3.connect(DB_NAME)


def inicializar_base_de_datos():
    """
    Crea todas las tablas si no existen y genera el usuario administrador
    por defecto la primera vez que corre el sistema.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla de equipos/activos tecnológicos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL,
            marca        TEXT NOT NULL,
            modelo       TEXT,
            serial       TEXT UNIQUE NOT NULL,
            estado       TEXT DEFAULT 'OPERATIVO',
            mantenimiento TEXT
        )
    """)

    # Tabla de préstamos/asignaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            equipo      TEXT NOT NULL,
            serial      TEXT NOT NULL,
            prestatario TEXT NOT NULL,
            fecha_p     TEXT NOT NULL,
            fecha_d     TEXT NOT NULL,
            estado      TEXT DEFAULT 'ASIGNADOS'
        )
    """)

    # Tabla de usuarios del sistema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nombres          TEXT NOT NULL,
            cedula           TEXT NOT NULL UNIQUE,
            fecha_nac        TEXT NOT NULL,
            correo           TEXT,
            telefono         TEXT,
            username         TEXT NOT NULL UNIQUE,
            rol              TEXT DEFAULT 'PRESTATARIO EXTERNO',
            password         TEXT NOT NULL,
            q1               TEXT,
            a1               TEXT,
            q2               TEXT,
            a2               TEXT,
            q3               TEXT,
            a3               TEXT,
            debe_cambiar_pwd INTEGER DEFAULT 0
        )
    """)

    # Tabla de historial/auditoría
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            accion      TEXT NOT NULL,
            referencia  TEXT,
            responsable TEXT,
            fecha       TEXT,
            detalles    TEXT,
            categoria   TEXT
        )
    """)

    # Migración segura: agrega la columna si la BD ya existe sin ella
    try:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN debe_cambiar_pwd INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # La columna ya existe, no hacemos nada

    conn.commit()

    # Crear administrador maestro si la tabla de usuarios está vacía
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios
                (nombres, cedula, fecha_nac, correo, telefono, username,
                 rol, password, q1, a1, q2, a2, q3, a3, debe_cambiar_pwd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "ADMINISTRADOR MAESTRO", "V-00000000", "01/01/2000",
            "ADMIN@XORTE.COM", "0000000000", "ADMIN",
            "ADMINISTRADOR EJECUTIVO", "1234",
            "", "", "", "", "", "", 0
        ))
        conn.commit()

        # Registrar en el historial la creación inicial del sistema
        fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        cursor.execute("""
            INSERT INTO historial (accion, referencia, responsable, fecha, detalles, categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "INICIO", "SISTEMA CENTRAL", "SISTEMA",
            fecha_hora,
            "BASE DE DATOS Y CUENTA ADMINISTRADORA CREADAS.",
            "Sistema"
        ))
        conn.commit()

    conn.close()
