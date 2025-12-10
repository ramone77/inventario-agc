"""
📋 DIÁLOGO DE HISTORIAL - Sistema de Inventario AGC
Muestra timeline completo de movimientos de un bien
CON CARGA MANUAL DE PDFs
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTableWidget, QTableWidgetItem, QPushButton,
                           QHeaderView, QTextEdit, QGroupBox, QMessageBox,
                           QTabWidget, QWidget, QFileDialog, QProgressBar, QMenu )
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices
import os
import shutil
from datetime import datetime


class HistorialDialog(QDialog):
    """Diálogo que muestra el historial completo de movimientos de un bien"""
    
    def __init__(self, db, bien, parent=None):
        super().__init__(parent)
        self.db = db
        self.bien = bien
        self.setWindowTitle(f"📋 Historial - {bien['ficha']}")
        self.setMinimumSize(1000, 700)  # ← Aumentado para nuevos botones
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        self._setup_ui()
        self.cargar_historial()

    def _setup_ui(self):
        """Configura la interfaz del historial - VERSIÓN CON GESTIÓN DE PDFs"""
        layout = QVBoxLayout(self)
        
        # Header con información del bien
        header = QLabel(f"📋 HISTORIAL DE MOVIMIENTOS - {self.bien['ficha']}")
        header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: #3498db;
                color: white;
                border-radius: 5px;
                margin-bottom: 10px;
            }
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Información rápida del bien
        info_group = QGroupBox("📦 INFORMACIÓN DEL BIEN")
        info_layout = QVBoxLayout(info_group)
        
        info_text = f"""
        <b>Ficha:</b> {self.bien['ficha']} | <b>Tipo:</b> {self.bien['tipo']}
        <b>Marca:</b> {self.bien['marca']} | <b>Modelo:</b> {self.bien['modelo']}
        <b>Serie:</b> {self.bien['serie']} | <b>Estado actual:</b> {self.bien['estado']}
        <b>Responsable actual:</b> {self.bien.get('nombre', '')} {self.bien.get('apellido', '')}
        """
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 11px; padding: 8px;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)
        
        # Timeline de movimientos
        movimientos_group = QGroupBox("🕒 TIMELINE DE MOVIMIENTOS")
        movimientos_layout = QVBoxLayout(movimientos_group)
        
        # Tabla de movimientos
        self.tabla_movimientos = QTableWidget()
        self.tabla_movimientos.setColumnCount(7)
        self.tabla_movimientos.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Responsable", "DNI/CUIT", "Área", "PDF", "Acciones"
        ])
        
        # Configurar header
        header = self.tabla_movimientos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Tipo
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Responsable
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # DNI
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Área
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # PDF
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Acciones
        
        self.tabla_movimientos.doubleClicked.connect(self.abrir_pdf_movimiento)
        
        movimientos_layout.addWidget(self.tabla_movimientos)
        layout.addWidget(movimientos_group)
        
        # ✅ NUEVA SECCIÓN: GESTIÓN DE PDFs
        gestion_group = QGroupBox("📥 GESTIÓN AVANZADA DE PDFs")
        gestion_layout = QVBoxLayout(gestion_group)
        
        gestion_text = """
        <b>Gestión completa de documentos:</b><br>
        • <b>Agregar:</b> Adjuntar PDFs a movimientos existentes<br>
        • <b>Reemplazar:</b> Cambiar PDFs subidos incorrectamente<br>
        • <b>Eliminar:</b> Quitar PDFs que no corresponden<br>
        • <b>Ver info:</b> Detalles del archivo actual<br><br>
        
        <b>Instrucciones:</b><br>
        1. Selecciona un movimiento en la tabla<br>
        2. Usa el botón \"✏️ Gestionar PDF\" para las opciones<br>
        3. O usa los botones individuales en la columna \"Acciones\"
        """
        
        gestion_label = QLabel(gestion_text)
        gestion_label.setStyleSheet("font-size: 10px; padding: 8px; color: #555;")
        gestion_label.setWordWrap(True)
        gestion_layout.addWidget(gestion_label)
        layout.addWidget(gestion_group)
        
        # ✅ BOTONES DE ACCIÓN MEJORADOS
        btn_layout = QHBoxLayout()
        
        # ✅ NUEVO BOTÓN: GESTIÓN DE PDFs CON MENÚ CONTEXTUAL
        self.btn_gestion_pdf = QPushButton("✏️ Gestionar PDF")
        self.btn_gestion_pdf.clicked.connect(self.mostrar_menu_gestion_pdf)
        self.btn_gestion_pdf.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.btn_gestion_pdf.setToolTip("Gestionar PDF del movimiento seleccionado")
        
        # Botón actualizar
        self.btn_actualizar = QPushButton("🔄 Actualizar Historial")
        self.btn_actualizar.clicked.connect(self.cargar_historial)
        self.btn_actualizar.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        
        # Botón cerrar
        self.btn_cerrar = QPushButton("✅ Cerrar")
        self.btn_cerrar.clicked.connect(self.accept)
        self.btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        
        btn_layout.addWidget(self.btn_gestion_pdf)
        btn_layout.addWidget(self.btn_actualizar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cerrar)
        layout.addLayout(btn_layout)

    def cargar_historial(self):
        """Carga el historial de movimientos del bien - VERSIÓN MEJORADA"""
        try:
            # Obtener movimientos del bien
            bien_id = self.bien['id']
            movimientos = self.db.obtener_movimientos_por_bien(bien_id)
            
            print(f"📊 Cargando historial - Bien ID: {bien_id}, Movimientos: {len(movimientos)}")
            
            if not movimientos:
                self.tabla_movimientos.setRowCount(1)
                self.tabla_movimientos.setItem(0, 0, QTableWidgetItem("No se encontraron movimientos para este bien"))
                return
            
            # Ordenar por fecha (más reciente primero)
            movimientos_ordenados = sorted(movimientos, 
                                         key=lambda x: x.get('fecha', ''), 
                                         reverse=True)
            
            self.tabla_movimientos.setRowCount(len(movimientos_ordenados))
            
            for i, mov in enumerate(movimientos_ordenados):
                # Fecha formateada
                fecha_original = mov.get('fecha', '')
                try:
                    fecha_dt = datetime.strptime(fecha_original, "%Y-%m-%d %H:%M:%S")
                    fecha_str = fecha_dt.strftime("%d/%m/%Y %H:%M")
                except:
                    fecha_str = fecha_original
                
                # Tipo de movimiento con icono
                tipo = mov.get('tipo', '')
                if tipo == 'Entrega':
                    tipo_icono = "📤 "
                elif tipo == 'Devolución':
                    tipo_icono = "📥 "
                elif tipo == 'Baja':
                    tipo_icono = "❌ "
                else:
                    tipo_icono = "📋 "
                
                # Responsable
                responsable_nombre = mov.get('responsable_nombre', '')
                responsable_apellido = mov.get('responsable_apellido', '')
                responsable_completo = f"{responsable_nombre} {responsable_apellido}".strip()
                if not responsable_completo:
                    responsable_completo = mov.get('responsable', '')
                
                # DNI/CUIT
                dni_cuit = mov.get('responsable_dni_cuit', '')
                
                # Área/Institucional
                area = mov.get('responsable_institucional', '')
                
                # PDF
                archivo_pdf = mov.get('archivo_path_pdf', '')  # ← ✅ CORRECTO
                if archivo_pdf and os.path.exists(archivo_pdf):
                    pdf_text = "📎 PDF"
                    pdf_tooltip = f"Archivo: {os.path.basename(archivo_pdf)}"
                else:
                    pdf_text = "❌ Sin PDF"
                    pdf_tooltip = "Haz clic en 'Agregar PDF' para adjuntar documento"
                
                # ✅ NUEVO: BOTÓN DE ACCIONES
                movimiento_id = mov.get('id')  # ID del movimiento para actualizar
                
                # Llenar tabla
                self.tabla_movimientos.setItem(i, 0, QTableWidgetItem(fecha_str))
                self.tabla_movimientos.setItem(i, 1, QTableWidgetItem(f"{tipo_icono}{tipo}"))
                self.tabla_movimientos.setItem(i, 2, QTableWidgetItem(responsable_completo))
                self.tabla_movimientos.setItem(i, 3, QTableWidgetItem(dni_cuit))
                self.tabla_movimientos.setItem(i, 4, QTableWidgetItem(area))
                
                # Columna PDF
                pdf_item = QTableWidgetItem(pdf_text)
                pdf_item.setToolTip(pdf_tooltip)
                self.tabla_movimientos.setItem(i, 5, pdf_item)
                
                # ✅ NUEVO: COLUMNA ACCIONES
                if archivo_pdf and os.path.exists(archivo_pdf):
                    # Ya tiene PDF - solo botón de abrir
                    btn_abrir = QPushButton("👁️ Abrir")
                    btn_abrir.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            padding: 4px 8px;
                            border-radius: 3px;
                            font-size: 10px;
                        }
                    """)
                    btn_abrir.clicked.connect(lambda checked, ruta=archivo_pdf: self._abrir_archivo(ruta))
                    self.tabla_movimientos.setCellWidget(i, 6, btn_abrir)
                else:
                    # No tiene PDF - botón para agregar
                    btn_agregar = QPushButton("📎 Agregar PDF")
                    btn_agregar.setStyleSheet("""
                        QPushButton {
                            background-color: #e67e22;
                            color: white;
                            padding: 4px 8px;
                            border-radius: 3px;
                            font-size: 10px;
                            font-weight: bold;
                        }
                        QPushButton:hover {
                            background-color: #d35400;
                        }
                    """)
                    btn_agregar.clicked.connect(lambda checked, mov_id=movimiento_id, fila=i: self.agregar_pdf_manual(mov_id, fila))
                    btn_agregar.setToolTip("Agregar PDF a este movimiento")
                    self.tabla_movimientos.setCellWidget(i, 6, btn_agregar)
            
            print(f"✅ Historial cargado: {len(movimientos)} movimientos")
            
        except Exception as e:
            print(f"❌ Error cargando historial: {e}")
            self.tabla_movimientos.setRowCount(1)
            self.tabla_movimientos.setItem(0, 0, QTableWidgetItem(f"Error cargando historial: {str(e)}"))

    def agregar_pdf_manual(self, movimiento_id, fila_tabla):
        """Agrega un PDF manualmente a un movimiento existente"""
        try:
            if not movimiento_id:
                QMessageBox.warning(self, "Error", "No se pudo identificar el movimiento seleccionado")
                return
            
            # Seleccionar archivo PDF
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Seleccionar PDF para el movimiento", 
                "", 
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return  # Usuario canceló
            
            # Verificar que sea un PDF
            if not file_path.lower().endswith('.pdf'):
                QMessageBox.warning(self, "Error", "Por favor selecciona un archivo PDF válido")
                return
            
            # Generar nombre único para el archivo
            from datetime import datetime
            nombre_original = os.path.basename(file_path)
            nombre_base, extension = os.path.splitext(nombre_original)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_unico = f"movimiento_{movimiento_id}_{timestamp}{extension}"
            
            # Ruta destino en carpeta de actas
            carpeta_actas = self.db.actas_folder
            destino = os.path.join(carpeta_actas, nombre_unico)
            
            # Copiar archivo
            shutil.copy2(file_path, destino)
            
            # Actualizar base de datos
            exito = self.db.actualizar_pdf_movimiento(movimiento_id, destino)
            
            if exito:
                QMessageBox.information(
                    self, 
                    "✅ Éxito", 
                    f"PDF agregado correctamente al movimiento:\n\n"
                    f"• Archivo: {nombre_unico}\n"
                    f"• Movimiento ID: {movimiento_id}\n"
                    f"• Guardado en: {destino}"
                )
                
                # Actualizar la fila en la tabla
                self.actualizar_fila_con_pdf(fila_tabla, destino)
                
            else:
                QMessageBox.critical(self, "❌ Error", "No se pudo actualizar la base de datos")
                # Intentar eliminar el archivo copiado si falló
                if os.path.exists(destino):
                    os.remove(destino)
                    
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error agregando PDF:\n{str(e)}")

    def actualizar_fila_con_pdf(self, fila, ruta_pdf):
        """Actualiza una fila específica después de agregar PDF"""
        try:
            # Actualizar columna PDF
            pdf_item = QTableWidgetItem("📎 PDF")
            pdf_item.setToolTip(f"Archivo: {os.path.basename(ruta_pdf)}")
            self.tabla_movimientos.setItem(fila, 5, pdf_item)
            
            # Actualizar columna Acciones (reemplazar botón)
            btn_abrir = QPushButton("👁️ Abrir")
            btn_abrir.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                }
            """)
            btn_abrir.clicked.connect(lambda checked, ruta=ruta_pdf: self._abrir_archivo(ruta))
            self.tabla_movimientos.setCellWidget(fila, 6, btn_abrir)
            
            print(f"✅ Fila {fila} actualizada con PDF: {ruta_pdf}")
            
        except Exception as e:
            print(f"❌ Error actualizando fila: {e}")

    def abrir_pdf_seleccionado(self):
        """Abre el PDF del movimiento seleccionado"""
        try:
            fila = self.tabla_movimientos.currentRow()
            if fila >= 0:
                archivo_pdf = self._obtener_pdf_de_fila(fila)
                if archivo_pdf:
                    self._abrir_archivo(archivo_pdf)
                else:
                    QMessageBox.information(self, "PDF", 
                                         "El movimiento seleccionado no tiene PDF asociado.\n\n"
                                         "Usa el botón \"📎 Agregar PDF\" para adjuntar un documento.")
            else:
                QMessageBox.warning(self, "PDF", "Selecciona un movimiento de la tabla")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el PDF:\n{str(e)}")

    def abrir_pdf_movimiento(self, index):
        """Abre PDF al hacer doble click en una fila"""
        try:
            fila = index.row()
            archivo_pdf = self._obtener_pdf_de_fila(fila)
            if archivo_pdf:
                self._abrir_archivo(archivo_pdf)
        except Exception as e:
            print(f"❌ Error abriendo PDF: {e}")

    def _obtener_pdf_de_fila(self, fila):
        """Obtiene la ruta del PDF de una fila específica"""
        try:
            # Obtener el movimiento correspondiente a la fila
            bien_id = self.bien['id']
            movimientos = self.db.obtener_movimientos_por_bien(bien_id)
            movimientos_ordenados = sorted(movimientos, 
                                         key=lambda x: x.get('fecha', ''), 
                                         reverse=True)
            
            if fila < len(movimientos_ordenados):
                mov = movimientos_ordenados[fila]
                archivo_pdf = mov.get('archivo_path_pdf', '')  # ← ✅ CORRECTO
                if archivo_pdf and os.path.exists(archivo_pdf):
                    return archivo_pdf
            return None
        except Exception as e:
            print(f"❌ Error obteniendo PDF de fila: {e}")
            return None

    def _abrir_archivo(self, ruta_archivo):
        """Abre un archivo con la aplicación predeterminada"""
        try:
            import subprocess
            import platform
            
            sistema = platform.system()
            
            if sistema == "Windows":
                os.startfile(ruta_archivo)
            elif sistema == "Darwin":  # macOS
                subprocess.run(["open", ruta_archivo])
            else:  # Linux
                subprocess.run(["xdg-open", ruta_archivo])
                
            print(f"✅ Archivo abierto: {ruta_archivo}")
            
        except Exception as e:
            print(f"❌ Error abriendo archivo: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{ruta_archivo}")
            
    def mostrar_menu_gestion_pdf(self):
        """Muestra menú contextual para gestionar PDF del movimiento seleccionado"""
        try:
            fila = self.tabla_movimientos.currentRow()
            if fila < 0:
                QMessageBox.warning(self, "Gestionar PDF", "Selecciona un movimiento de la tabla primero")
                return
            
            # Obtener información del movimiento seleccionado
            movimiento_id, archivo_pdf_actual = self._obtener_info_movimiento_fila(fila)
            if not movimiento_id:
                QMessageBox.warning(self, "Error", "No se pudo obtener información del movimiento")
                return
            
            # Crear menú contextual
            menu = QMenu(self)
            
            if archivo_pdf_actual and os.path.exists(archivo_pdf_actual):
                # Movimiento CON PDF - Opciones completas
                menu.addAction("👁️ Abrir PDF", lambda: self._abrir_archivo(archivo_pdf_actual))
                menu.addAction("🔄 Reemplazar PDF", lambda: self.reemplazar_pdf(movimiento_id, fila, archivo_pdf_actual))
                menu.addAction("🗑️ Eliminar PDF", lambda: self.eliminar_pdf(movimiento_id, fila))
                menu.addAction("📊 Información del PDF", lambda: self.mostrar_info_pdf(archivo_pdf_actual))
            else:
                # Movimiento SIN PDF - Solo agregar
                menu.addAction("📥 Agregar PDF", lambda: self.agregar_pdf_manual(movimiento_id, fila))
            
            # Mostrar menú en posición del botón
            pos = self.btn_gestion_pdf.mapToGlobal(self.btn_gestion_pdf.rect().bottomLeft())
            menu.exec_(pos)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error mostrando menú: {str(e)}")

    def _obtener_info_movimiento_fila(self, fila):
        """Obtiene ID y PDF del movimiento en una fila específica"""
        try:
            bien_id = self.bien['id']
            movimientos = self.db.obtener_movimientos_por_bien(bien_id)
            movimientos_ordenados = sorted(movimientos, key=lambda x: x.get('fecha', ''), reverse=True)
            
            if fila < len(movimientos_ordenados):
                mov = movimientos_ordenados[fila]
                movimiento_id = mov.get('id')
                # ✅ CORREGIDO: Buscar archivo_path_pdf
                archivo_pdf = mov.get('archivo_path_pdf', '')  # ← SOLO PDF, NO DOCX
                return movimiento_id, archivo_pdf
            return None, None
        except Exception as e:
            print(f"❌ Error obteniendo info de movimiento: {e}")
            return None, None

    def reemplazar_pdf(self, movimiento_id, fila, archivo_actual):
        """Reemplaza un PDF existente por uno nuevo"""
        try:
            # Primero eliminar el archivo actual
            if archivo_actual and os.path.exists(archivo_actual):
                os.remove(archivo_actual)
                print(f"🗑️ PDF anterior eliminado: {archivo_actual}")
            
            # Luego agregar uno nuevo
            self.agregar_pdf_manual(movimiento_id, fila)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reemplazando PDF: {str(e)}")

    def eliminar_pdf(self, movimiento_id, fila):
        """Elimina el PDF de un movimiento"""
        try:
            respuesta = QMessageBox.question(
                self, 
                "Confirmar Eliminación",
                "¿Estás seguro de que quieres eliminar el PDF de este movimiento?\n\n"
                "Esta acción no se puede deshacer.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.Yes:
                # Actualizar base de datos (poner archivo_path como NULL o vacío)
                query = "UPDATE movimientos SET archivo_path = NULL WHERE id = ?"
                self.db.conn.execute(query, (movimiento_id,))
                self.db.conn.commit()
                
                # Actualizar la fila en la tabla
                self.actualizar_fila_sin_pdf(fila)
                
                QMessageBox.information(self, "✅ Éxito", "PDF eliminado correctamente")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error eliminando PDF: {str(e)}")

    def mostrar_info_pdf(self, ruta_pdf):
        """Muestra información detallada del PDF"""
        try:
            if not ruta_pdf or not os.path.exists(ruta_pdf):
                QMessageBox.warning(self, "Info PDF", "No hay PDF asociado a este movimiento")
                return
            
            import os
            from datetime import datetime
            
            stats = os.stat(ruta_pdf)
            tamaño_kb = stats.st_size / 1024
            fecha_modificacion = datetime.fromtimestamp(stats.st_mtime).strftime("%d/%m/%Y %H:%M")
            
            info_text = f"""
            📊 INFORMACIÓN DEL PDF:
            
            📁 Archivo: {os.path.basename(ruta_pdf)}
            📏 Tamaño: {tamaño_kb:.1f} KB
            📅 Modificado: {fecha_modificacion}
            📍 Ruta: {ruta_pdf}
            """
            
            QMessageBox.information(self, "📊 Info PDF", info_text.strip())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error obteniendo info del PDF: {str(e)}")

    def actualizar_fila_sin_pdf(self, fila):
        """Actualiza una fila para mostrar que no tiene PDF"""
        try:
            # Actualizar columna PDF
            pdf_item = QTableWidgetItem("❌ Sin PDF")
            pdf_item.setToolTip("Haz clic en 'Agregar PDF' para adjuntar documento")
            self.tabla_movimientos.setItem(fila, 5, pdf_item)
            
            # Actualizar columna Acciones (botón de agregar)
            btn_agregar = QPushButton("📎 Agregar PDF")
            btn_agregar.setStyleSheet("""
                QPushButton {
                    background-color: #e67e22;
                    color: white;
                    padding: 4px 8px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d35400;
                }
            """)
            
            # Obtener movimiento_id para esta fila
            movimiento_id, _ = self._obtener_info_movimiento_fila(fila)
            if movimiento_id:
                btn_agregar.clicked.connect(lambda checked, mov_id=movimiento_id, f=fila: self.agregar_pdf_manual(mov_id, f))
            
            self.tabla_movimientos.setCellWidget(fila, 6, btn_agregar)
            
            print(f"✅ Fila {fila} actualizada - PDF eliminado")
            
        except Exception as e:
            print(f"❌ Error actualizando fila sin PDF: {e}")
            
    def _resolver_ruta_pdf(self, ruta_almacenada):
        """Resuelve una ruta de PDF (puede ser relativa o absoluta)"""
        try:
            from config.settings import get_config
            
            config = get_config()
            
            # Si ya es una ruta absoluta que existe
            if os.path.exists(ruta_almacenada):
                return ruta_almacenada
            
            # Si es solo un nombre de archivo, buscar en actas_local
            if not os.path.dirname(ruta_almacenada):  # Solo nombre de archivo
                ruta_local = os.path.join(config["actas_folder_local"], ruta_almacenada)
                if os.path.exists(ruta_local):
                    return ruta_local
                
                # Intentar en red también
                ruta_red = os.path.join(config["actas_folder_red"], ruta_almacenada)
                if os.path.exists(ruta_red):
                    return ruta_red
            
            return ruta_almacenada  # Devolver original si no se resuelve
            
        except Exception as e:
            print(f"❌ Error resolviendo ruta PDF: {e}")
            return ruta_almacenada

# Prueba simple
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from database.db_manager import DB
    
    app = QApplication(sys.argv)
    
    # Datos de prueba
    db = DB("inventario_local.db", "actas_generadas")
    bien_prueba = {
        'id': 1,
        'ficha': 'TEST-001',
        'tipo': 'NOTEBOOK', 
        'marca': 'DELL',
        'modelo': 'LATITUDE',
        'serie': 'SN123',
        'estado': 'Asignado',
        'nombre': 'Juan',
        'apellido': 'Pérez'
    }
    
    dialog = HistorialDialog(db, bien_prueba)
    dialog.exec_()
    
    sys.exit(app.exec_())