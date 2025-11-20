def analizar_excel_con_errores(ruta_archivo):
    """
    Analiza el Excel separando registros válidos y conflictivos.
    Devuelve: (df_validos, df_errores, resumen)
    df_validos: DataFrame con registros listos para importar
    df_errores: DataFrame con registros rechazados y motivo
    resumen: dict con conteo y detalles
    """
    import pandas as pd

    df = pd.read_excel(ruta_archivo)
    errores = []
    validos = []

    # Validar duplicados de ficha
    fichas_duplicadas = df[df.duplicated('ficha', keep=False)]['ficha'].unique().tolist()
    series_duplicadas = df[df['serie'].notna() & (df['serie'] != '') & (~df['serie'].astype(str).str.upper().isin(['SIN SERIE', 'S/N', 'N/A']))]
    series_duplicadas = series_duplicadas[series_duplicadas.duplicated('serie', keep=False)]['serie'].unique().tolist()
    imeis_duplicados = df[df['imei'].notna() & (df['imei'] != '') & (df['imei'] != '0') & (~df['imei'].astype(str).str.upper().isin(['N/A', 'NA']))]
    imeis_duplicados = imeis_duplicados[imeis_duplicados.duplicated('imei', keep=False)]['imei'].unique().tolist()



    # Agrupar por ficha y elegir el registro más completo
    ficha_grupos = {}
    for idx, row in df.iterrows():
        ficha_val = str(row.get('ficha', '')).strip()
        if ficha_val:
            ficha_grupos.setdefault(ficha_val, []).append((idx, row))
        else:
            # Fichas vacías se tratan como error
            motivo = ['Ficha vacía']
            if not str(row.get('tipo', '')).strip():
                motivo.append('Tipo vacío')
            row_dict = row.to_dict()
            row_dict['Motivo de rechazo'] = ", ".join(motivo)
            errores.append(row_dict)

    for ficha, registros in ficha_grupos.items():
        # Elegir el registro más completo (más campos no vacíos)
        def count_nonempty(row):
            return sum(bool(str(row.get(col, '')).strip()) for col in df.columns if col not in ['Motivo de rechazo'])
        registros_ordenados = sorted(registros, key=lambda x: count_nonempty(x[1]), reverse=True)
        idx_valido, row_valido = registros_ordenados[0]
        motivo_valido = []
        # Validar serie e imei duplicados
        if row_valido.get('serie') and str(row_valido.get('serie')).strip() in series_duplicadas:
            motivo_valido.append('Serie duplicada en Excel')
        if row_valido.get('imei') and str(row_valido.get('imei')).strip() in imeis_duplicados:
            motivo_valido.append('IMEI duplicado en Excel')
        if not str(row_valido.get('tipo', '')).strip():
            motivo_valido.append('Tipo vacío')
        if motivo_valido:
            row_dict = row_valido.to_dict()
            row_dict['Motivo de rechazo'] = ", ".join(motivo_valido)
            errores.append(row_dict)
        else:
            validos.append(row_valido)
        # Los demás duplicados se reportan como error
        for idx_dup, row_dup in registros_ordenados[1:]:
            motivo = ['Ficha duplicada en Excel']
            if row_dup.get('serie') and str(row_dup.get('serie')).strip() in series_duplicadas:
                motivo.append('Serie duplicada en Excel')
            if row_dup.get('imei') and str(row_dup.get('imei')).strip() in imeis_duplicados:
                motivo.append('IMEI duplicado en Excel')
            if not str(row_dup.get('tipo', '')).strip():
                motivo.append('Tipo vacío')
            row_dict = row_dup.to_dict()
            row_dict['Motivo de rechazo'] = ", ".join(motivo)
            errores.append(row_dict)

    df_validos = pd.DataFrame(validos) if validos else pd.DataFrame(columns=df.columns)
    df_errores = pd.DataFrame(errores) if errores else pd.DataFrame(columns=list(df.columns) + ['Motivo de rechazo'])

    resumen = {
        'total_registros': len(df),
        'total_validos': len(df_validos),
        'total_errores': len(df_errores),
        'fichas_duplicadas': fichas_duplicadas,
        'series_duplicadas': series_duplicadas,
        'imeis_duplicados': imeis_duplicados
    }
    return df_validos, df_errores, resumen
"""
🔧 MANEJADOR DE EXCEL - Sistema de Inventario AGC
Funciones para importación/exportación de Excel
"""

import pandas as pd
import os
from datetime import datetime


def leer_excel_importacion(ruta_archivo):
    """Lee Excel y devuelve análisis completo para diálogo estratégico"""
    try:
        # 1. SCAN EXPRESS (duplicados internos)
        from utils.validadores_inventario import analizador_excel_agresivo
        
        conflictos, df = analizador_excel_agresivo(ruta_archivo)
        
        if conflictos['bloqueado']:
            from utils.validadores_inventario import generar_reporte_bloqueo
            return None, generar_reporte_bloqueo(conflictos), None
        
        # 2. DETECTAR REGISTROS EXISTENTES vs NUEVOS
        from database.db_manager import DB
        db = DB()
        
        analisis = {
            'nuevos': [],
            'existentes': [],
            'total_filas_excel': len(df),  # Nombre más descriptivo
            'total_registros': len(df),    # Para compatibilidad con el resto del sistema
            'conflictos_merge': [],
            'ruta_original': ruta_archivo  # ✅ AGREGADO
        }
        
        for index, fila in df.iterrows():
            ficha = str(fila.get('ficha', '')).strip()
            
            # Verificar si existe en BD
            if db.existe_bien_por_ficha(ficha):
                analisis['existentes'].append({
                    'ficha': ficha,
                    'tipo': str(fila.get('tipo', '')),
                    'fila_excel': index + 2,
                    'datos_excel': fila.to_dict()
                })
            else:
                analisis['nuevos'].append({
                    'ficha': ficha, 
                    'tipo': str(fila.get('tipo', '')),
                    'fila_excel': index + 2
                })
        
        return df, None, analisis
        
    except Exception as e:
        return None, f"Error en importación: {str(e)}", None


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