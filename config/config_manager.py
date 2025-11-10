"""
⚙️ GESTOR DE CONFIGURACIÓN - Sistema de Inventario AGC
VERSIÓN MEJORADA con rutas relativas y migración segura
"""

import json
import os
from pathlib import Path
from datetime import datetime

# ✅ FUNCIÓN PARA RUTAS RELATIVAS
def _obtener_ruta_base():
    """Obtiene la ruta base de la aplicación"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✅ MANTENEMOS compatibilidad con estructura vieja
CONFIG_DEFAULT_LEGACY = {
    "modo_local": False,
    "db_path_local": os.path.join(_obtener_ruta_base(), "inventario_local.db"),
    "actas_folder_local": os.path.join(_obtener_ruta_base(), "actas_local"), 
    "db_path_red": "M:\\Patrimonio\\01 PATRIMONIO\\InventarioApp\\inventario.db",
    "actas_folder_red": "M:\\Patrimonio\\01 PATRIMONIO\\InventarioApp\\actas"
}

# ✅ AGREGAMOS nuevos campos para arquitectura profesional
CONFIG_DEFAULT_PRO = {
    # Campos legacy (compatibilidad)
    **CONFIG_DEFAULT_LEGACY,
    
    # ✅ NUEVOS CAMPOS
    "modo_trabajo": "local_con_sincronizacion",  # local_con_sincronizacion, red_directo, local_solo
    "db_maestra_red": "M:\\Patrimonio\\01 PATRIMONIO\\InventarioApp\\inventario.db",
    "db_cache_local": os.path.join(_obtener_ruta_base(), "inventario_cache.db"),
    
    # Configuración de sincronización
    "auto_sincronizar": True,
    "intervalo_sincronizacion": 300,
    "ultima_sincronizacion": None,
    "usuario_actual": "",
    
    # Control de conflictos
    "notificar_conflictos": True,
    "resolucion_automatica": False,
    
    # Backup automático
    "backup_automatico": True,
    "max_backups": 10
}

def cargar_configuracion():
    """Carga la configuración con migración automática"""
    config_file = _obtener_ruta_config()
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ Configuración cargada (modo migración)")
                
                # ✅ MIGRACIÓN AUTOMÁTICA: Si es configuración vieja, la actualizamos
                return _migrar_configuracion_si_es_necesario(config)
        else:
            # Crear archivo con valores por defecto PRO
            guardar_configuracion(CONFIG_DEFAULT_PRO)
            print("🆕 Archivo de configuración PROFESIONAL creado")
            return CONFIG_DEFAULT_PRO
            
    except Exception as e:
        print(f"⚠️ Error cargando configuración: {e}")
        return CONFIG_DEFAULT_PRO

def _migrar_configuracion_si_es_necesario(config):
    """Migra configuración antigua a nueva estructura si es necesario"""
    
    # ✅ DETECTAR si es configuración VIEJA (sin modo_trabajo)
    if "modo_trabajo" not in config:
        print("🔄 Detectada configuración LEGACY - Iniciando migración...")
        
        # 1. Determinar modo_trabajo basado en modo_local
        if config.get("modo_local", False):
            config["modo_trabajo"] = "local_solo"
        else:
            config["modo_trabajo"] = "red_directo"
        
        # 2. Mapear rutas legacy a nuevas rutas
        config["db_maestra_red"] = config.get("db_path_red", CONFIG_DEFAULT_PRO["db_maestra_red"])
        config["db_cache_local"] = config.get("db_path_local", CONFIG_DEFAULT_PRO["db_cache_local"])
        
        # 3. Agregar nuevos campos con valores por defecto
        nuevos_campos = {k: v for k, v in CONFIG_DEFAULT_PRO.items() if k not in config}
        config.update(nuevos_campos)
        
        # 4. Guardar configuración migrada
        guardar_configuracion(config)
        print("✅ Migración completada a configuración PROFESIONAL")
    
    # ✅ ASEGURAR que todos los campos existan
    for key, value in CONFIG_DEFAULT_PRO.items():
        if key not in config:
            config[key] = value
            print(f"⚠️ Campo faltante agregado: {key}")
    
    return config

def guardar_configuracion(config):
    """Guarda la configuración manteniendo compatibilidad"""
    config_file = _obtener_ruta_config()
    
    try:
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("💾 Configuración guardada (compatible)")
        return True
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False

def _obtener_ruta_config():
    """Obtiene la ruta del archivo de configuración (MISMO ARCHIVO)"""
    base_dir = Path(__file__).parent.parent
    return base_dir / "config_modo.json"  # ✅ MANTENEMOS EL MISMO NOMBRE

# ✅ FUNCIONES DE CONVENIENCIA
def es_modo_sincronizacion_activo():
    config = cargar_configuracion()
    return config["modo_trabajo"] == "local_con_sincronizacion"

def obtener_ruta_db_activa():
    config = cargar_configuracion()
    
    if config["modo_trabajo"] == "local_con_sincronizacion":
        return config["db_cache_local"]
    elif config["modo_trabajo"] == "red_directo":
        return config["db_maestra_red"]
    else:  # local_solo
        return config["db_cache_local"]

def obtener_ruta_db_maestra():
    config = cargar_configuracion()
    return config["db_maestra_red"]

def actualizar_ultima_sincronizacion():
    config = cargar_configuracion()
    config["ultima_sincronizacion"] = datetime.now().isoformat()
    guardar_configuracion(config)
    print("🕒 Marca de sincronización actualizada")

# ✅ NUEVA FUNCIÓN QUE FALTABA
def obtener_estado_sincronizacion():
    """Obtiene el estado actual de sincronización"""
    config = cargar_configuracion()
    return {
        "modo_trabajo": config["modo_trabajo"],
        "auto_sincronizar": config["auto_sincronizar"],
        "ultima_sincronizacion": config["ultima_sincronizacion"],
        "usuario_actual": config["usuario_actual"]
    }