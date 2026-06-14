"""
models/loan.py
--------------
Modelo de Préstamos. Gestiona la tabla 'prestamos' en SQLite.
Controla el ciclo completo: asignación, modificación y cierre de préstamos.

Las búsquedas soportan filtrado por fecha, serial, modelo y tipo de activo,
corrigiendo la limitación del buscador original.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import sqlite3
from datetime import datetime

from database import get_connection


# Estados válidos para un préstamo en el sistema
ESTADOS_PRESTAMO = {"ASIGNADOS", "EN DEVOLUCIÓN"}


# ---------------------------------------------------------------------------
# Validaciones internas
# ---------------------------------------------------------------------------

def _es_fecha_valida(fecha_str: str) -> tuple[bool, str]:
    """Verifica que una cadena tenga formato DD/MM/AAAA y sea una fecha real."""
    try:
        datetime.strptime(fecha_str, "%d/%m/%Y")
        return True, ""
    except ValueError:
        return False, f"La fecha '{fecha_str}' no tiene el formato correcto (DD/MM/AAAA)."


def _fecha_devolucion_es_posterior(fecha_prestamo: str, fecha_devolucion: str) -> bool:
    """Verifica que la devolución sea igual o posterior al préstamo."""
    fp = datetime.strptime(fecha_prestamo,   "%d/%m/%Y")
    fd = datetime.strptime(fecha_devolucion, "%d/%m/%Y")
    return fd >= fp


# ---------------------------------------------------------------------------
# Funciones del modelo (CRUD)
# ---------------------------------------------------------------------------

def obtener_todos(texto_busqueda: str = "", filtro_estado: str = "ALL") -> list:
    """
    Devuelve todos los préstamos con soporte de filtrado mejorado.

    La búsqueda funciona sobre: equipo (tipo/nombre), serial, prestatario,
    fecha de préstamo y fecha de devolución. Esto corrige el buscador original
    que no filtraba por fecha ni serial correctamente.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM prestamos WHERE 1=1"
    params = []

    if filtro_estado.upper() != "ALL":
        query += " AND UPPER(estado) = ?"
        params.append(filtro_estado.upper())

    if texto_busqueda:
        term = f"%{texto_busqueda.upper()}%"
        query += """
            AND (
                UPPER(equipo)      LIKE ?
             OR UPPER(serial)      LIKE ?
             OR UPPER(prestatario) LIKE ?
             OR UPPER(fecha_p)     LIKE ?
             OR UPPER(fecha_d)     LIKE ?
            )
        """
        params.extend([term, term, term, term, term])

    cursor.execute(query, params)
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def registrar_prestamo(id_activo: int, prestatario: str,
                       fecha_prestamo: str, fecha_devolucion: str,
                       ubicacion: str) -> tuple[bool, str]:
    """
    Registra un nuevo préstamo en la BD y actualiza el estado del equipo a ASIGNADO.

    Pasos:
    1. Valida los datos recibidos.
    2. Busca nombre y serial del activo en la tabla equipos.
    3. Inserta el préstamo.
    4. Actualiza el estado del equipo a 'ASIGNADO'.

    Devuelve (True, "nombre_activo") o (False, "mensaje de error").
    """
    # --- Normalización ---
    prestatario      = prestatario.strip().upper()
    fecha_prestamo   = fecha_prestamo.strip()
    fecha_devolucion = fecha_devolucion.strip()
    ubicacion        = ubicacion.strip().upper()

    # --- Validaciones ---
    if not prestatario:
        return False, "Debe seleccionar un prestatario de la lista."

    if not ubicacion:
        return False, "El campo de ubicación/destino es obligatorio."

    fecha_p_ok, msg_p = _es_fecha_valida(fecha_prestamo)
    if not fecha_p_ok:
        return False, f"Fecha de préstamo inválida: {msg_p}"

    fecha_d_ok, msg_d = _es_fecha_valida(fecha_devolucion)
    if not fecha_d_ok:
        return False, f"Fecha de devolución inválida: {msg_d}"

    if not _fecha_devolucion_es_posterior(fecha_prestamo, fecha_devolucion):
        return False, "La fecha de devolución no puede ser anterior a la fecha de préstamo."

    # --- Obtener datos del equipo ---
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, serial FROM equipos WHERE id = ?", (id_activo,))
    equipo = cursor.fetchone()

    if not equipo:
        conn.close()
        return False, "No se encontró el equipo seleccionado en el inventario."

    nombre_equipo, serial_equipo = equipo

    # --- Insertar el préstamo ---
    cursor.execute("""
        INSERT INTO prestamos (equipo, serial, prestatario, fecha_p, fecha_d, estado)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        nombre_equipo.upper(), serial_equipo.upper(),
        prestatario, fecha_prestamo, fecha_devolucion,
        "ASIGNADOS"
    ))

    # --- Cambiar estado del equipo a ASIGNADO ---
    cursor.execute(
        "UPDATE equipos SET estado = 'ASIGNADO' WHERE id = ?",
        (id_activo,)
    )

    conn.commit()
    conn.close()
    return True, nombre_equipo


def actualizar_prestamo(id_prestamo: int, nueva_fecha_devolucion: str,
                        nuevo_estado: str) -> tuple[bool, str]:
    """
    Modifica la fecha de devolución y/o el estado de un préstamo existente.
    Devuelve (True, nombre_equipo) o (False, "mensaje de error").
    """
    nueva_fecha_devolucion = nueva_fecha_devolucion.strip()
    nuevo_estado           = nuevo_estado.strip().upper()

    fecha_ok, msg_fecha = _es_fecha_valida(nueva_fecha_devolucion)
    if not fecha_ok:
        return False, msg_fecha

    if nuevo_estado not in ESTADOS_PRESTAMO:
        return False, f"Estado no válido. Use uno de: {', '.join(ESTADOS_PRESTAMO)}."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT equipo FROM prestamos WHERE id = ?", (id_prestamo,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False, "No se encontró el préstamo con ese ID."

    nombre_equipo = resultado[0]
    cursor.execute("""
        UPDATE prestamos
        SET fecha_d = ?, estado = ?
        WHERE id = ?
    """, (nueva_fecha_devolucion, nuevo_estado, id_prestamo))

    conn.commit()
    conn.close()
    return True, nombre_equipo


def eliminar_prestamo(id_prestamo: int) -> tuple[bool, str]:
    """
    Elimina un préstamo por su ID.
    Devuelve (True, "descripcion") para usar en el historial.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT equipo, prestatario FROM prestamos WHERE id = ?",
        (id_prestamo,)
    )
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False, "No se encontró el préstamo con ese ID."

    equipo, prestatario = resultado
    cursor.execute("DELETE FROM prestamos WHERE id = ?", (id_prestamo,))
    conn.commit()
    conn.close()
    return True, f"{equipo} asignado a {prestatario}"
