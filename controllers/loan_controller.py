"""
controllers/loan_controller.py
-------------------------------
Controlador de Préstamos. Gestiona el ciclo completo de asignación:
registro de nuevos préstamos, modificaciones, devoluciones y eliminaciones.

Coordina los modelos loan.py, asset.py (para actualizar estados del equipo)
y history.py (para auditoría).

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import models.loan    as loan_model
import models.history as history_model


class LoanController:

    def __init__(self, auth_controller):
        self.auth = auth_controller

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def obtener_prestamos(self, texto_busqueda: str = "",
                          filtro_estado: str = "ALL") -> list:
        """
        Devuelve la lista de préstamos para la tabla de trazabilidad.
        El parámetro texto_busqueda ahora filtra también por fecha y serial.
        """
        return loan_model.obtener_todos(texto_busqueda, filtro_estado)

    # ------------------------------------------------------------------
    # Creación
    # ------------------------------------------------------------------

    def registrar_prestamo(self, datos: dict) -> tuple[bool, str]:
        """
        Procesa una nueva asignación de préstamo.

        Campos esperados en 'datos':
            id_activo, prestatario, fecha_prestamo, fecha_devolucion, ubicacion

        El prestatario debe venir de un ComboBox, no de texto libre.
        El controlador lo valida también aquí como segunda línea de defensa.
        """
        prestatario = datos.get("prestatario", "").strip()
        if not prestatario:
            return False, "Debe seleccionar un prestatario válido de la lista desplegable."

        id_activo = datos.get("id_activo")
        if not id_activo:
            return False, "Debe seleccionar un equipo de la tabla de activos operativos."

        exito, nombre_o_error = loan_model.registrar_prestamo(
            id_activo        = id_activo,
            prestatario      = prestatario,
            fecha_prestamo   = datos.get("fecha_prestamo", ""),
            fecha_devolucion = datos.get("fecha_devolucion", ""),
            ubicacion        = datos.get("ubicacion", ""),
        )

        if exito:
            history_model.registrar(
                accion="ASIGNACIÓN DE PRÉSTAMO",
                referencia=f"EQUIPO: {nombre_o_error}",
                responsable=self.auth.usuario_actual,
                detalles=(
                    f"Asignado a: {prestatario.upper()} | "
                    f"Devolución: {datos.get('fecha_devolucion', '')} | "
                    f"Ubicación: {datos.get('ubicacion', '').upper()}."
                ),
                categoria="Préstamos"
            )
            return True, f"Préstamo de '{nombre_o_error}' registrado exitosamente."

        return False, nombre_o_error

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def modificar_prestamo(self, id_prestamo: int,
                           nueva_fecha_devolucion: str,
                           nuevo_estado: str) -> tuple[bool, str]:
        """
        Modifica la fecha de devolución y/o el estado de un préstamo activo.
        """
        exito, nombre_o_error = loan_model.actualizar_prestamo(
            id_prestamo,
            nueva_fecha_devolucion,
            nuevo_estado
        )

        if exito:
            history_model.registrar(
                accion="MODIFICACIÓN DE PRÉSTAMO",
                referencia=f"PRÉSTAMO ID: {id_prestamo}",
                responsable=self.auth.usuario_actual,
                detalles=(
                    f"Equipo: {nombre_o_error} | "
                    f"Nueva devolución: {nueva_fecha_devolucion} | "
                    f"Estado: {nuevo_estado.upper()}."
                ),
                categoria="Préstamos"
            )
            return True, "Préstamo actualizado correctamente."

        return False, nombre_o_error

    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------

    def eliminar_prestamo(self, id_prestamo: int) -> tuple[bool, str]:
        """
        Elimina el registro de un préstamo. Requiere confirmación previa en la Vista.
        Solo disponible para Administradores y Operadores.
        """
        if not self.auth.es_operador():
            return False, "No tiene permisos suficientes para eliminar registros de préstamos."

        exito, descripcion_o_error = loan_model.eliminar_prestamo(id_prestamo)

        if exito:
            history_model.registrar(
                accion="ELIMINACIÓN",
                referencia=f"PRÉSTAMO ID: {id_prestamo}",
                responsable=self.auth.usuario_actual,
                detalles=f"Registro eliminado: {descripcion_o_error}.",
                categoria="Préstamos"
            )
            return True, "Registro de préstamo eliminado correctamente."

        return False, descripcion_o_error
