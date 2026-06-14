"""
controllers/history_controller.py
----------------------------------
Controlador del Historial de Auditoría. Su único trabajo es consultar
y filtrar los registros del historial para la vista correspondiente.

Como el historial es de solo lectura para el usuario final,
este controlador no tiene operaciones de escritura.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import models.history as history_model


class HistoryController:

    def __init__(self, auth_controller):
        self.auth = auth_controller

    def obtener_historial(self, texto_busqueda: str = "",
                          categoria: str = "Todos",
                          orden: str = "Más Recientes") -> list:
        """
        Devuelve los registros del historial según los filtros activos en la vista.
        El parámetro 'categoria' corresponde al valor del SegmentedButton de la vista.
        """
        return history_model.obtener_todos(texto_busqueda, categoria, orden)
