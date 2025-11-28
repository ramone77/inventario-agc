"""
🏗️ GESTOR DE MOVIMIENTOS - Sistema de Inventario AGC  
Lógica de negocio para movimientos - CON GENERACIÓN AUTOMÁTICA DE ACTAS
"""

from database.db_manager import DB
from generador_actas import GeneradorActas
from datetime import datetime


class MovimientoManager:
    """Maneja la lógica de negocio para movimientos CON ACTAS AUTOMÁTICAS"""
    
    def __init__(self, db: DB):
        self.db = db
        self.generador_actas = GeneradorActas()  # Instanciamos el generador
    
    def crear_movimiento(self, datos_movimiento, bienes_ids, usuario_actual):
        """Crea un movimiento CON GENERACIÓN AUTOMÁTICA DE ACTA"""
        try:
            # 1️⃣ PRIMERO: Obtener datos completos de los bienes
            bienes_completos = self._obtener_datos_bienes(bienes_ids)
            if not bienes_completos:
                return None, "❌ No se pudieron obtener datos de los bienes"
            
            # 2️⃣ SEGUNDO: Generar el acta automáticamente
            ruta_acta = self._generar_acta_automatica(
                datos_movimiento['tipo'], 
                bienes_completos, 
                datos_movimiento,
                usuario_actual
            )
            
            if ruta_acta and not ruta_acta.startswith("❌"):
                # 3️⃣ TERCERO: Guardar ruta del acta en el movimiento
                datos_movimiento['archivo_path'] = ruta_acta
                print(f"✅ Acta generada: {ruta_acta}")
                # ✅ NUEVO: Abrir carpeta de actas
                self._abrir_carpeta_actas(ruta_acta)
                # ✅ NUEVO: Preguntar si quiere subir acta firmada
                self._preguntar_subir_acta_firmada(ruta_acta)
            else:
                datos_movimiento['archivo_path'] = ""
                print(f"⚠️ No se pudo generar acta: {ruta_acta}")
            
            # 4️⃣ CUARTO: Crear el movimiento en la BD
            movimiento_id = self.db.add_movimiento(datos_movimiento, bienes_ids)
            
            return movimiento_id, "✅ Movimiento creado exitosamente"
            
        except Exception as e:
            error_msg = f"❌ Error creando movimiento: {str(e)}"
            print(error_msg)
            return None, error_msg
    
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

    def _preguntar_subir_acta_firmada(self, ruta_acta):
        """Pregunta si quiere subir el acta firmada"""
        try:
            from PyQt5.QtWidgets import QMessageBox, QFileDialog
            import shutil
            
            respuesta = QMessageBox.question(
                None,  # Usar None para que sea diálogo global
                "Acta Generada",
                "¿Querés subir el acta firmada ahora?\n\n"
                "• Sí: Seleccioná el PDF firmado\n"
                "• No: Podés subirlo después desde el historial",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                # Seleccionar PDF firmado
                path, _ = QFileDialog.getOpenFileName(
                    None, "Seleccionar Acta Firmada", "", "PDF (*.pdf)"
                )
                if path:
                    # Reemplazar el acta generada por la firmada
                    shutil.copy(path, ruta_acta)
                    print(f"✅ Acta firmada subida: {ruta_acta}")
                    
        except Exception as e:
            print(f"⚠️ Error en diálogo acta firmada: {e}")
        
    def obtener_movimientos_detallados(self):
        """Obtiene movimientos con información completa"""
        return self.db.get_movimientos_detallados()
    
    def obtener_movimientos_por_bien(self, bien_id):
        """Obtiene todos los movimientos de un bien específico"""
        return self.db.obtener_movimientos_por_bien(bien_id)