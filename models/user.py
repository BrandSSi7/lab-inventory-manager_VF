"""
models/user.py
--------------
Modelo de Usuarios. Gestiona toda la interacción con la tabla 'usuarios'
en SQLite: consultas, inserciones, actualizaciones y eliminaciones.

Toda validación de datos ocurre AQUÍ, antes de tocar la base de datos.
El controlador solo recibe (True, "") o (False, "mensaje de error").

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import sqlite3
import re
from datetime import datetime

from database import get_connection, DB_NAME


# ---------------------------------------------------------------------------
# Funciones de validación de datos (sin efectos secundarios)
# ---------------------------------------------------------------------------

def _es_cedula_valida(cedula: str) -> bool:
    """
    Valida que la cédula sea alfanumérica.
    Acepta formatos como: V-12345678, E-1234567, 12345678, EXT-001.
    """
    # Permite letras, números y guiones. Mínimo 3 caracteres.
    patron = r'^[A-Za-z0-9\-]+$'
    return bool(re.match(patron, cedula)) and len(cedula) >= 3


def _es_correo_valido(correo: str) -> bool:
    """
    Valida que el correo tenga un '@' y un dominio con punto.
    Ejemplo válido: usuario@gmail.com
    """
    patron = r'^[\w\.\-\+]+@[\w\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, correo))


def _es_telefono_valido(telefono: str) -> bool:
    """
    Valida que el teléfono contenga solo dígitos numéricos.
    Mínimo 7 dígitos para ser razonable.
    """
    return telefono.isdigit() and len(telefono) >= 7


def _es_fecha_valida(fecha_str: str) -> tuple[bool, str]:
    """
    Valida que la fecha tenga formato DD/MM/AAAA y sea estrictamente anterior
    a hoy. La fecha actual misma no se acepta como fecha de nacimiento.
    """
    try:
        fecha = datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError:
        return False, "La fecha debe tener el formato DD/MM/AAAA y ser una fecha real."

    # Comparamos solo la fecha (date), no la hora, para que "hoy" quede excluido
    if fecha.date() >= datetime.now().date():
        return False, "La fecha de nacimiento debe ser estrictamente anterior a hoy."

    return True, ""


def _es_password_segura(password: str) -> tuple[bool, str]:
    """
    Valida que la contraseña cumpla los requisitos mínimos de seguridad:
      - Al menos 8 caracteres
      - Al menos una letra (mayúscula o minúscula)
      - Al menos un dígito numérico
      - Al menos un carácter especial (símbolo)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r'[A-Za-z]', password):
        return False, "La contraseña debe contener al menos una letra."
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número."
    if not re.search(r'[^A-Za-z0-9]', password):
        return False, "La contraseña debe contener al menos un carácter especial (ej: @, #, !, %)."
    return True, ""


def _preguntas_son_distintas(q1: str, q2: str, q3: str) -> bool:
    """Verifica que las tres preguntas de seguridad sean diferentes entre sí."""
    preguntas = [q1.strip().upper(), q2.strip().upper(), q3.strip().upper()]
    return len(set(preguntas)) == 3


def _respuestas_son_distintas(a1: str, a2: str, a3: str) -> bool:
    """Verifica que las tres respuestas de seguridad sean diferentes entre sí."""
    respuestas = [a1.strip().upper(), a2.strip().upper(), a3.strip().upper()]
    return len(set(respuestas)) == 3


# ---------------------------------------------------------------------------
# Funciones del modelo (CRUD con validación integrada)
# ---------------------------------------------------------------------------

def validar_login(username: str, password: str) -> bool:
    """
    Comprueba si el par usuario/contraseña existe en la BD.
    La comparación es EXACTA (case-sensitive) en ambos campos.
    Se elimina UPPER() para respetar mayúsculas, minúsculas y caracteres especiales.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Sin UPPER(): el username y password se comparan tal cual fueron guardados
    cursor.execute(
        "SELECT id FROM usuarios WHERE username = ? AND password = ?",
        (username.strip(), password)
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None


def obtener_rol(username: str) -> str:
    """Devuelve el rol del usuario. Si no existe, retorna 'SIN ACCESO'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rol FROM usuarios WHERE username = ?",
        (username.strip(),)
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0].upper() if resultado else "SIN ACCESO"


def necesita_cambio_password(username: str) -> bool:
    """Devuelve True si el usuario tiene pendiente cambiar su contraseña temporal."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT debe_cambiar_pwd FROM usuarios WHERE username = ?",
        (username.strip(),)
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] == 1 if resultado else False


def cambiar_password(username: str, nueva_password: str) -> tuple[bool, str]:
    """
    Actualiza la contraseña del usuario y limpia la bandera de cambio obligatorio.
    La nueva contraseña debe cumplir los requisitos de seguridad (8+ chars, letra,
    número y símbolo especial).
    """
    pwd_ok, msg_pwd = _es_password_segura(nueva_password.strip())
    if not pwd_ok:
        return False, msg_pwd

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET password = ?, debe_cambiar_pwd = 0 WHERE username = ?",
        (nueva_password.strip(), username.strip())
    )
    conn.commit()
    conn.close()
    return True, ""


def buscar_por_username_o_correo(busqueda: str):
    """
    Busca un usuario por su nombre de usuario o correo electrónico.
    Devuelve la fila completa o None si no encuentra nada.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE UPPER(username) = ? OR UPPER(correo) = ?",
        (busqueda.upper(), busqueda.upper())
    )
    resultado = cursor.fetchone()
    conn.close()
    return resultado


def obtener_todos(texto_busqueda: str = "") -> list:
    """
    Devuelve todos los usuarios.
    Si el término es un número entero busca por ID exacto además de los campos de texto.
    """
    conn = get_connection()
    cursor = conn.cursor()
    base = "SELECT id, nombres, cedula, fecha_nac, correo, telefono, username, rol FROM usuarios"

    if not texto_busqueda:
        cursor.execute(base)
    elif texto_busqueda.strip().isdigit():
        term = f"%{texto_busqueda.strip().upper()}%"
        id_val = int(texto_busqueda.strip())
        cursor.execute(
            base + " WHERE id = ?"
            " OR UPPER(nombres)  LIKE ?"
            " OR UPPER(cedula)   LIKE ?"
            " OR UPPER(correo)   LIKE ?"
            " OR UPPER(username) LIKE ?",
            (id_val, term, term, term, term)
        )
    else:
        term = f"%{texto_busqueda.strip().upper()}%"
        cursor.execute(
            base + " WHERE UPPER(nombres)  LIKE ?"
            " OR UPPER(cedula)   LIKE ?"
            " OR UPPER(correo)   LIKE ?"
            " OR UPPER(username) LIKE ?",
            (term, term, term, term)
        )

    resultado = cursor.fetchall()
    conn.close()
    return resultado


def obtener_nombres_registrados() -> list[str]:
    """
    Devuelve solo los nombres de todos los usuarios (para poblar ComboBoxes
    en el módulo de préstamos sin texto libre).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombres FROM usuarios ORDER BY nombres ASC")
    resultado = [fila[0].upper() for fila in cursor.fetchall()]
    conn.close()
    return resultado


def crear_usuario(nom, cedula, fecha_nac, correo, telefono, username,
                  password, q1, a1, q2, a2, q3, a3) -> tuple[bool, str]:
    """
    Inserta un nuevo usuario en la BD después de pasar por todas las validaciones.
    Devuelve (True, "") si todo sale bien, o (False, "mensaje de error") si algo falla.
    """
    # --- Normalización de texto antes de cualquier validación ---
    nom      = nom.strip().title()       # "juan perez" → "Juan Perez"
    cedula   = cedula.strip().upper()
    correo   = correo.strip().upper()
    telefono = telefono.strip()
    username = username.strip().upper()
    fecha_nac = fecha_nac.strip()

    # --- Validaciones de campos obligatorios ---
    if not nom or not cedula or not username or not password or not fecha_nac:
        return False, "Los campos Nombre, Cédula, Fecha de Nacimiento, Usuario y Contraseña son obligatorios."

    if not _es_cedula_valida(cedula):
        return False, "La cédula solo puede contener letras, números y guiones (ej: V-12345678)."

    fecha_ok, msg_fecha = _es_fecha_valida(fecha_nac)
    if not fecha_ok:
        return False, msg_fecha

    pwd_ok, msg_pwd = _es_password_segura(password.strip())
    if not pwd_ok:
        return False, msg_pwd

    # El correo es opcional pero si se escribe, debe ser válido
    if correo and correo != "NO ASIGNADO":
        if not _es_correo_valido(correo):
            return False, "El correo no tiene un formato válido (debe contener '@' y un dominio)."

    # El teléfono es opcional pero si se escribe, debe ser solo números
    if telefono and telefono.upper() != "NO ASIGNADO":
        if not _es_telefono_valido(telefono):
            return False, "El teléfono solo puede contener dígitos numéricos (mínimo 7)."

    # --- Validación de preguntas y respuestas de seguridad ---
    if not q1 or not q2 or not q3 or not a1 or not a2 or not a3:
        return False, "Debe configurar las tres preguntas de seguridad con sus respectivas respuestas."

    if not _preguntas_son_distintas(q1, q2, q3):
        return False, "Las tres preguntas de seguridad deben ser diferentes entre sí."

    if not _respuestas_son_distintas(a1, a2, a3):
        return False, "Las tres respuestas de seguridad deben ser diferentes entre sí."

    # --- Inserción en la BD con captura de duplicados ---
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios
                (nombres, cedula, fecha_nac, correo, telefono, username,
                 rol, password, q1, a1, q2, a2, q3, a3, debe_cambiar_pwd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nom, cedula, fecha_nac,
            correo if correo else "NO ASIGNADO",
            telefono if telefono else "NO ASIGNADO",
            username, "PRESTATARIO EXTERNO", password.strip(),
            q1.strip().upper(), a1.strip().upper(),
            q2.strip().upper(), a2.strip().upper(),
            q3.strip().upper(), a3.strip().upper(),
            1  # Obliga a cambiar la contraseña en el primer login
        ))
        conn.commit()
        conn.close()
        return True, ""

    except sqlite3.IntegrityError as e:
        conn.close()
        # SQLite nos dice qué campo violó el UNIQUE constraint
        error_str = str(e).lower()
        if "username" in error_str:
            return False, f"El nombre de usuario '{username}' ya está en uso. Elija otro."
        if "cedula" in error_str:
            return False, f"La cédula '{cedula}' ya está registrada en el sistema."
        if "correo" in error_str:
            return False, f"El correo '{correo}' ya pertenece a otra cuenta."
        return False, f"No se pudo guardar el usuario: dato duplicado en el sistema."


def crear_usuario_rapido(nombre: str) -> tuple[bool, str]:
    """
    Alta rápida de un prestatario externo: genera un username automático
    y una contraseña temporal '1234'. Se usa desde el módulo de préstamos.
    """
    if not nombre or not nombre.strip():
        return False, "El nombre del prestatario no puede estar vacío."

    nombre_normalizado = nombre.strip().title()

    # Generar un username único basado en el primer nombre
    base_username = nombre_normalizado.split()[0].upper()
    username_final = base_username
    contador = 1

    conn = get_connection()
    cursor = conn.cursor()

    while True:
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username_final,))
        if cursor.fetchone() is None:
            break
        username_final = f"{base_username}{contador}"
        contador += 1

    # Obtener el próximo ID para generar una cédula externa única
    cursor.execute("SELECT MAX(id) FROM usuarios")
    max_id = cursor.fetchone()[0] or 0
    cedula_ext = f"EXT-{max_id + 1}"

    try:
        cursor.execute("""
            INSERT INTO usuarios
                (nombres, cedula, fecha_nac, correo, telefono, username,
                 rol, password, q1, a1, q2, a2, q3, a3, debe_cambiar_pwd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nombre_normalizado, cedula_ext, "01/01/2000",
            "NO ASIGNADO", "NO ASIGNADO",
            username_final, "PRESTATARIO EXTERNO", "1234",
            "", "", "", "", "", "", 1
        ))
        conn.commit()
        conn.close()
        return True, username_final

    except sqlite3.IntegrityError:
        conn.close()
        return False, "Ocurrió un error al registrar el prestatario. Intente con otro nombre."


def actualizar_usuario(id_usuario: int, nom, cedula, fecha_nac,
                       correo, telefono, rol) -> tuple[bool, str]:
    """
    Actualiza los datos de un usuario existente.
    No modifica el username ni la contraseña (eso va por flujos separados).
    """
    nom       = nom.strip().title()
    cedula    = cedula.strip().upper()
    correo    = correo.strip().upper()
    telefono  = telefono.strip()
    fecha_nac = fecha_nac.strip()

    if not nom or not cedula or not fecha_nac:
        return False, "El nombre, la cédula y la fecha de nacimiento son obligatorios."

    if not _es_cedula_valida(cedula):
        return False, "La cédula solo puede contener letras, números y guiones."

    fecha_ok, msg_fecha = _es_fecha_valida(fecha_nac)
    if not fecha_ok:
        return False, msg_fecha

    if correo and correo != "NO ASIGNADO":
        if not _es_correo_valido(correo):
            return False, "El correo no tiene un formato válido."

    if telefono and telefono.upper() != "NO ASIGNADO":
        if not _es_telefono_valido(telefono):
            return False, "El teléfono solo puede contener dígitos numéricos."

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE usuarios
            SET nombres = ?, cedula = ?, fecha_nac = ?,
                correo = ?, telefono = ?, rol = ?
            WHERE id = ?
        """, (nom, cedula, fecha_nac, correo, telefono, rol, id_usuario))
        conn.commit()
        conn.close()
        return True, ""

    except sqlite3.IntegrityError as e:
        conn.close()
        error_str = str(e).lower()
        if "cedula" in error_str:
            return False, f"La cédula '{cedula}' ya está registrada en otra cuenta."
        return False, "Dato duplicado: otro usuario ya tiene ese valor en un campo único."


def resetear_password(id_usuario: int, password_temporal: str) -> None:
    """
    Resetea la contraseña de un usuario y activa la bandera de cambio obligatorio.
    Solo puede ser llamado por un administrador (el controlador valida el rol).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE usuarios SET password = ?, debe_cambiar_pwd = 1 WHERE id = ?",
        (password_temporal, id_usuario)
    )
    conn.commit()
    conn.close()


def obtener_username_por_id(id_usuario: int) -> str:
    """Devuelve el username de un usuario dado su ID. Útil para el historial."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM usuarios WHERE id = ?", (id_usuario,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else "DESCONOCIDO"


def eliminar_usuario(id_usuario: int) -> tuple[bool, str]:
    """Elimina un usuario por su ID. Devuelve su nombre para registrar en el historial."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombres FROM usuarios WHERE id = ?", (id_usuario,))
    resultado = cursor.fetchone()

    if not resultado:
        conn.close()
        return False, "No se encontró el usuario con ese ID."

    nombre = resultado[0]
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (id_usuario,))
    conn.commit()
    conn.close()
    return True, nombre
