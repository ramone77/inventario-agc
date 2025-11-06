"""
⚙️ CONFIGURACIÓN GLOBAL - Sistema de Inventario AGC
Variables globales y constantes de la aplicación
"""

from .config_manager import obtener_configuracion_actual
import os


# Cargar configuración actual
config_actual = obtener_configuracion_actual()

# Variables globales
MODO_LOCAL = config_actual["modo_local"]
DB_PATH = config_actual["db_path_local"] if MODO_LOCAL else config_actual["db_path_red"]  
ACTAS_FOLDER = config_actual["actas_folder_local"] if MODO_LOCAL else config_actual["actas_folder_red"]

# Crear carpetas necesarias
try:
    os.makedirs(config_actual["actas_folder_local"], exist_ok=True)
    if not MODO_LOCAL:
        try:
            os.makedirs(ACTAS_FOLDER, exist_ok=True)
        except:
            pass
except Exception as e:
    print(f"⚠️ No se pudo crear carpeta de actas: {e}")

# Información del sistema
print(f"📍 Directorio base: {os.path.dirname(__file__)}")
print(f"🗃️ Base de datos: {DB_PATH}")
print(f"📁 Carpeta actas: {ACTAS_FOLDER}") 
print(f"🔧 Modo: {'LOCAL (Pruebas)' if MODO_LOCAL else 'RED (Producción)'}")