"""
🔍 DIÁLOGO DE RESUMEN DE MOVIMIENTO OPTIMIZADO - Sistema de Inventario AGC
Versión profesional enfocada en ACTAS FIRMADAS (PDF) - Eliminado DOCX temporal
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QPushButton, QGroupBox, QScrollArea, QWidget, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QProgressBar)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QDesktopServices, QFont, QColor
import os
import datetime


class ResumenMovimientoDialog(QDialog):
    """Diálogo profesional para mostrar resumen COMPLETO de movimiento"""
    
    def __init__(self, movimiento, bienes_movimiento, parent=None):
        super().__init__(parent)
        self.movimiento = movimiento
        self.bienes_movimiento = bienes_movimiento
        self.parent = parent
        self.setWindowTitle(f"🔍 Resumen Detallado - Movimiento #{movimiento['id']}")
        self.setMinimumSize(1000, 750)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # === ENCABEZADO CON COLORES ===
        self._crear_encabezado(layout)
        
        # === PESTAÑAS ORGANIZADAS ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                background: white;
                margin-top: 5px;
            }
            QTabBar::tab {
                background: #e5e7eb;
                border: 1px solid #d1d5db;
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 4px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #3b82f6;
                color: white;
            }
            QTabBar::tab:hover {
                background: #dbeafe;
            }
        """)
        
        # Pestaña 1: Resumen Ejecutivo
        self._crear_tab_resumen_ejecutivo()
        
        # Pestaña 2: Bienes Involucrados
        self._crear_tab_bienes_detallados()
        
        # Pestaña 3: Información Técnica
        self._crear_tab_informacion_tecnica()
        
        layout.addWidget(self.tabs)
        
        # === SECCIÓN DE ACTA FIRMADA (SIEMPRE VISIBLE) ===
        self._crear_seccion_acta_firmada(layout)
        
        # === BOTONES DE ACCIÓN ===
        self._crear_botones_accion(layout)
    
    def _crear_encabezado(self, layout):
        """Crea encabezado visualmente atractivo"""
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e40af, stop:1 #3b82f6);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header_widget)
        
        # Título principal
        titulo = QLabel(f"MOVIMIENTO #{self.movimiento['id']}")
        titulo.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)
        
        # Subtítulo con tipo y fecha
        tipo_color = self._get_color_por_tipo(self.movimiento['tipo'])
        subtitulo = QLabel(
            f"<span style='color: {tipo_color}; font-weight: bold;'>{self.movimiento['tipo']}</span> • "
            f"<span style='color: #dbeafe;'>{self._formatear_fecha(self.movimiento['fecha'])}</span> • "
            f"<span style='color: #dbeafe;'>{len(self.bienes_movimiento)} bienes</span>"
        )
        subtitulo.setStyleSheet("font-size: 14px;")
        
        header_layout.addWidget(titulo)
        header_layout.addWidget(subtitulo)
        
        layout.addWidget(header_widget)
    
    def _crear_tab_resumen_ejecutivo(self):
        """Crea pestaña de resumen ejecutivo con visualizaciones"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # === INFORMACIÓN CLAVE ===
        info_container = QWidget()
        info_layout = QHBoxLayout(info_container)
        
        # Columna 1: Datos básicos
        col1 = self._crear_panel_info("📋 INFORMACIÓN BÁSICA", [
            ("Tipo", self.movimiento['tipo'], self._get_color_por_tipo(self.movimiento['tipo'])),
            ("Fecha", self._formatear_fecha(self.movimiento['fecha']), "#6b7280"),
            ("N° Transferencia", self.movimiento.get('numero_transferencia', 'N/A'), "#6b7280"),
            ("ID Movimiento", f"#{self.movimiento['id']}", "#9ca3af")
        ])
        
        # Columna 2: Responsable
        responsable_info = []
        if self.movimiento.get('responsable_nombre') or self.movimiento.get('responsable_apellido'):
            responsable_info = [
                ("Nombre", f"{self.movimiento.get('responsable_nombre', '')} {self.movimiento.get('responsable_apellido', '')}".strip(), "#1e40af"),
                ("DNI/CUIT", self.movimiento.get('responsable_dni_cuit', 'N/A'), "#4b5563"),
                ("Área/Institución", self.movimiento.get('responsable_institucional', 'N/A'), "#374151")
            ]
        else:
            responsable_info = [
                ("Responsable", self.movimiento.get('responsable', 'N/A'), "#1e40af")
            ]
        
        col2 = self._crear_panel_info("👤 RESPONSABLE", responsable_info)
        
        info_layout.addWidget(col1)
        info_layout.addWidget(col2)
        info_layout.setStretchFactor(col1, 1)
        info_layout.setStretchFactor(col2, 1)
        
        layout.addWidget(info_container)
        
        # === ESTADÍSTICAS VISUALES ===
        stats_group = QGroupBox("📊 ESTADÍSTICAS DEL MOVIMIENTO")
        stats_group.setStyleSheet(self._get_estilo_grupo("stats"))
        stats_layout = QVBoxLayout(stats_group)
        
        # Barra de progreso para tipos de bienes
        tipos = {}
        for bien in self.bienes_movimiento:
            tipo = bien.get('tipo', 'No especificado')
            tipos[tipo] = tipos.get(tipo, 0) + 1
        
        for tipo, cantidad in tipos.items():
            tipo_layout = QHBoxLayout()
            label = QLabel(f"{tipo}:")
            label.setMinimumWidth(120)
            
            bar = QProgressBar()
            bar.setMaximum(len(self.bienes_movimiento))
            bar.setValue(cantidad)
            bar.setTextVisible(True)
            bar.setFormat(f"{cantidad} ({cantidad/len(self.bienes_movimiento)*100:.0f}%)")
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    text-align: center;
                    height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: {self._get_color_por_tipo(tipo)};
                    border-radius: 3px;
                }}
            """)
            
            tipo_layout.addWidget(label)
            tipo_layout.addWidget(bar)
            stats_layout.addLayout(tipo_layout)
        
        layout.addWidget(stats_group)
        
        # === OBSERVACIONES ===
        obs_group = QGroupBox("📝 OBSERVACIONES")
        obs_group.setStyleSheet(self._get_estilo_grupo("obs"))
        obs_layout = QVBoxLayout(obs_group)
        
        observaciones = self.movimiento.get('observaciones', 'No hay observaciones registradas.')
        obs_text = QTextEdit()
        obs_text.setPlainText(observaciones)
        obs_text.setMaximumHeight(100)
        obs_text.setReadOnly(True)
        obs_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e5e7eb;
                border-radius: 4px;
                padding: 8px;
                background: #f9fafb;
            }
        """)
        
        obs_layout.addWidget(obs_text)
        layout.addWidget(obs_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "📈 Resumen")
    
    def _crear_tab_bienes_detallados(self):
        """Crea pestaña con tabla detallada de bienes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Barra de herramientas para bienes
        tools_layout = QHBoxLayout()
        
        total_label = QLabel(f"📦 TOTAL DE BIENES: {len(self.bienes_movimiento)}")
        total_label.setStyleSheet("font-weight: bold; color: #1e40af;")
        
        prds_unicos = set(b.get('prd', '') for b in self.bienes_movimiento if b.get('prd'))
        prds_label = QLabel(f"🏷️ PRDs ÚNICOS: {len(prds_unicos)}")
        
        tools_layout.addWidget(total_label)
        tools_layout.addWidget(prds_label)
        tools_layout.addStretch()
        
        layout.addLayout(tools_layout)
        
        # Tabla de bienes
        self.tabla_bienes = QTableWidget()
        self.tabla_bienes.setAlternatingRowColors(True)
        self._configurar_tabla_bienes()
        
        layout.addWidget(self.tabla_bienes)
        self.tabs.addTab(tab, "📦 Bienes")
    
    def _configurar_tabla_bienes(self):
        """Configura tabla de bienes con columnas optimizadas"""
        columnas = [
            ("Ficha", 80), ("Tipo", 100), ("Marca", 100), ("Modelo", 120),
            ("Serie", 120), ("IMEI", 120), ("PRD", 80), ("Estado", 100),
            ("Asignado a", 150)
        ]
        
        self.tabla_bienes.setColumnCount(len(columnas))
        self.tabla_bienes.setHorizontalHeaderLabels([c[0] for c in columnas])
        self.tabla_bienes.setRowCount(len(self.bienes_movimiento))
        
        # Llenar tabla
        for row, bien in enumerate(self.bienes_movimiento):
            # Columna 0: Ficha
            item_ficha = QTableWidgetItem(bien.get('ficha', ''))
            item_ficha.setData(Qt.UserRole, bien.get('id'))
            self.tabla_bienes.setItem(row, 0, item_ficha)
            
            # Columna 1: Tipo
            tipo_item = QTableWidgetItem(bien.get('tipo', ''))
            tipo_item.setForeground(QColor(self._get_color_por_tipo(bien.get('tipo', ''))))
            self.tabla_bienes.setItem(row, 1, tipo_item)
            
            # Columna 2-5: Datos técnicos
            self.tabla_bienes.setItem(row, 2, QTableWidgetItem(bien.get('marca', '')))
            self.tabla_bienes.setItem(row, 3, QTableWidgetItem(bien.get('modelo', '')))
            self.tabla_bienes.setItem(row, 4, QTableWidgetItem(bien.get('serie', '')))
            self.tabla_bienes.setItem(row, 5, QTableWidgetItem(bien.get('imei', '')))
            
            # Columna 6: PRD
            prd_item = QTableWidgetItem(bien.get('prd', ''))
            if bien.get('prd'):
                prd_item.setForeground(QColor("#059669"))
                prd_item.setToolTip(f"PRD: {bien.get('prd')}")
            self.tabla_bienes.setItem(row, 6, prd_item)
            
            # Columna 7: Estado
            estado = bien.get('estado', '')
            estado_item = QTableWidgetItem(estado)
            estado_item.setForeground(QColor(self._get_color_estado(estado)))
            self.tabla_bienes.setItem(row, 7, estado_item)
            
            # Columna 8: Asignado a
            asignado = f"{bien.get('nombre', '')} {bien.get('apellido', '')}".strip()
            if not asignado:
                asignado = "Depósito"
            asignado_item = QTableWidgetItem(asignado)
            self.tabla_bienes.setItem(row, 8, asignado_item)
        
        # Configurar header
        header = self.tabla_bienes.horizontalHeader()
        for i, (_, width) in enumerate(columnas):
            header.setSectionResizeMode(i, QHeaderView.Interactive)
            self.tabla_bienes.setColumnWidth(i, width)
        
        # Conectar doble click
        self.tabla_bienes.doubleClicked.connect(self._ver_historial_bien)
        
        # Estilo de la tabla
        self.tabla_bienes.setStyleSheet("""
            QTableWidget {
                gridline-color: #e5e7eb;
                selection-background-color: #dbeafe;
                selection-color: #1e40af;
            }
            QHeaderView::section {
                background-color: #f3f4f6;
                padding: 8px;
                border: 1px solid #e5e7eb;
                font-weight: bold;
            }
        """)
    
    def _crear_tab_informacion_tecnica(self):
        """Crea pestaña con información técnica y logs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # === METADATOS DEL MOVIMIENTO ===
        meta_group = QGroupBox("⚙️ METADATOS TÉCNICOS")
        meta_group.setStyleSheet(self._get_estilo_grupo("tech"))
        meta_layout = QVBoxLayout(meta_group)
        
        # Información de archivos
        archivo_pdf = self.movimiento.get('archivo_path_pdf', '')
        if archivo_pdf and os.path.exists(archivo_pdf):
            try:
                file_size = os.path.getsize(archivo_pdf) / 1024  # KB
                file_time = datetime.datetime.fromtimestamp(os.path.getmtime(archivo_pdf))
                
                meta_info = [
                    ("📄 Archivo PDF", os.path.basename(archivo_pdf)),
                    ("📏 Tamaño", f"{file_size:.1f} KB"),
                    ("🕒 Última modificación", file_time.strftime("%d/%m/%Y %H:%M")),
                    ("📍 Ruta completa", archivo_pdf[:80] + "..." if len(archivo_pdf) > 80 else archivo_pdf)
                ]
                
                for label, value in meta_info:
                    row = QHBoxLayout()
                    lbl = QLabel(f"<b>{label}:</b>")
                    lbl.setMinimumWidth(150)
                    val = QLabel(value)
                    val.setStyleSheet("color: #4b5563;")
                    row.addWidget(lbl)
                    row.addWidget(val)
                    row.addStretch()
                    meta_layout.addLayout(row)
            except Exception as e:
                error_label = QLabel(f"⚠️ Error cargando metadatos: {str(e)}")
                error_label.setStyleSheet("color: #dc2626;")
                meta_layout.addWidget(error_label)
        else:
            no_pdf_label = QLabel("📭 No hay archivo PDF asociado a este movimiento")
            no_pdf_label.setStyleSheet("color: #6b7280; font-style: italic;")
            meta_layout.addWidget(no_pdf_label)
        
        layout.addWidget(meta_group)
        
        # === RESUMEN TÉCNICO ===
        tech_group = QGroupBox("🔍 RESUMEN TÉCNICO")
        tech_group.setStyleSheet(self._get_estilo_grupo("tech"))
        tech_layout = QVBoxLayout(tech_group)
        
        # Generar resumen técnico
        resumen_html = self._generar_resumen_tecnico()
        tech_text = QTextEdit()
        tech_text.setHtml(resumen_html)
        tech_text.setReadOnly(True)
        tech_text.setMaximumHeight(200)
        
        tech_layout.addWidget(tech_text)
        layout.addWidget(tech_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "⚙️ Técnico")
    
    def _crear_seccion_acta_firmada(self, layout):
        """Crea sección especial para ACTA FIRMADA (siempre visible)"""
        acta_widget = QWidget()
        acta_widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 2px solid #dbeafe;
                border-radius: 8px;
                padding: 15px;
                margin-top: 10px;
            }
        """)
        
        acta_layout = QVBoxLayout(acta_widget)
        
        # Título de la sección
        titulo_acta = QLabel("📄 ACTA FIRMADA")
        titulo_acta.setStyleSheet("""
            QLabel {
                color: #1e40af;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        archivo_pdf = self.movimiento.get('archivo_path_pdf', '')
        pdf_existe = archivo_pdf and os.path.exists(archivo_pdf)
        
        if pdf_existe:
            # === ACTA DISPONIBLE ===
            estado_layout = QHBoxLayout()
            
            # Indicador verde
            indicador = QLabel("●")
            indicador.setStyleSheet("color: #10b981; font-size: 20px;")
            
            estado_text = QLabel("ACTA FIRMADA DISPONIBLE")
            estado_text.setStyleSheet("color: #10b981; font-weight: bold; font-size: 14px;")
            
            estado_layout.addWidget(indicador)
            estado_layout.addWidget(estado_text)
            estado_layout.addStretch()
            
            acta_layout.addLayout(estado_layout)
            
            # Información del archivo
            try:
                file_info = self._obtener_info_archivo(archivo_pdf)
                for info in file_info:
                    info_label = QLabel(info)
                    info_label.setStyleSheet("color: #4b5563; margin-left: 20px;")
                    acta_layout.addWidget(info_label)
            except:
                pass
            
            # Botones de acción
            btn_layout = QHBoxLayout()
            
            btn_abrir = QPushButton("📄 ABRIR ACTA")
            btn_abrir.setStyleSheet("""
                QPushButton {
                    background-color: #10b981;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #059669;
                }
                QPushButton:pressed {
                    background-color: #047857;
                }
            """)
            btn_abrir.clicked.connect(self.abrir_pdf)
            
            btn_verificar = QPushButton("🔍 VER DETALLES")
            btn_verificar.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    font-weight: bold;
                    padding: 10px 20px;
                    border-radius: 6px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            btn_verificar.clicked.connect(lambda: self.tabs.setCurrentIndex(2))  # Ir a pestaña técnica
            
            btn_layout.addWidget(btn_abrir)
            btn_layout.addWidget(btn_verificar)
            btn_layout.addStretch()
            
            acta_layout.addLayout(btn_layout)
            
        else:
            # === SIN ACTA - OFRECER SUBIR ===
            estado_layout = QHBoxLayout()
            
            indicador = QLabel("●")
            indicador.setStyleSheet("color: #f59e0b; font-size: 20px;")
            
            estado_text = QLabel("ACTA FIRMADA PENDIENTE")
            estado_text.setStyleSheet("color: #f59e0b; font-weight: bold; font-size: 14px;")
            
            estado_layout.addWidget(indicador)
            estado_layout.addWidget(estado_text)
            estado_layout.addStretch()
            
            acta_layout.addLayout(estado_layout)
            
            # Mensaje informativo
            mensaje = QLabel(
                "Este movimiento no tiene acta firmada registrada.\n"
                "Para completar el proceso, suba el PDF escaneado y firmado."
            )
            mensaje.setStyleSheet("color: #6b7280; margin-left: 20px; margin-top: 5px;")
            mensaje.setWordWrap(True)
            
            acta_layout.addWidget(mensaje)
            
            # Botón para subir
            btn_subir = QPushButton("📤 SUBIR ACTA FIRMADA")
            btn_subir.setStyleSheet("""
                QPushButton {
                    background-color: #f59e0b;
                    color: white;
                    font-weight: bold;
                    padding: 12px 24px;
                    border-radius: 6px;
                    border: none;
                    margin-top: 10px;
                }
                QPushButton:hover {
                    background-color: #d97706;
                }
                QPushButton:pressed {
                    background-color: #b45309;
                }
            """)
            btn_subir.clicked.connect(self._subir_acta_desde_resumen)
            
            acta_layout.addWidget(btn_subir, alignment=Qt.AlignCenter)
        
        layout.addWidget(acta_widget)
    
    def _crear_botones_accion(self, layout):
        """Crea botones de acción en la parte inferior"""
        botones_layout = QHBoxLayout()
        
        # Botón para historial de bien seleccionado
        self.btn_historial = QPushButton("📊 VER HISTORIAL DE BIEN")
        self.btn_historial.clicked.connect(self._ver_historial_bien_seleccionado)
        self.btn_historial.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
        """)
        
        # Botón para cerrar
        btn_cerrar = QPushButton("✅ CERRAR RESUMEN")
        btn_cerrar.clicked.connect(self.accept)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                padding: 8px 24px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        
        botones_layout.addWidget(self.btn_historial)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_cerrar)
        
        layout.addLayout(botones_layout)
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _crear_panel_info(self, titulo, items):
        """Crea un panel de información estilizado"""
        panel = QGroupBox(titulo)
        panel.setStyleSheet(self._get_estilo_grupo("info"))
        layout = QVBoxLayout(panel)
        
        for label, valor, color in items:
            row = QHBoxLayout()
            
            lbl = QLabel(f"{label}:")
            lbl.setMinimumWidth(120)
            lbl.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            val = QLabel(str(valor))
            val.setStyleSheet("color: #374151;")
            val.setWordWrap(True)
            
            row.addWidget(lbl)
            row.addWidget(val)
            row.addStretch()
            layout.addLayout(row)
        
        return panel
    
    def _get_estilo_grupo(self, tipo="default"):
        """Retorna estilos CSS para grupos según tipo"""
        estilos = {
            "default": """
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #e5e7eb;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    background: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #1f2937;
                }
            """,
            "stats": """
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #dbeafe;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    background: white;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #1e40af;
                }
            """,
            "obs": """
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #fef3c7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    background: #fffbeb;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #92400e;
                }
            """,
            "tech": """
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #dcfce7;
                    border-radius: 8px;
                    margin-top: 10px;
                    padding-top: 15px;
                    background: #f0fdf4;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #065f46;
                }
            """,
            "info": """
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #f3f4f6;
                    border-radius: 6px;
                    margin: 5px;
                    padding-top: 12px;
                    background: #f9fafb;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 8px 0 8px;
                    color: #4b5563;
                    font-size: 12px;
                }
            """
        }
        return estilos.get(tipo, estilos["default"])
    
    def _formatear_fecha(self, fecha_str):
        """Formatea fecha para visualización"""
        try:
            if ' ' in fecha_str:
                fecha_dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                return fecha_dt.strftime("%d/%m/%Y %H:%M")
            else:
                fecha_dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
                return fecha_dt.strftime("%d/%m/%Y")
        except:
            return fecha_str
    
    def _get_color_por_tipo(self, tipo):
        """Retorna color según tipo de movimiento"""
        colores = {
            'entrega': '#059669',
            'devolución': '#2563eb',
            'baja': '#dc2626',
            'transferencia': '#7c3aed',
            'compra': '#d97706'
        }
        return colores.get(tipo.lower(), '#6b7280')
    
    def _get_color_estado(self, estado):
        """Retorna color según estado del bien"""
        colores = {
            'en depósito': '#059669',
            'asignado': '#2563eb',
            'baja definitiva': '#dc2626',
            'en reparación': '#d97706',
            'stock': '#059669',
            'disponible': '#059669'
        }
        return colores.get(estado.lower(), '#6b7280')
    
    def _obtener_info_archivo(self, ruta_archivo):
        """Obtiene información detallada del archivo PDF"""
        info = []
        try:
            nombre = os.path.basename(ruta_archivo)
            tamano_kb = os.path.getsize(ruta_archivo) / 1024
            fecha_mod = datetime.datetime.fromtimestamp(os.path.getmtime(ruta_archivo))
            
            info.append(f"📁 Archivo: {nombre}")
            info.append(f"📏 Tamaño: {tamano_kb:.1f} KB")
            info.append(f"🕒 Fecha: {fecha_mod.strftime('%d/%m/%Y %H:%M')}")
            
            # Intentar extraer más info si es posible
            if "ACTA_" in nombre:
                partes = nombre.replace('.pdf', '').split('_')
                if len(partes) >= 3:
                    info.append(f"🏷️ Tipo: {partes[1].capitalize()}")
            
        except Exception as e:
            info.append(f"⚠️ Información limitada disponible")
        
        return info
    
    def _generar_resumen_tecnico(self):
        """Genera resumen técnico en HTML"""
        html = """
        <style>
            .tech-table { border-collapse: collapse; width: 100%; }
            .tech-table th { background: #f3f4f6; padding: 8px; text-align: left; }
            .tech-table td { padding: 8px; border-bottom: 1px solid #e5e7eb; }
            .badge { padding: 2px 8px; border-radius: 12px; font-size: 12px; }
        </style>
        <table class='tech-table'>
            <tr><th>Campo</th><th>Valor</th><th>Estado</th></tr>
        """
        
        campos = [
            ("ID Movimiento", self.movimiento['id'], "primary"),
            ("Tipo", self.movimiento['tipo'], self.movimiento['tipo'].lower()),
            ("Total Bienes", len(self.bienes_movimiento), "info"),
            ("Acta Firmada", "Sí" if self.movimiento.get('archivo_path_pdf') else "No", 
             "success" if self.movimiento.get('archivo_path_pdf') else "warning")
        ]
        
        for campo, valor, tipo in campos:
            color = {
                'primary': '#3b82f6',
                'info': '#06b6d4',
                'success': '#10b981',
                'warning': '#f59e0b',
                'entrega': '#059669',
                'devolución': '#2563eb',
                'baja': '#dc2626'
            }.get(tipo, '#6b7280')
            
            html += f"""
            <tr>
                <td><b>{campo}</b></td>
                <td>{valor}</td>
                <td><span style='background:{color};color:white;' class='badge'>{tipo}</span></td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def _ver_historial_bien_seleccionado(self):
        """Muestra historial del bien seleccionado"""
        current_row = self.tabla_bienes.currentRow()
        if current_row >= 0:
            self._ver_historial_bien(self.tabla_bienes.model().index(current_row, 0))
        else:
            QMessageBox.information(self, "Selección requerida", 
                                "Por favor, seleccione un bien de la tabla.")
    
    def _ver_historial_bien(self, index):
        """Abre diálogo de historial para un bien"""
        try:
            row = index.row()
            if 0 <= row < len(self.bienes_movimiento):
                bien = self.bienes_movimiento[row]
                from ui.dialogs.historial_dialog import HistorialDialog
                dialog = HistorialDialog(self.parent.db, bien, self.parent)
                dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el historial:\n{str(e)}")
    
    def _subir_acta_desde_resumen(self):
        """Permite subir acta firmada desde el resumen"""
        try:
            if self.parent and hasattr(self.parent, '_subir_acta_firmada'):
                movimiento_id = self.movimiento.get('id')
                if movimiento_id:
                    # Cerrar y subir
                    self.accept()
                    QTimer.singleShot(300, lambda: self.parent._subir_acta_firmada(movimiento_id))
            else:
                QMessageBox.information(self, "Información", 
                                      "Use la lista principal de movimientos para subir actas.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se puede subir acta:\n{str(e)}")
    
    def abrir_pdf(self):
        """Abre el archivo PDF de la acta firmada"""
        archivo_pdf = self.movimiento.get('archivo_path_pdf', '')
        if archivo_pdf and os.path.exists(archivo_pdf):
            try:
                QDesktopServices.openUrl(f"file:///{archivo_pdf}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir el PDF:\n{str(e)}")
        else:
            QMessageBox.warning(self, "No disponible", "El archivo PDF no está disponible.")