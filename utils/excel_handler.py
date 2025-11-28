"""
🔧 MANEJADOR DE EXCEL - Sistema de Inventario AGC
Funciones para importación/exportación de Excel
"""

import pandas as pd
from datetime import datetime
from typing import Optional  # ✅ Importar Optional

def normalizar_institucional(institucional_raw: str) -> str:
    """
    Normaliza una sigla como 'UCA' o 'DGFyC' a su nombre completo oficial.
    Si no se encuentra en el mapeo, devuelve el valor original.
    """
    institucional_clean = institucional_raw.strip().upper()

    # Mapeo de siglas a nombres completos
    mapeo = {
        "UCA": "UNIDAD DE COORDINACION ADMINISTRATIVA",
        "DGFYC": "DIRECCION GENERAL DE FISCALIZACION Y CONTROL",
        "DGFYCO": "DIRECCION GENERAL DE FISCALIZACION Y CONTROL",
        "DGHYSA": "DIRECCION GENERAL DE HIGIENE Y SEGURIDAD ALIMENTARIA",  # ← CORREGIDO
        "DGLYT": "DIRECCION GENERAL LEGAL Y TECNICA",
        "AGC": "AGENCIA GUBERNAMENTAL DE CONTROL",
        "UOPCG": "UNIDAD OPERATIVA PLANIFICACION Y COORDINACION DE GESTION",
        "DE": "DIRECCION EJECUTIVA",
        "GOEC": "GERENCIA OPERATIVA ESTRATEGIA COMUNICACIONAL",
        "DGHYP": "DIRECCION GENERAL HABILITACIONES Y PERMISOS",
        "DGFYCOBRAS": "DIRECCION GENERAL FISCALIZACION Y CONTROL DE OBRAS",  # ← Puedes usar un nombre más corto
        "UOFI": "UNION OPERATIVA DE FISCALIZACION INTEGRAL",
        "UAI": "UNIDAD DE AUDITORIA INTERNA",
        # Añadir más según necesites
    }

    # Buscar si coincide alguna sigla
    for sigla, nombre_completo in mapeo.items():
        if institucional_clean == sigla:
            return nombre_completo

    # Si no se encuentra, devolver el valor original
    return institucional_raw.strip()

def analizar_y_preparar_importacion(ruta_excel: str, db, bien_manager) -> dict:
    """
    Analiza Excel y prepara importación robusta:
    - Detecta duplicados internos (en el Excel)
    - Compara contra BD real usando tu lógica de bien_existe()
    - Clasifica: nuevos, actualizables, conflictos, errores
    - Usa _limpiar_valor_numerico() para evitar falsos duplicados por .0
    - Valida y estandariza estados (En depósito, Asignado, etc.)
    
    Devuelve dict con:
        'df_nuevos', 'df_actualizables', 'df_conflictos', 'df_duplicados_excel',
        'resumen', 'errores_detalles'
    """
    try:
        # 🔹 1. LEER EXCEL CON dtypes=str PARA EVITAR .0 y NaN
        df = pd.read_excel(ruta_excel, dtype=str)
        if df.empty:
            raise ValueError("El archivo Excel está vacío")

        # 🔹 2. LIMPIEZA INICIAL
        df = df.fillna("").astype(str).apply(lambda x: x.str.strip())
        total_registros = len(df)

        # 🔹 3. ESTRUCTURAS
        duplicados_excel = []
        errores_detalles = []

        # 🔹 4. AGRUPAR POR FICHA (PRIORIDAD MÁXIMA)
        # Agrupar índices por ficha (normalizada)
        grupos_por_ficha = {}
        for idx, row in df.iterrows():
            ficha_raw = str(row.get('ficha', '')).strip()
            # Usar _limpiar_valor_numerico para agrupar correctamente
            ficha_clean = bien_manager._limpiar_valor_numerico(ficha_raw)
            if ficha_clean:
                grupos_por_ficha.setdefault(ficha_clean, []).append((idx, row))
            else:
                # Ficha vacía → error
                errores_detalles.append({
                    'fila': idx + 2,
                    'ficha': ficha_raw,
                    'motivo': 'Ficha vacía o inválida'
                })

        # 🔹 5. PROCESAR CADA GRUPO (por ficha)
        registros_unicos = {}  # dict: ficha_clean -> row_dict
        for ficha_clean, registros in grupos_por_ficha.items():
            # Ordenar por completitud (más campos no vacíos primero)
            def completitud(row):
                # ✅ CORREGIDO: Asegurar que solo se suman cadenas no vacías
                return sum(1 for col in df.columns if str(row[col]).strip() not in ['', 'SIN SERIE', 'SIN IMEI', 'N/A'])
            
            registros_ordenados = sorted(registros, key=lambda x: completitud(x[1]), reverse=True)
            idx_valido, row_valido = registros_ordenados[0]

            # Registrar duplicados internos
            if len(registros_ordenados) > 1:
                for i, (idx_dup, row_dup) in enumerate(registros_ordenados):
                    if i > 0:  # El primero es el candidato válido
                        # Los demás son duplicados internos
                        duplicados_excel.append({
                            **row_dup.to_dict(),
                            'fila_excel': idx_dup + 2,
                            'Motivo de rechazo': f'Ficha duplicada en Excel (vs fila {idx_valido + 2})'
                        })
            
            # El que se queda para análisis contra BD
            row_dict = row_valido.to_dict()
            # LIMPIAR VALORES NUMÉRICOS (clave para evitar falsos duplicados)
            for campo in ['ficha', 'imei', 'dni_cuit', 'linea', 'sim', 'serie']:
                if campo in row_dict:
                    row_dict[campo] = bien_manager._limpiar_valor_numerico(row_dict[campo])

            # ✅ FUERA DEL FOR
            if 'institucional' in row_dict:
                row_dict['institucional'] = normalizar_institucional(row_dict['institucional'])
            
            # ✅ ESTANDARIZAR ESTADO ANTES DE VALIDAR
            estado_raw = str(row_dict.get('estado', '')).strip()
            estado_mapeado = mapear_estado(estado_raw)
            if estado_mapeado is None:
                errores_detalles.append({
                    'fila': idx_valido + 2,
                    'ficha': ficha_clean,
                    'motivo': f'Estado inválido o no mapeable: "{estado_raw}"'
                })
                continue  # Saltar este registro
            else:
                row_dict['estado'] = estado_mapeado  # Reemplazar con el oficial
            
            registros_unicos[ficha_clean] = row_dict

        # 🔹 6. VALIDAR Y CLASIFICAR REGISTROS ÚNICOS
        nuevos = []
        actualizables = []
        conflictos = []

        for ficha_clean, row_dict in registros_unicos.items():
            # Obtener valores clave
            tipo = str(row_dict.get('tipo', '')).strip()
            marca = str(row_dict.get('marca', '')).strip()
            modelo = str(row_dict.get('modelo', '')).strip()
            serie = str(row_dict.get('serie', '')).strip()
            imei = str(row_dict.get('imei', '')).strip()

            # ✅ VALIDACIONES OBLIGATORIAS (ajustadas para flexibilidad)
            motivos_error = []
            if not tipo:
                motivos_error.append('Tipo vacío')  # <-- Esto sí es obligatorio
            # if tipo and tipo not in ["Oficina", "Cocina", "Laboratorio", "Celular", "Tablet", "Otro"]:
            #     motivos_error.append(f'Tipo inválido: "{tipo}"')  # <-- COMENTADO: ya no es necesario
            
            # Validar IMEI para móviles (solo si tipo es Celular/Tablet y hay IMEI)
            if tipo in ["Celular", "Tablet"] and imei:
                if not imei.isdigit() or len(imei) != 15:
                    motivos_error.append('IMEI debe ser 15 dígitos numéricos')

            if motivos_error:
                errores_detalles.append({
                    'fila': row_dict.get('fila_excel', 'N/A'),
                    'ficha': ficha_clean,
                    'motivo': ', '.join(motivos_error)
                })
                continue

            # ✅ BUSCAR EN BD REAL
            bien_bd = db.obtener_bien_por_ficha(ficha_clean)

            # Determinar estado
            if bien_bd is None:
                # ✅ NUEVO
                nuevos.append(row_dict)
            else:
                # 🔄 o ⚠️: comparar con BD
                es_actualizable = True
                conflictos_campos = []

                # Definir campos que NO se sobrescriben (solo se completan si están vacíos en BD)
                campos_solo_completar = ['nombre', 'apellido', 'dni_cuit', 'institucional', 'imei', 'serie', 'linea', 'sim', 'descripcion', 'prd', 'anio_prd', 'monto_original']
                campos_no_sobrescribir = ['estado', 'responsable']  # cambiar solo con movimientos

                # Comparar campos
                for campo in campos_solo_completar:
                    valor_excel = str(row_dict.get(campo, '')).strip()
                    valor_bd = str(bien_bd.get(campo, '')).strip()

                    # Si BD está vacío y Excel tiene dato → actualizar (actualizable)
                    if not valor_bd and valor_excel:
                        continue  # OK: completar
                    # Si ambos tienen datos y difieren → no es error, pero tampoco sobrescribir
                    elif valor_bd and valor_excel and valor_bd != valor_excel:
                        # No es conflicto grave: solo info adicional
                        pass

                # Verificar campos críticos (no sobrescribir)
                for campo in campos_no_sobrescribir:
                    valor_excel = str(row_dict.get(campo, '')).strip()
                    valor_bd = str(bien_bd.get(campo, '')).strip()
                    if valor_bd and valor_excel and valor_bd != valor_excel:
                        conflictos_campos.append(f'{campo}: BD="{valor_bd}" ≠ Excel="{valor_excel}"')

                # Estado también es crítico
                estado_excel = str(row_dict.get('estado', '')).strip()
                estado_bd = str(bien_bd.get('estado', '')).strip()
                if estado_bd and estado_excel and estado_bd.lower() != estado_excel.lower():
                    conflictos_campos.append(f'estado: BD="{estado_bd}" ≠ Excel="{estado_excel}"')

                if conflictos_campos:
                    # ⚠️ CONFLICTO
                    conflictos.append({
                        **row_dict,
                        '_bien_bd': bien_bd,
                        '_conflictos': conflictos_campos
                    })
                else:
                    # 🔄 ACTUALIZABLE (completar datos faltantes)
                    actualizables.append({
                        **row_dict,
                        '_bien_bd': bien_bd
                    })

        # 🔹 7. CONVERTIR A DATAFRAMES
        df_nuevos = pd.DataFrame(nuevos) if nuevos else pd.DataFrame(columns=df.columns)
        df_actualizables = pd.DataFrame(actualizables) if actualizables else pd.DataFrame(columns=df.columns)
        df_conflictos = pd.DataFrame(conflictos) if conflictos else pd.DataFrame(columns=df.columns)
        df_duplicados_excel = pd.DataFrame(duplicados_excel) if duplicados_excel else pd.DataFrame(columns=list(df.columns) + ['fila_excel', 'Motivo de rechazo'])

        # 🔹 8. RESUMEN EJECUTIVO
        resumen = {
            'total_registros': total_registros,
            'nuevos': len(nuevos),
            'actualizables': len(actualizables),
            'conflictos': len(conflictos),
            'duplicados_excel': len(duplicados_excel),
            'errores_validacion': len(errores_detalles),
            'importables': len(nuevos) + len(actualizables),
            'rechazados': len(conflictos) + len(duplicados_excel) + len(errores_detalles)
        }

        return {
            'df_nuevos': df_nuevos,
            'df_actualizables': df_actualizables,
            'df_conflictos': df_conflictos,
            'df_duplicados_excel': df_duplicados_excel,
            'resumen': resumen,
            'errores_detalles': errores_detalles
        }

    except Exception as e:
        raise RuntimeError(f"Error analizando Excel: {str(e)}")


def mapear_estado(estado_raw: str) -> Optional[str]:  # ✅ CORREGIDO: Usando Optional
    """
    Mapea estados no oficiales a estados oficiales.
    Devuelve None si no se puede mapear.
    """
    estado_lower = estado_raw.lower().strip()

    # Mapeo a versión estandarizada
    if estado_lower in ["en deposito", "en depósito", "en_deposito", "stock", "disponible", "disponible para asignar"]:
        return "En depósito"
    elif estado_lower in ["asignado", "asignada", "asignacion", "asignación", "entregado", "en uso"]:
        return "Asignado"
    elif estado_lower in ["baja definitiva", "baja", "dado de baja", "baja_definitiva", "retirado"]:
        return "Baja definitiva"
    elif estado_lower in ["en reparacion", "en reparación", "reparacion", "reparación", "en mantenimiento", "en reparo"]:
        return "En reparación"
    else:
        # Estado no mapeable
        return None