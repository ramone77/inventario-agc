"""
🏗️ GESTOR DE MOVIMIENTOS - Sistema de Inventario AGC  
Lógica de negocio para movimientos - CON GENERACIÓN AUTOMÁTICA DE ACTAS
"""

import os
import shutil  # ← AÑADE ESTA LÍNEA
import json
from datetime import datetime
from pathlib import Path

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
        """Guarda PDF en local Y en red si está disponible - VERSIÓN CON DEPURACIÓN COMPLETA"""
        try:
            print(f"🔍 DEBUG _guardar_pdf_correctamente LLAMADO")
            print(f"   PDF temp: {pdf_temp_path}")
            print(f"   Mov ID: {movimiento_id}")
            print(f"   Tipo movimiento: {datos_movimiento.get('tipo', 'N/A')}")
            
            import os
            import shutil
            from datetime import datetime
            from config.settings import get_config, get_modo_trabajo
            
            config = get_config()
            modo = get_modo_trabajo()
            
            print(f"   Modo trabajo: {modo}")
            print(f"   Carpeta red config: {config.get('actas_folder_red', 'NO CONFIGURADO')}")
            print(f"   Carpeta local config: {config.get('actas_folder_local', 'NO CONFIGURADO')}")
            
            # 1. Nombre único del archivo
            responsable = ""
            if datos_movimiento.get('responsable_nombre'):
                responsable += datos_movimiento['responsable_nombre'].replace(" ", "_")
            if datos_movimiento.get('responsable_apellido'):
                responsable += "_" + datos_movimiento['responsable_apellido'].replace(" ", "_")
            
            if not responsable:
                responsable = "SIN_RESPONSABLE"
            
            tipo_mov = datos_movimiento.get('tipo', 'ENTREGA').upper().replace(" ", "_")
            fecha = datetime.now().strftime('%Y%m%d')
            timestamp = datetime.now().strftime('%H%M%S')
            
            nombre_pdf = f"ACTA_{tipo_mov}_{responsable}_{fecha}_{timestamp}.pdf"
            print(f"   Nombre PDF generado: {nombre_pdf}")
            
            # 2. GUARDAR LOCALMENTE (SIEMPRE)
            # Crear carpeta si no existe
            carpeta_local = config["actas_folder_local"]
            print(f"   Creando carpeta local: {carpeta_local}")
            os.makedirs(carpeta_local, exist_ok=True)
            
            ruta_local = os.path.join(carpeta_local, nombre_pdf)
            print(f"   Ruta local completa: {ruta_local}")
            
            print(f"   Copiando a local...")
            shutil.copy(pdf_temp_path, ruta_local)
            print(f"✅ PDF guardado localmente: {ruta_local}")
            print(f"   ¿Existe local después de copiar?: {os.path.exists(ruta_local)}")
            
            # 3. GUARDAR EN RED SI ES NECESARIO
            ruta_red = None
            print(f"   Modo actual: {modo}")
            print(f"   ¿Modo diferente de local_solo?: {modo != 'local_solo'}")
            
            if modo != "local_solo":  # Solo si no estamos en modo solo local
                print("   🔄 Intentando guardar en red...")
                try:
                    # Verificar si la carpeta de red es accesible
                    carpeta_red = config["actas_folder_red"]
                    print(f"   Carpeta red: {carpeta_red}")
                    
                    # Verificar si el directorio padre existe
                    directorio_padre_red = os.path.dirname(carpeta_red)
                    print(f"   Directorio padre red: {directorio_padre_red}")
                    print(f"   ¿Existe padre red?: {os.path.exists(directorio_padre_red)}")
                    
                    if os.path.exists(directorio_padre_red):
                        print(f"   Creando carpeta red si no existe...")
                        os.makedirs(carpeta_red, exist_ok=True)
                        
                        ruta_red = os.path.join(carpeta_red, nombre_pdf)
                        print(f"   Ruta red completa: {ruta_red}")
                        
                        print(f"   Copiando a red...")
                        shutil.copy(pdf_temp_path, ruta_red)
                        print(f"🌐 PDF guardado en red: {ruta_red}")
                        print(f"   ¿Existe red después de copiar?: {os.path.exists(ruta_red)}")
                    else:
                        print(f"⚠️ Directorio padre de red NO existe: {directorio_padre_red}")
                        
                except Exception as e:
                    print(f"⚠️ ERROR guardando en red: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    ruta_red = None
            else:
                print("   📭 Modo local_solo - No se guarda en red")
            
            # 4. Devolver la ruta que usará la BD
            if modo == "red_directo" and ruta_red:
                print(f"   Devolviendo ruta de red (modo red_directo): {ruta_red}")
                return ruta_red
            else:
                print(f"   Devolviendo ruta local: {ruta_local}")
                return ruta_local
            
        except Exception as e:
            print(f"❌ Error guardando PDF: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"🔍 DEBUG guardar_movimiento_completo INICIO")
            print(f"   archivo_pdf_path recibido: {archivo_pdf_path}")
            print(f"   ¿Existe PDF?: {archivo_pdf_path and os.path.exists(archivo_pdf_path)}")
            
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