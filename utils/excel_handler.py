"""
🔧 MANEJADOR DE EXCEL - Sistema de Inventario AGC
Funciones para importación/exportación de Excel
"""

import pandas as pd
import os
from datetime import datetime


def leer_excel_importacion(ruta_archivo):
    """Lee un archivo Excel para importación y valida su estructura"""
    try:
        df = pd.read_excel(ruta_archivo).fillna("")
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        
        # Validar columnas requeridas
        columnas_requeridas = {"ficha", "tipo", "marca", "modelo", "serie"}
        if not columnas_requeridas.issubset(set(df.columns)):
            return None, f"Faltan columnas requeridas: {columnas_requeridas}"
        
        return df, None
        
    except Exception as e:
        return None, f"Error leyendo archivo Excel: {e}"


def validar_fila_importacion(fila, indice):
    """Valida una fila individual de importación"""
    try:
        errores = []
        
        # Validar campos requeridos
        ficha = str(fila.get("ficha", "")).strip()
        tipo = str(fila.get("tipo", "")).strip()
        
        if not ficha:
            errores.append("Ficha vacía")
        if not tipo:
            errores.append("Tipo vacío")
            
        # Validar formato de ficha
        if ficha and not ficha.isdigit():
            errores.append("Ficha debe ser numérica")
            
        return errores
        
    except Exception as e:
        return [f"Error validando fila: {e}"]


def crear_plantilla_importacion():
    """Crea un DataFrame de plantilla para importación"""
    datos = {
        'ficha': ['1001', '1002', '1003'],
        'tipo': ['Oficina', 'Celular', 'Tablet'],
        'marca': ['Ejemplo', 'Ejemplo', 'Ejemplo'],
        'modelo': ['Modelo A', 'Modelo B', 'Modelo C'],
        'serie': ['SN001', 'SN002', 'SN003'],
        'estado': ['En depósito', 'Asignado', 'En depósito'],
        'nombre': ['Juan', 'María', 'Carlos'],
        'apellido': ['Pérez', 'Gómez', 'López'],
        'dni_cuit': ['20123456789', '27123456789', '23123456789'],
        'institucional': ['DIRECCION EJECUTIVA', 'AGENCIA GUBERNAMENTAL DE CONTROL', 'UNIDAD OPERATIVA'],
        'descripcion': ['Equipo oficina', 'Celular corporativo', 'Tablet inspecciones'],
        'prd': ['1234-2023', '1234-2023', '1234-2023'],
        'anio_prd': ['2023', '2023', '2023'],
        'monto_original': ['150000.50', '80000.00', '120000.00'],
        'linea': ['', '1112345678', ''],
        'sim': ['', 'SIM001', ''],
        'empresa': ['', 'Personal', ''],
        'imei': ['', '123456789012345', '']
    }
    
    return pd.DataFrame(datos)