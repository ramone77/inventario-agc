"""
📋 DIÁLOGO DE HISTORIAL - Sistema de Inventario AGC
Muestra timeline completo de movimientos de un bien
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QTableWidget, QTableWidgetItem, QPushButton,
                           QHeaderView, QTextEdit, QGroupBox, QMessageBox,
                           QTabWidget, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices
import os
from datetime import datetime


class HistorialDialog(QDialog):
    """Diálogo que muestra el historial completo de movimientos de un bien"""
    
    def __init__(self, db, bien, parent=None):
        super().__init__(parent)
        self.db = db
        self.bien = bien
        self.setWindowTitle(f"📋 Historial - {bien['ficha']}")
        self.setMinimumSize(900, 600)
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
        """Configura la interfaz del historial"""
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
        self.tabla_movimientos.setColumnCount(6)
        self.tabla_movimientos.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Responsable", "DNI/CUIT", "Área", "PDF"
        ])
        
        # Configurar header
        header = self.tabla_movimientos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Tipo
        header.setSectionResizeMode(2, QHeaderView.Stretch)          # Responsable
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # DNI
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Área
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # PDF
        
        self.tabla_movimientos.doubleClicked.connect(self.abrir_pdf_movimiento)
        
        movimientos_layout.addWidget(self.tabla_movimientos)
        layout.addWidget(movimientos_group)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        self.btn_ver_pdf = QPushButton("📎 Abrir PDF Seleccionado")
        self.btn_ver_pdf.clicked.connect(self.abrir_pdf_seleccionado)
        self.btn_ver_pdf.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        
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
        """)
        
        btn_layout.addWidget(self.btn_ver_pdf)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cerrar)
        layout.addLayout(btn_layout)

    def cargar_historial(self):
        """Carga el historial de movimientos del bien"""
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
                archivo_pdf = mov.get('archivo_path', '')
                if archivo_pdf and os.path.exists(archivo_pdf):
                    pdf_text = "📎 PDF"
                else:
                    pdf_text = ""
                
                # Llenar tabla
                self.tabla_movimientos.setItem(i, 0, QTableWidgetItem(fecha_str))
                self.tabla_movimientos.setItem(i, 1, QTableWidgetItem(f"{tipo_icono}{tipo}"))
                self.tabla_movimientos.setItem(i, 2, QTableWidgetItem(responsable_completo))
                self.tabla_movimientos.setItem(i, 3, QTableWidgetItem(dni_cuit))
                self.tabla_movimientos.setItem(i, 4, QTableWidgetItem(area))
                self.tabla_movimientos.setItem(i, 5, QTableWidgetItem(pdf_text))
            
            print(f"✅ Historial cargado: {len(movimientos)} movimientos")
            
        except Exception as e:
            print(f"❌ Error cargando historial: {e}")
            self.tabla_movimientos.setRowCount(1)
            self.tabla_movimientos.setItem(0, 0, QTableWidgetItem(f"Error cargando historial: {str(e)}"))

    def abrir_pdf_seleccionado(self):
        """Abre el PDF del movimiento seleccionado"""
        try:
            fila = self.tabla_movimientos.currentRow()
            if fila >= 0:
                archivo_pdf = self._obtener_pdf_de_fila(fila)
                if archivo_pdf:
                    self._abrir_archivo(archivo_pdf)
                else:
                    QMessageBox.information(self, "PDF", "El movimiento seleccionado no tiene PDF asociado")
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
                archivo_pdf = mov.get('archivo_path', '')
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