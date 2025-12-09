"""
🏗️ GESTOR DE MOVIMIENTOS - Sistema de Inventario AGC  
Lógica de negocio para movimientos - CON GENERACIÓN AUTOMÁTICA DE ACTAS
"""

import os  # <-- AÑADE ESTA LÍNEA (para os.path.exists)
import json
from datetime import datetime
from pathlib import Path  # <-- OPCIONAL pero recomendado para manejo de rutas

from database.db_manager import DB
from generador_actas import GeneradorActas


class MovimientoManager:
    """Maneja la lógica de negocio para movimientos CON ACTAS AUTOMÁTICAS"""
    
    def __init__(self, db: DB):
        self.db = db
        self.generador_actas = GeneradorActas()  # Instanciamos el generador
    
    def _obtener_datos_bienes(self, bienes_ids):
        """Obtiene datos completos de los bienes para el acta"""
        try:
            bienes_completos = []
            for bien_id in bienes_ids:
                # Necesitamos implementar este método en DB
                bien_data = self.db.obtener_bien_por_id(bien_id)
                if bien_data:
                    # Agregar datos del responsable si están en el bien
                    bien_data['responsable_actual'] = f"{bien_data.get('nombre', '')} {bien_data.get('apellido', '')}".strip()
                    bien_data['dni_responsable'] = bien_data.get('dni_cuit', '')
                    bien_data['area'] = bien_data.get('institucional', 'INSTITUCIONAL')
                    bien_data['cantidad'] = 1
                    bienes_completos.append(bien_data)
            
            return bienes_completos
        except Exception as e:
            print(f"❌ Error obteniendo datos de bienes: {e}")
            return []
    
    def _generar_acta_automatica(self, tipo_movimiento, bienes_completos, datos_movimiento, usuario_actual):
        """Genera acta automáticamente según el tipo de movimiento"""
        try:
            # Preparar datos adicionales para el acta
            for bien in bienes_completos:
                # Si es una entrega, usar datos del movimiento (nuevo responsable)
                if tipo_movimiento == "Entrega":
                    bien['responsable_actual'] = f"{datos_movimiento.get('responsable_nombre', '')} {datos_movimiento.get('responsable_apellido', '')}".strip()
                    bien['dni_responsable'] = datos_movimiento.get('responsable_dni_cuit', '')
                    bien['area'] = datos_movimiento.get('responsable_institucional', 'INSTITUCIONAL')
            
            # Generar acta según el tipo
            if tipo_movimiento == "Entrega":
                return self.generador_actas.generar_acta_entrega(bienes_completos, usuario_actual)
            elif tipo_movimiento == "Devolución":
                return self.generador_actas.generar_acta_recepcion(bienes_completos, usuario_actual)
            else:
                # Para bajas u otros movimientos, no generar acta
                return ""
                
        except Exception as e:
            print(f"❌ Error generando acta automática: {e}")
            return f"❌ Error: {str(e)}"
        
    def _abrir_carpeta_actas(self, ruta_acta):
        """Abre la carpeta de actas generadas en el explorador"""
        try:
            import os
            import platform
            import subprocess
            
            carpeta_actas = os.path.dirname(ruta_acta)
            
            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(carpeta_actas)
            elif sistema == "Darwin":  # macOS
                subprocess.run(["open", carpeta_actas])
            else:  # Linux
                subprocess.run(["xdg-open", carpeta_actas])
                
            print(f"📁 Carpeta de actas abierta: {carpeta_actas}")
            
        except Exception as e:
            print(f"⚠️ No se pudo abrir la carpeta: {e}")

     

        
    def _guardar_pdf_correctamente(self, pdf_temp_path, movimiento_id, datos_movimiento):
        """Guarda PDF en actas_local/ con nombre descriptivo - VERSIÓN SEGURA"""
        try:
            # Crear carpeta si no existe
            import os
            os.makedirs("actas_local", exist_ok=True)
            
            # Nombre descriptivo sin caracteres problemáticos
            responsable = ""
            if datos_movimiento.get('responsable_nombre'):
                responsable += datos_movimiento['responsable_nombre'].replace(" ", "_")
            if datos_movimiento.get('responsable_apellido'):
                responsable += "_" + datos_movimiento['responsable_apellido'].replace(" ", "_")
            
            if not responsable:
                responsable = "SIN_RESPONSABLE"
            
            tipo_mov = datos_movimiento.get('tipo', 'ENTREGA').upper().replace(" ", "_")
            fecha = datetime.now().strftime('%Y%m%d')
            
            nombre_pdf = f"ACTA_{tipo_mov}_{responsable}_{fecha}.pdf"
            ruta_final = os.path.join("actas_local", nombre_pdf)
            
            # Copiar (NO sobreescribir si existe)
            import shutil
            if os.path.exists(ruta_final):
                # Agregar timestamp único
                timestamp = datetime.now().strftime('%H%M%S')
                nombre_pdf = f"ACTA_{tipo_mov}_{responsable}_{fecha}_{timestamp}.pdf"
                ruta_final = os.path.join("actas_local", nombre_pdf)
            
            shutil.copy(pdf_temp_path, ruta_final)
            
            print(f"✅ PDF guardado correctamente en: {ruta_final}")
            return ruta_final
            
        except Exception as e:
            print(f"❌ Error guardando PDF: {e}")
            return None  
       
    def obtener_movimientos_detallados(self):
        """Obtiene movimientos con información completa"""
        return self.db.get_movimientos_detallados()
    
    def obtener_movimientos_por_bien(self, bien_id):
        """Obtiene todos los movimientos de un bien específico"""
        return self.db.obtener_movimientos_por_bien(bien_id)
    
    def guardar_movimiento_completo(self, datos_formulario, bienes_ids, usuario_actual, archivo_pdf_path=None):
        """Guarda movimiento completo con generación automática de DOCX y PDF opcional"""
        try:
            print(f"🔄 Guardando movimiento completo...")
            
            # 1️⃣ Obtener datos completos de los bienes
            bienes_completos = self._obtener_datos_bienes(bienes_ids)
            if not bienes_completos:
                return None, "❌ No se pudieron obtener datos de los bienes"
            
            # 2️⃣ Generar acta DOCX automáticamente
            ruta_acta_docx = self._generar_acta_automatica(
                datos_formulario['tipo'], 
                bienes_completos, 
                datos_formulario,
                usuario_actual
            )
            
            # 3️⃣ Preparar datos para BD
            datos_bd = {
                "tipo": datos_formulario['tipo'],
                "fecha": datos_formulario['fecha'],
                "responsable": datos_formulario['responsable'],
                "responsable_nombre": datos_formulario['responsable_nombre'],
                "responsable_apellido": datos_formulario['responsable_apellido'],
                "responsable_dni_cuit": datos_formulario['responsable_dni_cuit'],
                "responsable_institucional": datos_formulario['responsable_institucional'],
                "observaciones": datos_formulario['observaciones'],
                "numero_transferencia": datos_formulario['numero_transferencia'],
                "archivo_path_docx": ruta_acta_docx if ruta_acta_docx and not ruta_acta_docx.startswith("❌") else ""
            }
            
            # 4️⃣ Crear movimiento en BD
            movimiento_id = self.db.add_movimiento(datos_bd, bienes_ids)
            
            if not movimiento_id:
                return None, "❌ Error al crear movimiento en base de datos"
            
            # 5️⃣ Si hay PDF, guardarlo CORRECTAMENTE y actualizar BD
            if archivo_pdf_path and os.path.exists(archivo_pdf_path):
                # Guardar PDF en actas_local/ con nombre descriptivo
                ruta_pdf_final = self._guardar_pdf_correctamente(
                    archivo_pdf_path, 
                    movimiento_id, 
                    datos_formulario
                )
                
                if ruta_pdf_final:
                    # Actualizar BD con la nueva ruta
                    if self.db.actualizar_pdf_movimiento(movimiento_id, ruta_pdf_final):
                        print(f"✅ PDF guardado correctamente en BD: {ruta_pdf_final}")
                    else:
                        print(f"⚠️ PDF guardado pero no se pudo actualizar BD: {ruta_pdf_final}")
                else:
                    print(f"⚠️ No se pudo guardar el PDF: {archivo_pdf_path}")
            
            # 6️⃣ Abrir carpeta y preguntar por PDF si se generó acta
            if ruta_acta_docx and not ruta_acta_docx.startswith("❌"):
                self._abrir_carpeta_actas(ruta_acta_docx)
                # ❌ ELIMINADA la llamada al diálogo molesto
                print(f"📄 Acta generada: {ruta_acta_docx}")
                print("💡 Podés subir el PDF firmado después desde la lista de movimientos.")
            
            return movimiento_id, "✅ Movimiento registrado correctamente"
            
        except Exception as e:
            error_msg = f"❌ Error guardando movimiento completo: {str(e)}"
            print(error_msg)
            return None, error_msg    