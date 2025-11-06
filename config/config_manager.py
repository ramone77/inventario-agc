"""
⚙️ GESTOR DE CONFIGURACIÓN - Sistema de Inventario AGC
Maneja la configuración LOCAL/RED desde archivo JSON
"""

import json
import os
from pathlib import Path


# Configuración por defecto
CONFIG_DEFAULT = {
    "modo_local": False,
    "db_path_local": "C:\\InventarioApp\\inventario_local.db",
    "actas_folder_local": "C:\\InventarioApp\\actas_local", 
    "db_path_red": "M:\\Patrimonio\\01 PATRIMONIO\\InventarioApp\\inventario.db",
    "actas_folder_red": "M:\\Patrimonio\\01 PATRIMONIO\\InventarioApp\\actas"
}


def cargar_configuracion():
    """Carga la configuración desde archivo JSON"""
    config_file = _obtener_ruta_config()
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ Configuración cargada desde archivo")
                return config
        else:
            # Crear archivo con valores por defecto
            guardar_configuracion(CONFIG_DEFAULT)
            print("🆕 Archivo de configuración creado con valores por defecto")
            return CONFIG_DEFAULT
    except Exception as e:
        print(f"⚠️ Error cargando configuración: {e}")
        return CONFIG_DEFAULT


def guardar_configuracion(config):
    """Guarda la configuración en archivo JSON"""
    config_file = _obtener_ruta_config()
    
    try:
        # Crear directorio si no existe
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("💾 Configuración guardada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False


def _obtener_ruta_config():
    """Obtiene la ruta del archivo de configuración"""
    base_dir = Path(__file__).parent.parent  # Sube dos niveles desde config/
    return base_dir / "config_modo.json"


def obtener_configuracion_actual():
    """Obtiene la configuración actual con valores por defecto"""
    config = cargar_configuracion()
    
    # Asegurar que todos los campos existan
    for key, value in CONFIG_DEFAULT.items():
        if key not in config:
            config[key] = value
    
    return config