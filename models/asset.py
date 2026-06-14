"""
models/asset.py
---------------
Modelo de Activos Tecnológicos. Gestiona la tabla 'equipos' en SQLite.
Incluye validación de serial único, estados permitidos y fechas de mantenimiento.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import sqlite3
from datetime import datetime

from database import get_connection


# Estados operativos válidos del sistema. Cualquier otro valor es rechazado.
ESTADOS_VALIDOS = {"OPERATIVO", "MANTENIMIENTO", "ASIGNADO", "INACTIVO"}


# ---------------------------------------------------------------------------
# Funciones de validación (sin efectos secundarios)
# ---------------------------------------------------------------------------

def _es_fecha_valida(fecha_str: str) -> tuple[bool, str]:
    """
    Valida que la fecha tenga formato DD/MM/AAAA y sea una fecha real.
    A diferencia de la fecha de nacimiento, la fecha de mantenimiento
    SÍ puede estar en el futuro (es una fecha planificada).
    """
    try:
        datetime.strptime(fecha_str, "%d/%m/%Y")
        return True, ""
    except ValueError:
        return False, "La fecha debe tener el formato DD/MM/AAAA y ser una fecha real (ej: 15/07/2025)."


# ---------------------------------------------------------------------------
# Funciones del modelo (CRUD)
# ---------------------------------------------------------------------------

def obtener_todos(texto_busqueda: str = "", filtro_estado: str = "ALL") -> list:
    """
    Devuelve todos los equipos. Acepta filtro por estado y búsqueda parcial
    por nombre, marca, modelo o serial.
    """
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM equipos WHERE 1=1"
    params = []

    if filtro_estado.upper() != "ALL":
        query += " AND UPPER(estado) = ?"
        params.append(filtro_estado.upper())

    if texto_busqueda:
        term = f"%{texto_busqueda.upper()}%"
        query += " AND (UPPER(nombre) LIKE ? OR UPPER(marca) LIKE ? OR UPPER(modelo) LIKE ? OR UPPER(serial) LIKE ?)"
        params.extend([term, term, term, term])

    cursor.execute(query, params)
    resultado = cursor.fetchall()
    conn.close()
    return resultado


def obtener_operativos() -> list:
    """
    Devuelve solo los equipos en estado OPERATIVO.
    Usado exclusivamente por el módulo de asignación de préstamos.
    """
    return obtener_todos(filtro_estado="OPERATIVO")


def obtener_custodio_actual(serial: str) -> str:
    """
    Busca en la tabla de préstamos quién tiene actualmente un equipo.
    Devuelve el nombre del prestatario o 'SIN USUARIO ASIGNADO'.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT prestatario FROM prestamos
        WHERE UPPER(serial) = ? AND UPPER(estado) = 'ASIGNADOS'
        ORDER BY id DESC
        LIMIT 1
    """, (serial.upper(),))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0].upper() if resultado else "SIN USUARIO ASIGNADO"


def crear_activo(nombre, marca, modelo, serial, estado, mantenimiento) -> tuple[bool, str]:
    """
    Inserta un nuevo activo en la BD después de validar todos los campos.
    Devuelve (True, "") si fue exitoso, (False, "mensaje") si algo falla.
    """
    # --- Normalización ---
    nombre       = nombre.strip().upper()
    marca        = marca.strip().upper()
    modelo       = modelo.strip().upper()
    serial       = serial.strip().upper()
    estado       = estado.strip().upper()
    mantenimiento = mantenimiento.strip()

    # --- Campos obligatorios ---
    if not nombre or not marca or not serial:
        return False, "El nombre del activo, el fabricante y el serial son campos obligatorios."

    # --- Estado permitido ---
    if estado not in ESTADOS_VALIDOS:
        return False, f"Estado no válido. Los estados permitidos son: {', '.join(ESTADOS_VALIDOS)}."

    # --- Fecha de mantenimiento ---
    if mantenimiento:
        fecha_ok, msg_fecha = _es_fecha_valida(mantenimiento)
        if not fecha_ok:
            return False, msg_fecha

    # --- Inserción con control de serial duplicado ---
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO equipos (nombre, marca, modelo, serial, estado, mantenimiento)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, marca, modelo, serial, estado, mantenimiento))
        conn.commit()
        conn.close()
        return True, ""

    except sqlite3.IntegrityError:
        conn.close()
        return False, f"El serial '{serial}' ya existe en el inventario. Cada activo debe tener un serial único."


def actualizar_estado(id_activo: int, nuevo_estado: str) -> tuple[bool, str]:
    """
    Cambia únicamente el estado operativo de un activo.
    Valida que el nuevo estado sea uno de los valores permitidos.
    """
    nuevo_estado = nuevo_estado.strip().upper()

    if nuevo_estado not in ESTADOS_VALIDOS:
        return False, f"Estado no válido. Use uno de: {', '.join(ESTADOS_VALIDOS)}."

    conn = get_connection()
    cursor = conn.cursor()

    # Obtenemos el nombre del equipo para usarlo en el historial desde el controlador
    cursor.execute("SELECT nombre FROM equipos WHERE id = ?", (id_activo,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False, "No se encontró ningún activo con ese ID."

    nombre_equipo = resultado[0]
    cursor.execute(
        "UPDATE equipos SET estado = ? WHERE id = ?",
        (nuevo_estado, id_activo)
    )
    conn.commit()
    conn.close()
    return True, nombre_equipo


def resolver_alarma(id_activo: int, nueva_fecha: str, nuevo_estado: str) -> tuple[bool, str]:
    """
    Atiende una incidencia de mantenimiento: actualiza la fecha de próxima
    revisión y el estado del equipo en una sola operación.
    Devuelve (True, nombre_equipo) o (False, "mensaje de error").
    """
    nueva_fecha  = nueva_fecha.strip()
    nuevo_estado = nuevo_estado.strip().upper()

    fecha_ok, msg_fecha = _es_fecha_valida(nueva_fecha)
    if not fecha_ok:
        return False, msg_fecha

    if nuevo_estado not in ESTADOS_VALIDOS:
        return False, f"Estado no válido. Use uno de: {', '.join(ESTADOS_VALIDOS)}."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre FROM equipos WHERE id = ?", (id_activo,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False, "No se encontró el activo con ese ID."

    nombre_equipo = resultado[0]
    cursor.execute(
        "UPDATE equipos SET estado = ?, mantenimiento = ? WHERE id = ?",
        (nuevo_estado, nueva_fecha, id_activo)
    )
    conn.commit()
    conn.close()
    return True, nombre_equipo


def eliminar_activo(id_activo: int) -> tuple[bool, str]:
    """
    Elimina un activo por su ID.
    Devuelve (True, serial) para poder registrarlo en el historial.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, serial FROM equipos WHERE id = ?", (id_activo,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False, "No se encontró el activo con ese ID."

    nombre, serial = resultado
    cursor.execute("DELETE FROM equipos WHERE id = ?", (id_activo,))
    conn.commit()
    conn.close()
    return True, f"{nombre} (Serial: {serial})"


def obtener_alarmas(texto_busqueda: str = "") -> list:
    """
    Devuelve todos los equipos que tienen una incidencia activa:
    - Fecha de mantenimiento vencida (ya pasó la fecha límite), O
    - Estado marcado como INACTIVO (dañado/fuera de servicio).

    Devuelve una lista de tuplas con la información necesaria para la vista.
    """
    todos = obtener_todos(texto_busqueda=texto_busqueda)
    hoy = datetime.now()
    alarmas = []

    for eq in todos:
        id_eq, nombre, marca, modelo, serial, estado, fecha_mant = eq
        tiene_alarma = False
        motivo = ""
        descripcion = ""

        # Revisar si la fecha de mantenimiento ya venció
        if fecha_mant:
            try:
                fecha_obj = datetime.strptime(fecha_mant, "%d/%m/%Y")
                if fecha_obj <= hoy and estado.upper() != "MANTENIMIENTO REALIZADO":
                    tiene_alarma = True
                    motivo      = "REVISIÓN VENCIDA"
                    descripcion = "EL CICLO ÚTIL OPERACIONAL HA EXPIRADO"
            except ValueError:
                pass  # Fecha mal formateada, ignoramos

        # Un equipo INACTIVO también genera alarma independientemente de la fecha
        if estado.upper() == "INACTIVO":
            tiene_alarma = True
            motivo      = "EQUIPO INACTIVO"
            descripcion = "ACTIVO MARCADO COMO FUERA DE SERVICIO"

        if tiene_alarma:
            alarmas.append((id_eq, nombre, motivo, descripcion, modelo, fecha_mant, "CRÍTICA"))

    return alarmas
