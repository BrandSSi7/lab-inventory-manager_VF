import os
import shutil

directorio_base = os.path.dirname(os.path.abspath(__file__))

carpetas = ['models', 'controllers', 'views']

mapa_archivos = {
    'models': ['user.py', 'asset.py', 'loan.py', 'history.py'],
    'controllers': [
        'auth_controller.py', 'user_controller.py', 
        'asset_controller.py', 'loan_controller.py', 'history_controller.py'
    ],
    'views': [
        'theme.py', 'login_view.py', 'register_user_view.py', 
        'dashboard_view.py', 'asset_module.py', 'loan_module.py', 
        'assign_module.py', 'alarm_module.py', 'user_module.py', 'history_module.py'
    ]
}

print("Iniciando construcción de la Catedral Digital...\n")

for carpeta in carpetas:
    ruta_carpeta = os.path.join(directorio_base, carpeta)
    os.makedirs(ruta_carpeta, exist_ok=True)
    open(os.path.join(ruta_carpeta, '__init__.py'), 'a').close()
    print(f"Carpeta y módulo listos: {carpeta}/")

print("-" * 40)

archivos_movidos = 0
for carpeta, lista in mapa_archivos.items():
    ruta_carpeta = os.path.join(directorio_base, carpeta)
    for archivo in lista:
        ruta_origen = os.path.join(directorio_base, archivo)
        ruta_destino = os.path.join(ruta_carpeta, archivo)
        
        if os.path.exists(ruta_origen):
            shutil.move(ruta_origen, ruta_destino)
            print(f"Movido: {archivo}  -->  {carpeta}/")
            archivos_movidos += 1
        else:
            print(f"No encontrado: {archivo}")

print("-" * 40)
print(f"Estructura MVC completada! Se movieron {archivos_movidos} archivos.")
