
   """
controllers/asset_controller.py
--------------------------------
"""

import csv
from datetime import datetime, timedelta

import models.asset   as asset_model
import models.history as history_model


class AssetController:

    def __init__(self, auth_controller):
        self.auth = auth_controller

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def obtener_activos(self, texto_busqueda: str = "",
                        filtro_estado: str = "ALL") -> list:
        """Devuelve la lista de activos filtrada para poblar la tabla principal."""
        return asset_model.obtener_todos(texto_busqueda, filtro_estado)

    def obtener_activos_operativos(self) -> list:
        """
        Devuelve solo equipos operativos. Usado por el módulo de asignación
        para mostrar únicamente lo que se puede prestar.
        """
        return asset_model.obtener_operativos()

    def obtener_alarmas(self, texto_busqueda: str = "") -> list:
        """Devuelve los equipos con incidencias activas para el panel de alarmas."""
        return asset_model.obtener_alarmas(texto_busqueda)

    def obtener_custodio(self, serial: str) -> str:
        """Devuelve el nombre del responsable actual de un equipo."""
        return asset_model.obtener_custodio_actual(serial)

    # ------------------------------------------------------------------
    # Creación
    # ------------------------------------------------------------------

    def incorporar_activo(self, datos: dict) -> tuple[bool, str]:
        """
        Registra un nuevo activo tecnológico en el inventario.
        El modelo devuelve (False, mensaje) para cualquier error — nunca lanza excepciones.
        """
        exito, msg = asset_model.crear_activo(
            nombre        = datos.get("nombre", ""),
            marca         = datos.get("marca", ""),
            modelo        = datos.get("modelo", ""),
            serial        = datos.get("serial", ""),
            estado        = datos.get("estado", "OPERATIVO"),
            mantenimiento = datos.get("mantenimiento", ""),
        )

        if exito:
            serial = datos.get("serial", "").upper()
            nombre = datos.get("nombre", "").upper()
            marca  = datos.get("marca", "").upper()
            history_model.registrar(
                accion="INCORPORACIÓN",
                referencia=f"EQUIPO: {nombre}",
                responsable=self.auth.usuario_actual,
                detalles=f"Fabricante: {marca} | Serial: {serial} ingresado al inventario.",
                categoria="Equipos"
            )

        return exito, msg

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def cambiar_estado(self, id_activo: int,
                       nuevo_estado: str) -> tuple[bool, str]:
        """
        Cambia el estado operativo de un activo (Operativo, Mantenimiento, etc.).
        """
        exito, nombre_o_error = asset_model.actualizar_estado(id_activo, nuevo_estado)

        if exito:
            history_model.registrar(
                accion="ACTUALIZACIÓN DE ESTADO",
                referencia=f"EQUIPO: {nombre_o_error}",
                responsable=self.auth.usuario_actual,
                detalles=f"Estado modificado a: {nuevo_estado.upper()}.",
                categoria="Equipos"
            )
            return True, f"Estado actualizado a '{nuevo_estado}' correctamente."

        return False, nombre_o_error

    def resolver_alarma(self, id_activo: int, nueva_fecha: str,
                        nuevo_estado: str) -> tuple[bool, str]:
        """
        Atiende una incidencia de mantenimiento: actualiza fecha y estado del equipo.
        """
        exito, nombre_o_error = asset_model.resolver_alarma(
            id_activo, nueva_fecha, nuevo_estado
        )

        if exito:
            history_model.registrar(
                accion="RESOLUCIÓN DE INCIDENCIA",
                referencia=f"EQUIPO: {nombre_o_error}",
                responsable=self.auth.usuario_actual,
                detalles=f"Mantenimiento atendido. Nueva revisión: {nueva_fecha} | Estado: {nuevo_estado}.",
                categoria="Equipos"
            )
            return True, "Incidencia resuelta y equipo actualizado correctamente."

        return False, nombre_o_error

    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------

    def eliminar_activo(self, id_activo: int) -> tuple[bool, str]:
        """Elimina un activo del inventario. Solo para Administradores."""
        if not self.auth.es_administrador():
            return False, "Solo un Administrador Ejecutivo puede eliminar activos del inventario."

        exito, descripcion_o_error = asset_model.eliminar_activo(id_activo)

        if exito:
            history_model.registrar(
                accion="ELIMINACIÓN",
                referencia=f"ACTIVO: {descripcion_o_error}",
                responsable=self.auth.usuario_actual,
                detalles="Activo removido permanentemente del inventario.",
                categoria="Equipos"
            )
            return True, f"Activo '{descripcion_o_error}' eliminado del inventario."

        return False, descripcion_o_error

    # ------------------------------------------------------------------
    # Importación masiva CSV
    # ------------------------------------------------------------------

    def importar_desde_csv(self, filepath: str) -> tuple[bool, str]:
        """
        Lee un archivo CSV e intenta incorporar cada fila como un nuevo activo.
        Formato esperado de columnas (con o sin encabezado):
            id | nombre | marca | modelo | serial | estado | mantenimiento

        Devuelve (True, "resumen") con conteo de éxitos y errores.
        """
        if not filepath:
            return False, "No se seleccionó ningún archivo."

        exitos  = 0
        errores = 0
        fecha_mant_default = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")

        try:
            with open(filepath, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f, delimiter=";")
                next(reader, None)  # Saltar encabezado si existe

                for fila in reader:
                    # Filtramos filas vacías o con menos columnas de las esperadas
                    if not fila or len(fila) < 5:
                        errores += 1
                        continue

                    datos = {
                        "nombre":       fila[1].strip() if len(fila) > 1 else "",
                        "marca":        fila[2].strip() if len(fila) > 2 else "",
                        "modelo":       fila[3].strip() if len(fila) > 3 else "",
                        "serial":       fila[4].strip() if len(fila) > 4 else "",
                        "estado":       fila[5].strip() if len(fila) > 5 else "OPERATIVO",
                        "mantenimiento": fila[6].strip() if len(fila) > 6 else fecha_mant_default,
                    }

                    exito, _ = self.incorporar_activo(datos)
                    if exito:
                        exitos += 1
                    else:
                        errores += 1

        except FileNotFoundError:
            return False, "No se encontró el archivo seleccionado."
        except Exception as e:
            return False, f"Error al leer el archivo CSV: {e}"

        history_model.registrar(
            accion="IMPORTACIÓN MASIVA CSV",
            referencia="MÓDULO: EQUIPOS",
            responsable=self.auth.usuario_actual,
            detalles=f"Importación completada. Éxitos: {exitos} | Ignorados/Duplicados: {errores}.",
            categoria="Sistema"
        )

        resumen = (
            f"Importación finalizada.\n\n"
            f"✔ Activos incorporados: {exitos}\n"
            f"✘ Filas ignoradas (duplicadas o incompletas): {errores}"
        )
        return True, resumen
