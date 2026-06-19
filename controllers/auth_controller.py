"""
controllers/auth_controller.py
-------------------------------
Controlador de Autenticación. Gestiona el ciclo completo de sesión:
login, cambio de contraseña obligatorio y cierre de sesión.

No importa ni usa ningún widget de interfaz gráfica.
Devuelve tuplas (bool, str) que la Vista interpreta y muestra al usuario.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import models.user as user_model
import models.history as history_model


class AuthController:
    """
    Mantiene el estado de la sesión activa: usuario logueado y su rol.
    Una sola instancia de esta clase viaja de la LoginView al DashboardView.
    """

    def __init__(self):
        self.usuario_actual = "SISTEMA"
        self.rol_actual = ""
        
    # ------------------------------------------------------------------
    # Autenticación
    # ------------------------------------------------------------------

    def intentar_login(self, username: str, password: str) -> tuple[bool, str]:
        """
        Valida las credenciales contra la base de datos.

        Devuelve:
            (True,  "CAMBIO_REQUERIDO") si el login es correcto pero hay que cambiar clave.
            (True,  "OK")               si el login es correcto y puede entrar directo.
            (False, "mensaje de error") si las credenciales son incorrectas.
        """
        username = username.strip().upper()

        if not username or not password:
            return False, "Debe ingresar su nombre de usuario y contraseña."

        if not user_model.validar_login(username, password):
            return False, "El nombre de usuario o la contraseña son incorrectos."

        # Guardar el estado de sesión en el controlador
        self.usuario_actual = username
        self.rol_actual = user_model.obtener_rol(username)

        if user_model.necesita_cambio_password(username):
            return True, "CAMBIO_REQUERIDO"

        history_model.registrar(
            accion="INICIO SESIÓN",
            referencia="Módulo de Autenticación",
            responsable=self.usuario_actual,
            detalles="Ingreso autorizado al panel de control.",
            categoria="Sistema"
        )
        return True, "OK"

    def cambiar_password(self, nueva_password: str,
                         confirmacion: str) -> tuple[bool, str]:
        """
        Cambia la contraseña del usuario de sesión activa.
        Valida coincidencia Y fortaleza antes de delegar al modelo.
        """
        nueva_password = nueva_password.strip()
        confirmacion   = confirmacion.strip()

        if nueva_password != confirmacion:
            return False, "Las contraseñas no coinciden. Inténtelo de nuevo."

        # Validación de fortaleza en el Controlador (no solo en el Modelo)
        import re
        patron = re.compile(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')
        if not patron.match(nueva_password):
            return False, (
                "La contraseña debe tener mínimo 8 caracteres e incluir "
                "al menos una letra, un número y un carácter especial (ej: @, #, !, %)."
            )

        exito, msg = user_model.cambiar_password(self.usuario_actual, nueva_password)
        if not exito:
            return False, msg

        history_model.registrar(
            accion="CAMBIO DE CONTRASEÑA",
            referencia=f"USUARIO: {self.usuario_actual}",
            responsable=self.usuario_actual,
            detalles="Contraseña personal actualizada en el primer inicio de sesión.",
            categoria="Sistema"
        )
        return True, "OK"

    def cerrar_sesion(self) -> None:
        """Registra el cierre de sesión y limpia el estado del controlador."""
        history_model.registrar(
            accion="CIERRE SESIÓN",
            referencia="Módulo de Autenticación",
            responsable=self.usuario_actual,
            detalles="Cierre de sesión manual del operador.",
            categoria="Sistema"
        )
        self.usuario_actual = "SISTEMA"
        self.rol_actual = ""

    # ------------------------------------------------------------------
    # Recuperación de contraseña
    # ------------------------------------------------------------------

    def buscar_cuenta_recuperacion(self, busqueda: str):
        """
        Busca un usuario por username o correo para iniciar la recuperación.
        Devuelve la fila completa del usuario o None si no existe.
        """
        if not busqueda.strip():
            return None
        return user_model.buscar_por_username_o_correo(busqueda.strip())

    def verificar_respuestas_seguridad(self, usuario_fila: tuple,
                                       r1: str, r2: str, r3: str) -> tuple[bool, str]:
        """
        Compara las respuestas ingresadas con las almacenadas en la BD.
        Si son correctas, devuelve la contraseña actual para mostrársela al usuario.

        Índices de la fila de usuario:
            [8]  = password, [9] = q1, [10] = a1,
            [11] = q2,       [12] = a2,
            [13] = q3,       [14] = a3
        """
        a1_bd = usuario_fila[10].upper() if usuario_fila[10] else ""
        a2_bd = usuario_fila[12].upper() if usuario_fila[12] else ""
        a3_bd = usuario_fila[14].upper() if usuario_fila[14] else ""

        if r1.strip().upper() == a1_bd \
                and r2.strip().upper() == a2_bd \
                and r3.strip().upper() == a3_bd:

            history_model.registrar(
                accion="RECUPERACIÓN DE CUENTA",
                referencia=f"USUARIO: {usuario_fila[6]}",
                responsable="SISTEMA",
                detalles="Recuperación exitosa mediante preguntas de seguridad.",
                categoria="Sistema"
            )
            return True, usuario_fila[8]   # Devuelve la contraseña actual

        history_model.registrar(
            accion="ALERTA DE SEGURIDAD",
            referencia=f"INTENTO FALLIDO: {usuario_fila[6]}",
            responsable="SISTEMA",
            detalles="Respuestas de seguridad incorrectas en intento de recuperación.",
            categoria="Sistema"
        )
        return False, "Una o más respuestas no coinciden con los registros del sistema."

    # ------------------------------------------------------------------
    # Helpers de sesión (usados por la Vista para adaptar la UI al rol)
    # ------------------------------------------------------------------

    def es_administrador(self) -> bool:
        """Devuelve True si el usuario activo tiene rol de Administrador Ejecutivo."""
        return "ADMINISTRADOR" in self.rol_actual.upper()

    def es_operador(self) -> bool:
        """Devuelve True si el usuario activo es Operador de Laboratorio o superior."""
        return "OPERADOR" in self.rol_actual.upper() or self.es_administrador()
