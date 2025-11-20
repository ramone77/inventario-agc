import pandas as pd
from collections import defaultdict
import sys

def analizador_excel_agresivo(ruta_archivo):
    """Scan rápido - solo duplicados críticos"""
    try:
        df = pd.read_excel(ruta_archivo)
        
        # 1. FICHAS DUPLICADAS (siempre bloqueante)
        fichas_dup = df[df.duplicated('ficha', keep=False)]
        if not fichas_dup.empty:
            return {'bloqueado': True, 'motivo': 'FICHAS_DUPLICADAS', 'detalle': fichas_dup['ficha'].unique().tolist(), 'total_registros': len(df)}, None

        # 2. SERIES DUPLICADAS (solo si no vacías)
        series_validas = df[df['serie'].notna() & (df['serie'] != '') & (~df['serie'].astype(str).str.upper().isin(['SIN SERIE', 'S/N', 'N/A']))]
        series_dup = series_validas[series_validas.duplicated('serie', keep=False)]
        if not series_dup.empty:
            return {'bloqueado': True, 'motivo': 'SERIES_DUPLICADAS', 'detalle': series_dup['serie'].unique().tolist(), 'total_registros': len(df)}, None

        # 3. IMEIs DUPLICADOS (solo si no vacíos)  
        imeis_validos = df[df['imei'].notna() & (df['imei'] != '') & (df['imei'] != '0') & (~df['imei'].astype(str).str.upper().isin(['N/A', 'NA']))]
        imeis_dup = imeis_validos[imeis_validos.duplicated('imei', keep=False)]
        if not imeis_dup.empty:
            return {'bloqueado': True, 'motivo': 'IMEIS_DUPLICADOS', 'detalle': imeis_dup['imei'].unique().tolist(), 'total_registros': len(df)}, None

        return {'bloqueado': False, 'total_registros': len(df)}, df
        
    except Exception as e:
        return {'bloqueado': True, 'motivo': f'ERROR_LECTURA: {str(e)}', 'total_registros': 0}, None

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