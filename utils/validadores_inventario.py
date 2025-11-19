import pandas as pd
from collections import defaultdict
import sys

def analizador_excel_agresivo(ruta_archivo):
    """
    Versión SIMPLE - Solo busca duplicados por ficha, serie, IMEI
    """
    try:
        df = pd.read_excel(ruta_archivo)
        
        conflictos = {
            'fichas_duplicadas': {},
            'series_duplicadas': {}, 
            'imeis_duplicados': {},
            'total_registros': len(df),
            'bloqueado': False
        }
        
        # 1. BUSCAR FICHAS DUPLICADAS
        fichas_dup = df[df.duplicated('ficha', keep=False)]
        if not fichas_dup.empty:
            for ficha in fichas_dup['ficha'].unique():
                conflictos['fichas_duplicadas'][ficha] = "DUPLICADO_EN_EXCEL"
        
        # 2. BUSCAR SERIES DUPLICADAS (ignorar vacíos y "SIN SERIE")
        series_filtradas = df[
            df['serie'].notna() & 
            ~df['serie'].isin(['', 'SIN SERIE', 'S/N'])
        ]
        series_dup = series_filtradas[series_filtradas.duplicated('serie', keep=False)]
        if not series_dup.empty:
            for serie in series_dup['serie'].unique():
                conflictos['series_duplicadas'][serie] = "DUPLICADO_EN_EXCEL"
        
        # 3. BUSCAR IMEIs DUPLICADOS (ignorar vacíos)
        imeis_filtrados = df[
            df['imei'].notna() & 
            ~df['imei'].isin(['', '0'])
        ]
        imeis_dup = imeis_filtrados[imeis_filtrados.duplicated('imei', keep=False)]
        if not imeis_dup.empty:
            for imei in imeis_dup['imei'].unique():
                conflictos['imeis_duplicados'][imei] = "DUPLICADO_EN_EXCEL"
        
        # BLOQUEAR si hay CUALQUIER duplicado
        conflictos['bloqueado'] = any([
            conflictos['fichas_duplicadas'],
            conflictos['series_duplicadas'],
            conflictos['imeis_duplicados']
        ])
        
        return conflictos, df
        
    except Exception as e:
        return {'error': str(e), 'bloqueado': True}, None

def generar_reporte_bloqueo(conflictos):
    """
    Genera un reporte MEGA CLARO para el usuario
    """
    if conflictos.get('error'):
        return f"❌ ERROR: No se pudo leer el archivo - {conflictos['error']}"
    
    reporte = []
    reporte.append("🛑 **IMPORTACIÓN BLOQUEADA** 🛑")
    reporte.append("======================================")
    reporte.append(f"📊 Total registros en Excel: {conflictos['total_registros']}")
    reporte.append("")
    
    # FICHAS DUPLICADAS
    if conflictos['fichas_duplicadas']:
        reporte.append("❌ **FICHAS DUPLICADAS EN EL EXCEL:**")
        for ficha, registros in conflictos['fichas_duplicadas'].items():
            reporte.append(f"   📍 Ficha {ficha} aparece en:")
            for reg in registros:
                serie_info = f" (Serie: {reg['serie']})" if reg['serie'] else ""
                imei_info = f" (IMEI: {reg['imei']})" if reg['imei'] else ""
                reporte.append(f"      - Fila {reg['fila']}: {reg['tipo']}{serie_info}{imei_info}")
        reporte.append("")
    
    # SERIES DUPLICADAS
    if conflictos['series_duplicadas']:
        reporte.append("❌ **SERIES DUPLICADAS EN EL EXCEL:**")
        for serie, registros in conflictos['series_duplicadas'].items():
            reporte.append(f"   📍 Serie {serie} aparece en:")
            for reg in registros:
                reporte.append(f"      - Fila {reg['fila']}: Ficha {reg['ficha']} ({reg['tipo']})")
        reporte.append("")
    
    # IMEIs DUPLICADOS
    if conflictos['imeis_duplicados']:
        reporte.append("❌ **IMEIs DUPLICADOS EN EL EXCEL:**")
        for imei, registros in conflictos['imeis_duplicados'].items():
            reporte.append(f"   📍 IMEI {imei} aparece en:")
            for reg in registros:
                reporte.append(f"      - Fila {reg['fila']}: Ficha {reg['ficha']} ({reg['tipo']})")
        reporte.append("")
    
    reporte.append("💡 **ACCIONES REQUERIDAS:**")
    reporte.append("   1. Abra el archivo Excel")
    reporte.append("   2. Corrija los duplicados mencionados arriba") 
    reporte.append("   3. Guarde el archivo")
    reporte.append("   4. Vuelva a intentar la importación")
    reporte.append("")
    reporte.append("🔒 **Nota: Ningún registro se importará hasta que se resuelvan estos conflictos**")
    
    return "\n".join(reporte)

# Función principal para testing
def main():
    if len(sys.argv) != 2:
        print("Uso: python analizador_duplicados.py <archivo_excel>")
        return
    
    archivo = sys.argv[1]
    
    print("🚀 INICIANDO ANALIZADOR DE DUPLICADOS")
    print("=" * 50)
    
    # Ejecutar análisis
    conflictos, df = analizador_excel_agresivo(archivo)
    
    # Generar y mostrar reporte
    reporte = generar_reporte_bloqueo(conflictos)
    print("\n" + reporte)
    
    # Mostrar resumen ejecutivo
    print("\n📈 RESUMEN EJECUTIVO:")
    print(f"   - Fichas duplicadas: {len(conflictos.get('fichas_duplicadas', {}))}")
    print(f"   - Series duplicadas: {len(conflictos.get('series_duplicadas', {}))}")
    print(f"   - IMEIs duplicados: {len(conflictos.get('imeis_duplicados', {}))}")
    print(f"   - Importación bloqueada: {'SI' if conflictos['bloqueado'] else 'NO'}")

if __name__ == "__main__":
    main()