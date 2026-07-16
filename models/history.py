"""
models/history.py
-----------------
"""

from datetime import datetime
from database import get_connection



ORDENES_VALIDOS = {
    "Más Recientes":  "ORDER BY id DESC",
    "Más Antiguos":   "ORDER BY id ASC",
    "A-Z (Acción)":   "ORDER BY accion ASC",
    "A-Z (Activo)":   "ORDER BY referencia ASC",
    "A-Z (Usuario)":  "ORDER BY responsable ASC",
    "A-Z (Detalles)": "ORDER BY detalles ASC",
}


def registrar(accion: str, referencia: str, responsable: str,
              detalles: str, categoria: str) -> None:
    """
    Inserta un nuevo registro en el historial de auditoría.
    Esta función es llamada por todos los controladores después de cada operación.
    """
    fecha_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO historial (accion, referencia, responsable, fecha, detalles, categoria)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        accion.upper(),
        referencia.upper(),
        responsable.upper(),
        fecha_hora,
        detalles.upper(),
        categoria
    ))
    conn.commit()
    conn.close()


def obtener_todos(texto_busqueda: str = "", categoria: str = "Todos",
                  orden: str = "Más Recientes") -> list:
    """
    Devuelve los registros del historial con búsqueda, filtro por categoría y orden.
    Si el término es un número entero, también busca por ID exacto de log.
    """
    conn = get_connection()
    cursor = conn.cursor()

    condiciones = ["1=1"]
    params = []

    if categoria and categoria != "Todos":
        condiciones.append("categoria = ?")
        params.append(categoria)

    if texto_busqueda:
        t = texto_busqueda.strip()
        term = f"%{t.upper()}%"
        if t.isdigit():
            condiciones.append(
                "(id = ?"
                " OR UPPER(accion)      LIKE ?"
                " OR UPPER(referencia)  LIKE ?"
                " OR UPPER(responsable) LIKE ?"
                " OR UPPER(detalles)    LIKE ?)"
            )
            params.extend([int(t), term, term, term, term])
        else:
            condiciones.append(
                "(UPPER(accion)      LIKE ?"
                " OR UPPER(referencia)  LIKE ?"
                " OR UPPER(responsable) LIKE ?"
                " OR UPPER(detalles)    LIKE ?)"
            )
            params.extend([term, term, term, term])

    clausula_orden = ORDENES_VALIDOS.get(orden, "ORDER BY id DESC")
    query = (
        "SELECT id, accion, referencia, responsable, fecha, detalles "
        "FROM historial WHERE "
        + " AND ".join(condiciones)
        + f" {clausula_orden}"
    )

    cursor.execute(query, params)
    resultado = cursor.fetchall()
    conn.close()
    return resultado

       
