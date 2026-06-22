# Lab-Inventory Manager

Sistema de gestión de inventario para UNEXCA desarrollado bajo una arquitectura **MVC (Modelo-Vista-Controlador)** robusta, diseñada para garantizar la escalabilidad, mantenibilidad y seguridad de los activos tecnológicos.

## Arquitectura del Sistema
El proyecto está estructurado para separar estrictamente las responsabilidades:
- **Models:** Lógica de negocio, validaciones y acceso a datos (SQLite).
- **Controllers:** Gestión de flujo y comunicación entre modelos y vistas.
- **Views:** Interfaz de usuario moderna basada en `customtkinter`.

## Equipo de Desarrollo
Este sistema es el resultado de un esfuerzo conjunto bajo un modelo de desarrollo modular:

| Desarrollador | Responsabilidades |
| :--- | :--- |
| **Brandon Pérez** | Arquitectura MVC, Capa de Autenticación y Ensamble del Core. |
| **Andrea Useche** | Lógica de negocio para Préstamos y Gestión de Activos. |
| **Edwin Urbina** | Diseño de Vistas de Usuario y optimización de formularios (UX). |
| **Yorman Blanco** | Sistema de Auditoría (Logs) y Gestión de Incidencias/Alarmas. |

## Instalación y Ejecución

1. **Requisitos:**
   - Python 3.10 o superior.
   - Instalar las dependencias necesarias:
     ```bash
     pip install customtkinter
     ```

2. **Ejecución:**
   Ubicado en la carpeta raíz del proyecto, ejecuta:
   ```bash
   python main.py
