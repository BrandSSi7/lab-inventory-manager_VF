"""
controllers/history_controller.py
----------------------------------
Controlador del Historial de Auditoría.

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
