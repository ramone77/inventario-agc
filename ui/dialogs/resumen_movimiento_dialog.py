"""
🔍 DIÁLOGO DE RESUMEN DE MOVIMIENTO MEJORADO - Sistema de Inventario AGC
Muestra un resumen COMPLETO y DETALLADO de un movimiento seleccionado
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QPushButton, QGroupBox, QScrollArea, QWidget, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices, QFont
import os


class ResumenMovimientoDialog(QDialog):
    """Diálogo para mostrar un resumen COMPLETO y detallado de un movimiento"""
    
    def __init__(self, movimiento, bienes_movimiento, parent=None):
        super().__init__(parent)
        self.movimiento = movimiento
        self.bienes_movimiento = bienes_movimiento
        self.parent = parent
        self.setWindowTitle(f"🔍 Resumen Detallado - Movimiento #{movimiento['id']}")
        self.setMinimumSize(900, 700)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # === PESTAÑAS PARA ORGANIZAR LA INFORMACIÓN ===
        self.tabs = QTabWidget()
        
        # Pestaña 1: Información General
        self._crear_tab_informacion_general()
        
        # Pestaña 2: Bienes Involucrados (Tabla)
        self._crear_tab_bienes_detallados()
        
        # Pestaña 3: Resumen Ejecutivo
        self._crear_tab_resumen_ejecutivo()
        
        layout.addWidget(self.tabs)
        
        # === BOTONES DE ACCIÓN ===
        self._crear_botones_accion(layout)
    
    def _crear_tab_informacion_general(self):
        """Crea la pestaña de información general del movimiento"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # === ENCABEZADO PRINCIPAL ===
        header_group = QGroupBox("📋 INFORMACIÓN DEL MOVIMIENTO")
        header_group.setStyleSheet(self._get_estilo_grupo())
        header_layout = QVBoxLayout(header_group)
        
        # Fila 1: Tipo, Fecha, N° Transferencia
        fila1 = QHBoxLayout()
        tipo_label = QLabel(f"<b>Tipo:</b> {self.movimiento['tipo']}")
        tipo_label.setStyleSheet("color: #2c3e50; font-size: 14px;")
        
        fecha_label = QLabel(f"<b>Fecha:</b> {self._formatear_fecha(self.movimiento['fecha'])}")
        num_label = QLabel(f"<b>N° Transferencia:</b> {self.movimiento['numero_transferencia'] or 'N/A'}")
        
        fila1.addWidget(tipo_label)
        fila1.addWidget(fecha_label)
        fila1.addWidget(num_label)
        fila1.addStretch()
        header_layout.addLayout(fila1)
        
        # ID del movimiento
        id_label = QLabel(f"<b>ID Movimiento:</b> #{self.movimiento['id']}")
        id_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        header_layout.addWidget(id_label)
        
        layout.addWidget(header_group)
        
        # === INFORMACIÓN DEL RESPONSABLE ===
        grupo_responsable = QGroupBox("👤 INFORMACIÓN DEL RESPONSABLE")
        grupo_responsable.setStyleSheet(self._get_estilo_grupo())
        responsable_layout = QVBoxLayout(grupo_responsable)
        
        # Usar datos separados si están disponibles, sino usar el campo responsable completo
        if self.movimiento.get('responsable_nombre') or self.movimiento.get('responsable_apellido'):
            responsable_nombre = QLabel(f"<b>Nombre:</b> {self.movimiento.get('responsable_nombre', 'N/A')}")
            responsable_apellido = QLabel(f"<b>Apellido:</b> {self.movimiento.get('responsable_apellido', 'N/A')}")
            responsable_dni = QLabel(f"<b>DNI/CUIT:</b> {self.movimiento.get('responsable_dni_cuit', 'N/A')}")
            responsable_institucional = QLabel(f"<b>Institucional:</b> {self.movimiento.get('responsable_institucional', 'N/A')}")
            
            responsable_layout.addWidget(responsable_nombre)
            responsable_layout.addWidget(responsable_apellido)
            responsable_layout.addWidget(responsable_dni)
            responsable_layout.addWidget(responsable_institucional)
        else:
            # Fallback al campo responsable completo
            responsable_completo = QLabel(f"<b>Responsable:</b> {self.movimiento['responsable']}")
            responsable_layout.addWidget(responsable_completo)
        
        layout.addWidget(grupo_responsable)
        
        # === OBSERVACIONES ===
        grupo_observaciones = QGroupBox("📝 OBSERVACIONES Y COMENTARIOS")
        grupo_observaciones.setStyleSheet(self._get_estilo_grupo())
        observaciones_layout = QVBoxLayout(grupo_observaciones)
        
        observaciones_text = QTextEdit()
        observaciones_text.setPlainText(self.movimiento.get('observaciones', 'No hay observaciones registradas.'))
        observaciones_text.setMaximumHeight(120)
        observaciones_text.setReadOnly(True)
        observaciones_layout.addWidget(observaciones_text)
        
        layout.addWidget(grupo_observaciones)
        
        # === ESTADÍSTICAS RÁPIDAS ===
        grupo_stats = QGroupBox("📊 ESTADÍSTICAS DEL MOVIMIENTO")
        grupo_stats.setStyleSheet(self._get_estilo_grupo())
        stats_layout = QHBoxLayout(grupo_stats)
        
        # Cantidad de bienes
        cant_bienes = len(self.bienes_movimiento)
        stats_bienes = QLabel(f"<b>Total de Bienes:</b> {cant_bienes}")
        stats_bienes.setStyleSheet("color: #27ae60; font-size: 13px;")
        
        # PRDs únicos
        prds_unicos = set(bien.get('prd', '') for bien in self.bienes_movimiento if bien.get('prd'))
        stats_prds = QLabel(f"<b>PRDs Involucrados:</b> {len(prds_unicos)}")
        stats_prds.setStyleSheet("color: #2980b9; font-size: 13px;")
        
        # Tipos únicos
        tipos_unicos = set(bien.get('tipo', '') for bien in self.bienes_movimiento if bien.get('tipo'))
        stats_tipos = QLabel(f"<b>Tipos de Bienes:</b> {len(tipos_unicos)}")
        stats_tipos.setStyleSheet("color: #e67e22; font-size: 13px;")
        
        stats_layout.addWidget(stats_bienes)
        stats_layout.addWidget(stats_prds)
        stats_layout.addWidget(stats_tipos)
        stats_layout.addStretch()
        
        layout.addWidget(grupo_stats)
        
        layout.addStretch()
        self.tabs.addTab(tab, "📋 Información General")
    
    def _crear_tab_bienes_detallados(self):
        """Crea la pestaña con tabla detallada de bienes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grupo_bienes = QGroupBox(f"📦 BIENES INVOLUCRADOS ({len(self.bienes_movimiento)})")
        grupo_bienes.setStyleSheet(self._get_estilo_grupo())
        bienes_layout = QVBoxLayout(grupo_bienes)
        
        # Crear tabla de bienes
        self.tabla_bienes = QTableWidget()
        self._configurar_tabla_bienes()
        bienes_layout.addWidget(self.tabla_bienes)
        
        layout.addWidget(grupo_bienes)
        self.tabs.addTab(tab, "📦 Bienes Detallados")
    
    def _configurar_tabla_bienes(self):
        """Configura la tabla de bienes con columnas relevantes"""
        columnas = [
            "Ficha", "Tipo", "Marca", "Modelo", "Serie", "PRD", 
            "Estado", "Nombre", "Apellido", "DNI/CUIT"
        ]
        
        self.tabla_bienes.setColumnCount(len(columnas))
        self.tabla_bienes.setHorizontalHeaderLabels(columnas)
        self.tabla_bienes.setRowCount(len(self.bienes_movimiento))
        
        # Llenar tabla con datos
        for row, bien in enumerate(self.bienes_movimiento):
            self.tabla_bienes.setItem(row, 0, QTableWidgetItem(bien.get('ficha', '')))
            self.tabla_bienes.setItem(row, 1, QTableWidgetItem(bien.get('tipo', '')))
            self.tabla_bienes.setItem(row, 2, QTableWidgetItem(bien.get('marca', '')))
            self.tabla_bienes.setItem(row, 3, QTableWidgetItem(bien.get('modelo', '')))
            self.tabla_bienes.setItem(row, 4, QTableWidgetItem(bien.get('serie', '')))
            self.tabla_bienes.setItem(row, 5, QTableWidgetItem(bien.get('prd', '')))
            self.tabla_bienes.setItem(row, 6, QTableWidgetItem(bien.get('estado', '')))
            self.tabla_bienes.setItem(row, 7, QTableWidgetItem(bien.get('nombre', '')))
            self.tabla_bienes.setItem(row, 8, QTableWidgetItem(bien.get('apellido', '')))
            self.tabla_bienes.setItem(row, 9, QTableWidgetItem(bien.get('dni_cuit', '')))
        
        # Ajustar columnas
        header = self.tabla_bienes.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)
        
        # Conectar doble click para ver historial del bien
        self.tabla_bienes.doubleClicked.connect(self._ver_historial_bien)
    
    def _crear_tab_resumen_ejecutivo(self):
        """Crea la pestaña de resumen ejecutivo"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grupo_resumen = QGroupBox("📈 RESUMEN EJECUTIVO")
        grupo_resumen.setStyleSheet(self._get_estilo_grupo())
        resumen_layout = QVBoxLayout(grupo_resumen)
        
        # Resumen en texto
        resumen_text = QTextEdit()
        resumen_text.setReadOnly(True)
        resumen_text.setHtml(self._generar_html_resumen())
        resumen_layout.addWidget(resumen_text)
        
        layout.addWidget(grupo_resumen)
        self.tabs.addTab(tab, "📈 Resumen Ejecutivo")
    
    def _generar_html_resumen(self):
        """Genera un resumen ejecutivo en HTML"""
        tipo_movimiento = self.movimiento['tipo']
        fecha = self._formatear_fecha(self.movimiento['fecha'])
        cant_bienes = len(self.bienes_movimiento)
        
        # Estadísticas de bienes
        tipos = {}
        estados = {}
        for bien in self.bienes_movimiento:
            tipo = bien.get('tipo', 'No especificado')
            estado = bien.get('estado', 'No especificado')
            tipos[tipo] = tipos.get(tipo, 0) + 1
            estados[estado] = estados.get(estado, 0) + 1
        
        html = f"""
        <h3 style='color: #2c3e50;'>Resumen del Movimiento #{self.movimiento['id']}</h3>
        <p><b>Tipo:</b> {tipo_movimiento}</p>
        <p><b>Fecha:</b> {fecha}</p>
        <p><b>Total de Bienes:</b> <span style='color: #27ae60;'>{cant_bienes}</span></p>
        
        <h4 style='color: #34495e;'>Distribución por Tipo:</h4>
        <ul>
        """
        
        for tipo, cantidad in tipos.items():
            html += f"<li>{tipo}: <b>{cantidad}</b></li>"
        
        html += """
        </ul>
        
        <h4 style='color: #34495e;'>Estados de los Bienes:</h4>
        <ul>
        """
        
        for estado, cantidad in estados.items():
            color = self._get_color_estado(estado)
            html += f"<li><span style='color: {color};'>{estado}</span>: <b>{cantidad}</b></li>"
        
        html += """
        </ul>
        
        <h4 style='color: #34495e;'>PRDs Involucrados:</h4>
        <ul>
        """
        
        prds = set(bien.get('prd', '') for bien in self.bienes_movimiento if bien.get('prd'))
        for prd in sorted(prds):
            if prd:  # Solo mostrar PRDs no vacíos
                html += f"<li>{prd}</li>"
        
        html += "</ul>"
        
        return html
    
    def _crear_botones_accion(self, layout):
        """Crea los botones de acción en la parte inferior"""
        botones_layout = QHBoxLayout()
        
        # Botones para abrir archivos
        archivo_pdf = self.movimiento.get('archivo_path_pdf', '')
        archivo_docx = self.movimiento.get('archivo_path_docx', '')
        
        self.btn_abrir_pdf = QPushButton("📄 Abrir PDF del Movimiento")
        self.btn_abrir_pdf.setEnabled(bool(archivo_pdf and os.path.exists(archivo_pdf)))
        self.btn_abrir_pdf.clicked.connect(self.abrir_pdf)
        self.btn_abrir_pdf.setToolTip(archivo_pdf if archivo_pdf else "No hay PDF disponible")
        
        self.btn_abrir_docx = QPushButton("📝 Abrir DOCX del Movimiento")
        self.btn_abrir_docx.setEnabled(bool(archivo_docx and os.path.exists(archivo_docx)))
        self.btn_abrir_docx.clicked.connect(self.abrir_docx)
        self.btn_abrir_docx.setToolTip(archivo_docx if archivo_docx else "No hay DOCX disponible")
        
        # Botón para ver historial (solo si hay un bien seleccionado)
        self.btn_ver_historial = QPushButton("📊 Ver Historial del Bien")
        self.btn_ver_historial.clicked.connect(self._ver_historial_bien_seleccionado)
        self.btn_ver_historial.setToolTip("Ver historial del bien seleccionado en la tabla")
        
        btn_cerrar = QPushButton("✅ Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        
        botones_layout.addWidget(self.btn_abrir_pdf)
        botones_layout.addWidget(self.btn_abrir_docx)
        botones_layout.addWidget(self.btn_ver_historial)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_cerrar)
        
        layout.addLayout(botones_layout)
    
    def _ver_historial_bien_seleccionado(self):
        """Muestra el historial del bien seleccionado en la tabla"""
        current_row = self.tabla_bienes.currentRow()
        if current_row >= 0:
            self._ver_historial_bien(self.tabla_bienes.model().index(current_row, 0))
        else:
            QMessageBox.information(self, "Selección requerida", 
                                "Por favor, selecciona un bien de la tabla para ver su historial.")
    
    def _ver_historial_bien(self, index):
        """Abre el diálogo de historial para un bien específico"""
        try:
            row = index.row()
            if row >= 0 and row < len(self.bienes_movimiento):
                bien = self.bienes_movimiento[row]
                from ui.dialogs.historial_dialog import HistorialDialog
                dialog = HistorialDialog(self.parent.db, bien, self.parent)
                dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el historial:\n{str(e)}")
    
    def _get_estilo_grupo(self):
        """Retorna el estilo CSS para los grupos"""
        return """
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
        """
    
    def _formatear_fecha(self, fecha_str):
        """Formatea la fecha para mejor visualización"""
        try:
            from datetime import datetime
            if ' ' in fecha_str:
                fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                return fecha_dt.strftime("%d/%m/%Y %H:%M")
            else:
                fecha_dt = datetime.strptime(fecha_str, "%Y-%m-%d")
                return fecha_dt.strftime("%d/%m/%Y")
        except:
            return fecha_str
    
    def _get_color_estado(self, estado):
        """Retorna color según el estado del bien"""
        colores = {
            'en depósito': '#27ae60',
            'asignado': '#3498db', 
            'baja definitiva': '#e74c3c',
            'en reparación': '#f39c12',
            'stock': '#27ae60',
            'disponible': '#27ae60'
        }
        return colores.get(estado.lower(), '#7f8c8d')
    
    def abrir_pdf(self):
        """Abre el archivo PDF asociado al movimiento"""
        archivo_pdf = self.movimiento.get('archivo_path_pdf', '')
        if archivo_pdf and os.path.exists(archivo_pdf):
            try:
                QDesktopServices.openUrl(f"file:///{archivo_pdf}")
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"No se pudo abrir el PDF:\n{str(e)}")
        else:
            QMessageBox.warning(self, "❌ No encontrado", "El archivo PDF no existe o no está disponible.")
    
    def abrir_docx(self):
        """Abre el archivo DOCX asociado al movimiento"""
        archivo_docx = self.movimiento.get('archivo_path_docx', '')
        if archivo_docx and os.path.exists(archivo_docx):
            try:
                QDesktopServices.openUrl(f"file:///{archivo_docx}")
            except Exception as e:
                QMessageBox.critical(self, "❌ Error", f"No se pudo abrir el DOCX:\n{str(e)}")
        else:
            QMessageBox.warning(self, "❌ No encontrado", "El archivo DOCX no existe o no está disponible.")