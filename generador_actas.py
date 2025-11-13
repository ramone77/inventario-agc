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
        self.responsables = self._cargar_responsables()
        
    def _crear_carpetas(self):
        """Crea las carpetas necesarias si no existen"""
        os.makedirs(self.carpeta_plantillas, exist_ok=True)
        os.makedirs(self.carpeta_actas, exist_ok=True)
        
    def _cargar_responsables(self):
        """Carga los responsables desde el archivo JSON"""
        try:
            with open('responsables_sopys.json', 'r', encoding='utf-8') as f:
                return json.load(f)['responsables']
        except FileNotFoundError:
            print("⚠️  Archivo responsables_sopys.json no encontrado, usando datos por defecto")
            return [
                {
                    "nombre": "SANTIAGO JOAQUÍN LÓPEZ",
                    "dni": "29.989.358",
                    "cargo": "Responsable de Patrimonio"
                }
            ]
    
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
            
            # Obtener responsable SOPyS
            responsable_sopys = self._obtener_responsable_actual(usuario_actual)
            
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
            
            # Preparar contexto MEJORADO
            contexto = {
                'dia': datetime.now().day,
                'mes': self._obtener_mes_actual(),
                'anio': datetime.now().year,
                'responsable_sopys': responsable_sopys['nombre'],
                'dni_responsable_sopys': responsable_sopys['dni'],
                'cargo_responsable_sopys': responsable_sopys.get('cargo', ''),
                'agente_receptor': datos_bienes[0].get('responsable_actual', '') if isinstance(datos_bienes, list) else datos_bienes.get('responsable_actual', ''),
                'area_receptor': datos_bienes[0].get('area', 'INSTITUCIONAL') if isinstance(datos_bienes, list) else datos_bienes.get('area', 'INSTITUCIONAL'),
                'dni_receptor': datos_bienes[0].get('dni_responsable', '') if isinstance(datos_bienes, list) else datos_bienes.get('dni_responsable', ''),
                'bienes': bienes_lista,  # NUEVO: Lista de bienes para la tabla dinámica
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
            return ruta_completa
            
        except Exception as e:
            error_msg = f"❌ Error generando acta {tipo}: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _obtener_responsable_actual(self, usuario_actual):
        """Obtiene el responsable SOPyS (usuario actual o por defecto)"""
        for resp in self.responsables:
            if resp['nombre'].lower() == usuario_actual.lower():
                return resp
        return self.responsables[0]  # Por defecto
    
    def _generar_texto_pie(self, usuario_actual):
        """Genera el texto de auditoría"""
        fecha_hora = datetime.now().strftime("%d/%m/%Y a las %H:%M hrs")
        return f"Generado por {usuario_actual} el {fecha_hora}"
    
    def _obtener_mes_actual(self):
        meses = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        return meses[datetime.now().month - 1]


# TEST MEJORADO CON MÚLTIPLES BIENES
if __name__ == "__main__":
    # DATOS DE PRUEBA MEJORADOS - AHORA CON MÚLTIPLES BIENES
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
        },
        {
            'ficha': 'INV-2024-002', 
            'serie': 'SN987654321',
            'tipo': 'MONITOR',
            'marca': 'SAMSUNG',
            'modelo': '24F350',
            'responsable_actual': 'LAURA GÓMEZ',
            'area': 'CONTABILIDAD',
            'dni_responsable': '27.654.321',
            'cantidad': 1
        },
        {
            'ficha': 'INV-2024-003',
            'serie': 'SN555666777',
            'tipo': 'TECLADO',
            'marca': 'LOGITECH',
            'modelo': 'K120',
            'responsable_actual': 'LAURA GÓMEZ', 
            'area': 'CONTABILIDAD',
            'dni_responsable': '27.654.321',
            'cantidad': 1
        }
    ]
    
    generador = GeneradorActas()
    
    print("🧪 PROBANDO GENERADOR MEJORADO CON MÚLTIPLES BIENES...")
    
    # Probar acta de entrega con múltiples bienes
    resultado_entrega = generador.generar_acta_entrega(bienes_prueba, "RUBEN LAZARTE")
    print(f"Entrega: {resultado_entrega}")
    
    # Probar acta de recepción con múltiples bienes
    resultado_recepcion = generador.generar_acta_recepcion(bienes_prueba, "RUBEN LAZARTE")  
    print(f"Recepción: {resultado_recepcion}")
    
    print("🎯 PRUEBA COMPLETADA - Revisa la carpeta 'actas_generadas'")
    print("   Ahora con soporte para múltiples bienes y firmas profesionales!")