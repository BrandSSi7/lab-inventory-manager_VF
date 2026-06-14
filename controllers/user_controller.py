"""
controllers/user_controller.py
-------------------------------
Controlador de Usuarios. Intermediario entre la vista de gestión de personal
y el modelo user.py. Orquesta validaciones, persistencia y registro de auditoría.

Regla de oro: ninguna línea de este archivo toca CustomTkinter ni messagebox.

Autores: Equipo de Ingeniería Informática - 4to Semestre
Proyecto: Xorte - Lab Inventory Manager
"""

import models.user    as user_model
import models.history as history_model


class UserController:

    def __init__(self, auth_controller):
        # Referencia al controlador de sesión para saber quién ejecuta cada acción
        self.auth = auth_controller

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def obtener_usuarios(self, texto_busqueda: str = "") -> list:
        """Devuelve la lista de usuarios para poblar la tabla en la vista."""
        return user_model.obtener_todos(texto_busqueda)

    def obtener_nombres_para_combo(self) -> list[str]:
        """
        Devuelve solo los nombres de usuarios para el ComboBox de préstamos.
        Garantiza que el campo prestatario no sea texto libre.
        """
        return user_model.obtener_nombres_registrados()

    # ------------------------------------------------------------------
    # Creación
    # ------------------------------------------------------------------

    def registrar_usuario(self, datos: dict) -> tuple[bool, str]:
        """
        Recibe un diccionario con todos los campos del formulario de registro
        y los pasa al modelo para validación e inserción.

        Campos esperados en 'datos':
            nombres, cedula, fecha_nac, correo, telefono, username,
            password, q1, a1, q2, a2, q3, a3
        """
        exito, msg = user_model.crear_usuario(
            nom       = datos.get("nombres", ""),
            cedula    = datos.get("cedula", ""),
            fecha_nac = datos.get("fecha_nac", ""),
            correo    = datos.get("correo", ""),
            telefono  = datos.get("telefono", ""),
            username  = datos.get("username", ""),
            password  = datos.get("password", ""),
            q1        = datos.get("q1", ""),
            a1        = datos.get("a1", ""),
            q2        = datos.get("q2", ""),
            a2        = datos.get("a2", ""),
            q3        = datos.get("q3", ""),
            a3        = datos.get("a3", ""),
        )

        if exito:
            nombre_guardado = datos.get("nombres", "").strip().title()
            username_guardado = datos.get("username", "").strip().upper()
            history_model.registrar(
                accion="NUEVO USUARIO",
                referencia=f"PERFIL: {nombre_guardado}",
                responsable=self.auth.usuario_actual,
                detalles=f"Usuario registrado en el sistema. Login asignado: {username_guardado}.",
                categoria="Usuarios"
            )

        return exito, msg

    def registrar_usuario_rapido(self, nombre: str) -> tuple[bool, str]:
        """
        Alta express de un prestatario externo desde el módulo de préstamos.
        Devuelve (True, username_generado) o (False, "mensaje de error").
        """
        exito, resultado = user_model.crear_usuario_rapido(nombre)

        if exito:
            history_model.registrar(
                accion="ALTA RÁPIDA",
                referencia=f"PERFIL: {nombre.strip().title()}",
                responsable=self.auth.usuario_actual,
                detalles=f"Prestatario externo registrado. Login generado: {resultado}.",
                categoria="Usuarios"
            )

        return exito, resultado

    # ------------------------------------------------------------------
    # Actualización
    # ------------------------------------------------------------------

    def actualizar_usuario(self, id_usuario: int, datos: dict) -> tuple[bool, str]:
        """
        Actualiza los datos de perfil de un usuario existente.

        Campos esperados en 'datos':
            nombres, cedula, fecha_nac, correo, telefono, rol
        """
        exito, msg = user_model.actualizar_usuario(
            id_usuario = id_usuario,
            nom        = datos.get("nombres", ""),
            cedula     = datos.get("cedula", ""),
            fecha_nac  = datos.get("fecha_nac", ""),
            correo     = datos.get("correo", ""),
            telefono   = datos.get("telefono", ""),
            rol        = datos.get("rol", "PRESTATARIO EXTERNO"),
        )

        if exito:
            nombre = datos.get("nombres", "").strip().title()
            rol    = datos.get("rol", "")
            history_model.registrar(
                accion="EDICIÓN DE PERFIL",
                referencia=f"USUARIO: {nombre}",
                responsable=self.auth.usuario_actual,
                detalles=f"Datos actualizados. Rol asignado: {rol}.",
                categoria="Usuarios"
            )

        return exito, msg

    def resetear_password_usuario(self, id_usuario: int,
                                  password_temporal: str) -> tuple[bool, str]:
        """
        Permite a un Administrador restablecer la contraseña de otro usuario.
        Valida que quien ejecuta la acción tenga permisos de administrador.
        """
        if not self.auth.es_administrador():
            return False, "Solo un Administrador Ejecutivo puede resetear contraseñas."

        if not password_temporal or len(password_temporal.strip()) < 4:
            return False, "La contraseña temporal debe tener al menos 4 caracteres."

        username_afectado = user_model.obtener_username_por_id(id_usuario)
        user_model.resetear_password(id_usuario, password_temporal.strip())

        history_model.registrar(
            accion="RESET DE CONTRASEÑA",
            referencia=f"USUARIO: {username_afectado}",
            responsable=self.auth.usuario_actual,
            detalles=f"Clave restablecida por administrador. Clave temporal: {password_temporal.strip()}.",
            categoria="Usuarios"
        )
        return True, f"Contraseña restablecida. El usuario '{username_afectado}' deberá crear una nueva clave en su próximo ingreso."

    # ------------------------------------------------------------------
    # Eliminación
    # ------------------------------------------------------------------

    def eliminar_usuario(self, id_usuario: int) -> tuple[bool, str]:
        """
        Elimina un usuario del sistema. Solo disponible para Administradores.
        Devuelve (True, "mensaje de confirmación") o (False, "error").
        """
        if not self.auth.es_administrador():
            return False, "Solo un Administrador Ejecutivo puede eliminar usuarios del sistema."

        exito, nombre_o_error = user_model.eliminar_usuario(id_usuario)

        if exito:
            history_model.registrar(
                accion="ELIMINACIÓN",
                referencia=f"USUARIO: {nombre_o_error}",
                responsable=self.auth.usuario_actual,
                detalles="Ficha de usuario y accesos revocados del sistema.",
                categoria="Usuarios"
            )
            return True, f"El usuario '{nombre_o_error}' fue eliminado correctamente."

        return False, nombre_o_error
