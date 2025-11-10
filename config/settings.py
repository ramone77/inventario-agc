"""
⚙️ CONFIGURACIÓN GLOBAL PROFESIONAL - Sistema de Inventario AGC
Nueva arquitectura con funciones dinámicas
"""

from .config_manager import (
    cargar_configuracion, 
    obtener_ruta_db_activa,
    obtener_ruta_db_maestra,
    es_modo_sincronizacion_activo,
    obtener_estado_sincronizacion
)
import os

# ✅ ELIMINADO: Variables globales estáticas
# ✅ NUEVO: Funciones dinámicas que siempre obtienen valores actuales

def get_config():
    """Obtiene configuración ACTUAL (siempre fresca)"""
    return cargar_configuracion()

def get_db_path():
    """Obtiene ruta de BD activa según modo actual"""
    return obtener_ruta_db_activa()

def get_db_maestra_path():
    """Obtiene ruta de BD maestra en red"""
    return obtener_ruta_db_maestra()

def get_actas_folder():
    """Obtiene carpeta de actas según modo actual"""
    config = get_config()
    if es_modo_sincronizacion_activo():
        return config["actas_folder_local"]
    else:
        return config["actas_folder_red"]

def get_modo_trabajo():
    """Obtiene el modo de trabajo actual"""
    config = get_config()
    return config["modo_trabajo"]

def get_info_sistema():
    """Obtiene información completa del sistema"""
    config = get_config()
    return {
        "modo_trabajo": config["modo_trabajo"],
        "db_activa": get_db_path(),
        "db_maestra": get_db_maestra_path(),
        "carpeta_actas": get_actas_folder(),
        "auto_sincronizar": config["auto_sincronizar"],  # ✅ CORREGIDO: sin 'n' al final
        "usuario": config["usuario_actual"],
        "ultima_sincronizacion": config["ultima_sincronizacion"]
    }

# ✅ NUEVO: Crear carpetas necesarias al inicio
def inicializar_directorios():
    """Crea las carpetas necesarias para el sistema"""
    config = get_config()
    
    try:
        # Crear carpeta local de actas
        os.makedirs(config["actas_folder_local"], exist_ok=True)
        
        # Crear carpeta de backups local
        backup_dir = os.path.join(os.path.dirname(config["db_cache_local"]), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Intentar crear carpeta de red (si existe el acceso)
        if es_modo_sincronizacion_activo() or get_modo_trabajo() == "red_directo":
            try:
                os.makedirs(config["actas_folder_red"], exist_ok=True)
            except:
                print("⚠️ No se pudo acceder a carpeta de red")
                
        print("✅ Directorios del sistema inicializados")
        
    except Exception as e:
        print(f"❌ Error inicializando directorios: {e}")

# ✅ Inicializar al importar el módulo
inicializar_directorios()

# ✅ Información del sistema al iniciar
info = get_info_sistema()
print(f"🏢 SISTEMA INVENTARIO AGC - ARQUITECTURA PROFESIONAL")
print(f"📍 Modo: {info['modo_trabajo']}")
print(f"🗃️ BD Activa: {os.path.basename(info['db_activa'])}")
print(f"🌐 BD Maestra: {os.path.basename(info['db_maestra'])}")
print(f"👤 Usuario: {info['usuario']}")