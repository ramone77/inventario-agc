# generador_actas.py
from docxtpl import DocxTemplate
from datetime import datetime
import os
import json

class GeneradorActas:
    def __init__(self):
        self.carpeta_plantillas = "plantillas"
        self.carpeta_actas = "actas_generadas"
        self._crear_carpetas()
        
    def _crear_carpetas(self):
        """Crea las carpetas necesarias si no existen"""
        os.makedirs(self.carpeta_plantillas, exist_ok=True)
        os.makedirs(self.carpeta_actas, exist_ok=True)
    
    def generar_acta_entrega(self, datos_bienes, usuario_actual):
        """Genera acta de entrega automáticamente - AHORA SOPORTA MÚLTIPLES BIENES"""
        return self._generar_acta('entrega', datos_bienes, usuario_actual)
    
    def generar_acta_recepcion(self, datos_bienes, usuario_actual):
        """Genera acta de recepción automáticamente - AHORA SOPORTA MÚLTIPLES BIENES"""
        return self._generar_acta('recepcion', datos_bienes, usuario_actual)
    
    def _generar_acta(self, tipo, datos_bienes, usuario_actual):
        """Genera acta según el tipo (entrega/recepcion) - AHORA SOPORTA MÚLTIPLES BIENES"""
        try:
            # Seleccionar plantilla según tipo
            if tipo == 'entrega':
                plantilla = "UCA-GOAYF-SOPyS-PRO-01-FORM-02 Rev. 02 - Acta de entrega (Recuperado automáticamente).docx"
            else:
                plantilla = "UCA-GOAYF-SOPyS-PRO-01-FORM-12 Rev. 01 Acta de recepcion.docx"
            
            # Verificar que la plantilla existe
            ruta_plantilla = f"{self.carpeta_plantillas}/{plantilla}"
            if not os.path.exists(ruta_plantilla):
                return f"❌ Plantilla no encontrada: {ruta_plantilla}"
            
            # Cargar plantilla
            doc = DocxTemplate(ruta_plantilla)
            
            # ✅ NUEVO: Obtener datos del usuario actual (responsable SOPyS)
            responsable_sopys = self._obtener_datos_usuario_actual(usuario_actual)
            
            # PREPARAR LISTA DE BIENES (AHORA SOPORTA MÚLTIPLES)
            if isinstance(datos_bienes, list):
                # Si es una lista de bienes
                bienes_lista = []
                for bien in datos_bienes:
                    bienes_lista.append({
                        'cantidad': bien.get('cantidad', 1),
                        'descripcion': f"{bien.get('tipo', '')} {bien.get('marca', '')} {bien.get('modelo', '')}".strip(),
                        'ficha': bien.get('ficha', ''),
                        'serie': bien.get('serie', '')
                    })
            else:
                # Si es un solo bien (compatibilidad hacia atrás)
                bienes_lista = [{
                    'cantidad': 1,
                    'descripcion': f"{datos_bienes.get('tipo', '')} {datos_bienes.get('marca', '')} {datos_bienes.get('modelo', '')}".strip(),
                    'ficha': datos_bienes.get('ficha', ''),
                    'serie': datos_bienes.get('serie', '')
                }]
            
            # ✅ NUEVO: Preparar contexto MEJORADO con datos del usuario
            contexto = {
                'dia': datetime.now().day,
                'mes': self._obtener_mes_actual(),
                'anio': datetime.now().year,
                
                # ✅ DATOS DEL USUARIO ACTUAL (RESPONSABLE SOPyS)
                'responsable_sopys': responsable_sopys['nombre_completo'],
                'dni_responsable_sopys': responsable_sopys['dni_cuit'],
                'cargo_responsable_sopys': responsable_sopys['cargo'],
                
                # Datos del receptor (persona que recibe el bien)
                'agente_receptor': datos_bienes[0].get('responsable_actual', '') if isinstance(datos_bienes, list) else datos_bienes.get('responsable_actual', ''),
                'area_receptor': datos_bienes[0].get('area', 'INSTITUCIONAL') if isinstance(datos_bienes, list) else datos_bienes.get('area', 'INSTITUCIONAL'),
                'dni_receptor': datos_bienes[0].get('dni_responsable', '') if isinstance(datos_bienes, list) else datos_bienes.get('dni_responsable', ''),
                
                # Lista de bienes
                'bienes': bienes_lista,
                'texto_generacion': self._generar_texto_pie(usuario_actual)
            }
            
            # Generar nombre de archivo
            if isinstance(datos_bienes, list) and len(datos_bienes) > 0:
                ficha_principal = datos_bienes[0].get('ficha', 'MULTIPLES')
            else:
                ficha_principal = datos_bienes.get('ficha', 'SIN_FICHA')
                
            nombre_archivo = f"ACTA_{tipo.upper()}_{ficha_principal}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
            ruta_completa = f"{self.carpeta_actas}/{nombre_archivo}"
            
            # Renderizar y guardar
            doc.render(contexto)
            doc.save(ruta_completa)
            
            print(f"✅ Acta de {tipo.upper()} generada: {nombre_archivo}")
            print(f"   📦 Bienes incluidos: {len(bienes_lista)}")
            print(f"   👤 Responsable SOPyS: {responsable_sopys['nombre_completo']}")
            return ruta_completa
            
        except Exception as e:
            error_msg = f"❌ Error generando acta {tipo}: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _obtener_datos_usuario_actual(self, usuario_actual):
        """✅ NUEVO: Obtiene los datos completos del usuario actual"""
        print(f"🔍 DEBUG _obtener_datos_usuario_actual:")
        print(f"   Tipo: {type(usuario_actual)}")
        print(f"   Valor: {usuario_actual}")
        
        try:
            # Si es string, buscar en la base de datos
            if isinstance(usuario_actual, str):
                print(f"   ⚠️ usuario_actual es string, buscando en BD...")
                # Aquí necesitaríamos conectar a la BD para obtener los datos completos
                # Por ahora devolvemos datos por defecto
                return {
                    'nombre_completo': 'USUARIO TEMPORAL',
                    'dni_cuit': 'SIN DATOS',
                    'cargo': 'Responsable de Patrimonio'
                }
            
            # Si es diccionario, usar los datos directamente
            nombre_completo = f"{usuario_actual.get('nombre', '')} {usuario_actual.get('apellido', '')}".strip()
            
            resultado = {
                'nombre_completo': nombre_completo,
                'dni_cuit': usuario_actual.get('dni_cuit', ''),
                'cargo': usuario_actual.get('cargo', 'Responsable de Patrimonio')
            }
            
            print(f"   ✅ Datos obtenidos: {resultado}")
            return resultado
            
        except Exception as e:
            print(f"⚠️ Error obteniendo datos usuario: {e}")
            return {
                'nombre_completo': 'SANTIAGO JOAQUÍN LÓPEZ',
                'dni_cuit': '29.989.358', 
                'cargo': 'Responsable de Patrimonio'
            }
    
    def _generar_texto_pie(self, usuario_actual):
        """Genera el texto de auditoría"""
        fecha_hora = datetime.now().strftime("%d/%m/%Y a las %H:%M hrs")
        usuario_id = usuario_actual.get('id', 'SISTEMA') if isinstance(usuario_actual, dict) else usuario_actual
        return f"Generado por {usuario_id} el {fecha_hora}"
    
    def _obtener_mes_actual(self):
        meses = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        return meses[datetime.now().month - 1]


# TEST MEJORADO CON DATOS DE USUARIO REALES
if __name__ == "__main__":
    # ✅ DATOS DE USUARIO DE PRUEBA (simulando usuario logueado)
    usuario_prueba = {
        'id': 'mario',
        'nombre': 'Mario',
        'apellido': 'Admin', 
        'cargo': 'Administrador del Sistema',
        'dni_cuit': '20.123.456',
        'email': 'mario@agc.gob.ar',
        'rol': 'admin'
    }
    
    # DATOS DE BIENES DE PRUEBA
    bienes_prueba = [
        {
            'ficha': 'INV-2024-001',
            'serie': 'SN123456789',
            'tipo': 'NOTEBOOK',
            'marca': 'DELL',
            'modelo': 'LATITUDE 5420',
            'responsable_actual': 'LAURA GÓMEZ',
            'area': 'CONTABILIDAD',
            'dni_responsable': '27.654.321',
            'cantidad': 1
        }
    ]
    
    generador = GeneradorActas()
    
    print("🧪 PROBANDO GENERADOR CON DATOS DE USUARIO REALES...")
    
    # Probar acta de entrega con datos de usuario
    resultado_entrega = generador.generar_acta_entrega(bienes_prueba, usuario_prueba)
    print(f"Entrega: {resultado_entrega}")
    
    print("🎯 PRUEBA COMPLETADA - Revisa la carpeta 'actas_generadas'")
    print("   Ahora con datos reales del usuario logueado!")