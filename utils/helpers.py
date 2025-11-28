"""
🔧 HELPERS Y FUNCIONES AUXILIARES - Sistema de Inventario AGC
Funciones de utilidad para todo el sistema
"""

import pandas as pd
from datetime import datetime


def safe_get(data, key, default=""):
    """Obtiene valores de forma segura desde diccionarios o objetos"""
    try:
        if hasattr(data, '__getitem__'):
            value = data[key]
            return str(value) if value is not None else default
        else:
            value = getattr(data, key, default)
            return str(value) if value is not None else default
    except (KeyError, IndexError, AttributeError):
        return default


def formatear_fecha_argentina(fecha_str):
    """Convierte fecha de BD a formato argentino DD/MM/AAAA"""
    try:
        # Intentar formato YYYY-MM-DD
        fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        return fecha_dt.strftime("%d/%m/%Y")
    except:
        try:
            # Intentar otro formato si falla
            fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return fecha_dt.strftime("%d/%m/%Y")
        except:
            return fecha_str  # Devolver original si no se puede parsear


def validar_ficha(ficha):
    """Valida que la ficha sea un número válido"""
    try:
        return str(ficha).strip().isdigit()
    except:
        return False


def validar_imei(imei):
    """Valida que el IMEI tenga 15 dígitos"""
    try:
        imei_clean = str(imei).strip()
        return len(imei_clean) == 15 and imei_clean.isdigit()
    except:
        return False


def exportar_dataframe_excel(df, titulo_archivo):
    """Exporta un DataFrame a Excel con nombre automático"""
    try:
        nombre_archivo = f"{titulo_archivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
        df.to_excel(nombre_archivo, index=False)
        return nombre_archivo
    except Exception as e:
        print(f"❌ Error exportando a Excel: {e}")
        return None


def crear_backup_automatico(db_path):
    """Crea un backup automático de la base de datos"""
    import shutil
    import os
    from datetime import datetime
    
    try:
        # Crear carpeta de backups si no existe
        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nombre del archivo con fecha/hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"inventario_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Crear backup
        shutil.copy2(db_path, backup_path)
        
        print(f"✅ Backup creado: {backup_name}")
        return backup_path
    except Exception as e:
        print(f"❌ Error en backup automático: {e}")
        return None