"""
🎨 VENTANA PRINCIPAL - Sistema de Inventario AGC
Ventana principal modularizada
"""

import os
from datetime import datetime

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QTableWidget, QTableWidgetItem, QLabel, 
                           QLineEdit, QMessageBox, QTabWidget, QStatusBar,
                           QToolBar, QComboBox, QGroupBox, QFormLayout,
                           QScrollArea, QCheckBox, QDialog, QTextEdit,
                           QFileDialog, QProgressBar, QRadioButton,
                           QListWidget, QListWidgetItem, QDialogButtonBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import QUrl

# Importar nuestros módulos
from database.db_manager import DB
from ui.components.header_filtros import HeaderFiltros
from ui.components.panel_filtros import PanelFiltrosAvanzados
from ui.dialogs.bien_dialog import BienDialog
from ui.dialogs.movimiento_dialog import MovimientoDialog
from ui.dialogs.config_modo_dialog import ConfiguracionModoDialog


class VentanaPrincipal(QMainWindow):
    def __init__(self, db: DB, usuario_actual=None):
        super().__init__()
        self.db = db
        self.usuario_actual = usuario_actual
        
        # Configuración inicial
        self._inicializar_configuracion()
        self._setup_ui()
        
    def _inicializar_configuracion(self):
        """Configuración inicial de la ventana"""
        # Configuración de paginación
        self.pagina_actual = 1
        self.registros_por_pagina = 50
        self.total_registros = 0
        self.total_paginas = 1
        
        # Configuración de columnas para BIENES
        self.columnas_visibles_bienes = {
            "FICHA": True, "TIPO": True, "MARCA": True, "MODELO": True, 
            "SERIE": True, "IMEI": False, "LINEA": False, "SIM": False,
            "EMPRESA": False, "NOMBRE": True, "APELLIDO": True, 
            "DNI_CUIT": True, "INSTITUCIONAL": True, "DESCRIPCION": False,
            "ESTADO": True, "FECHA_REGISTRO": False, "MONTO_ORIGINAL": False,
            "PRD": True, "AÑO PRD": False
        }
        
        # Configuración de columnas para MOVIMIENTOS
        self.columnas_visibles_movimientos = {
            "Tipo": True,
            "Fecha Entrega": True, 
            "N° Transferencia": True,
            "Responsable": True,
            "Nombre": True,
            "Apellido": True,  
            "DNI/CUIT": True,
            "Institucional": True,
            "Cantidad Bienes": True,
            "PRD": True,
            "Fichas": False,
            "Observaciones": False,
            "PDF": True
        }
        
        # Mapeo de columnas
        self.mapeo_columnas = [
            ("FICHA", "ficha"),
            ("TIPO", "tipo"),
            ("MARCA", "marca"),
            ("MODELO", "modelo"), 
            ("SERIE", "serie"),
            ("IMEI", "imei"),
            ("LINEA", "linea"),
            ("SIM", "sim"),
            ("EMPRESA", "empresa"),
            ("NOMBRE", "nombre"),
            ("APELLIDO", "apellido"),
            ("DNI_CUIT", "dni_cuit"),
            ("INSTITUCIONAL", "institucional"),
            ("DESCRIPCION", "descripcion"),
            ("ESTADO", "estado"),
            ("FECHA_REGISTRO", "fecha_registro"),
            ("MONTO_ORIGINAL", "monto_original"),
            ("PRD", "prd"),
            ("AÑO PRD", "anio_prd")
        ]
        
        self.mapeo_columnas_movimientos = [
            ("Tipo", "tipo"),
            ("Fecha Entrega", "fecha"),
            ("N° Transferencia", "numero_transferencia"),
            ("Responsable", "responsable"),
            ("Nombre", "responsable_nombre"),
            ("Apellido", "responsable_apellido"),
            ("DNI/CUIT", "responsable_dni_cuit"),
            ("Institucional", "responsable_institucional"),
            ("Cantidad Bienes", "cantidad_bienes"),
            ("PRD", "prds"),
            ("Fichas", "fichas"),
            ("Observaciones", "observaciones"),
            ("PDF", "archivo_path")
        ]
        
        self.filtros_activos = {}
        self._configurar_permisos()
        
    def _configurar_permisos(self):
        """Configura permisos según el rol del usuario"""
        self.permisos = {
            "admin": {
                "puede_eliminar": True,
                "puede_exportar_todo": True, 
                "puede_configurar": True,
                "puede_ver_todo": True
            },
            "supervisor": {
                "puede_eliminar": False,
                "puede_exportar_todo": True,
                "puede_configurar": False, 
                "puede_ver_todo": True
            },
            "operador": {
                "puede_eliminar": False,
                "puede_exportar_todo": False,
                "puede_configurar": False,
                "puede_ver_todo": False
            }
        }
        
        self.permisos_actual = self.permisos.get(self.usuario_actual["rol"], {})

    def _setup_ui(self):
        """Configura la interfaz principal"""
        self.setWindowTitle(f"🏢 Sistema de Inventario AGC v1.0 | 👤 {self.usuario_actual['id']} ({self.usuario_actual['rol']})")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QTableWidget {
                gridline-color: #bdc3c7;
                background-color: white;
                alternate-background-color: #f8f9fa;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 5px;
                border: 1px solid #2c3e50;
                font-weight: bold;
            }
        """)
        
        # Crear barra de herramientas
        self._crear_barra_herramientas()
        
        # Widget central con tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self._crear_tab_buscar()
        self._crear_tab_movimientos()
        self._crear_tab_estadisticas()
        
        # Barra de estado
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.actualizar_status_bar()

    def _crear_barra_herramientas(self):
        """Crea la barra de herramientas con el selector de modo"""
        toolbar = QToolBar("Modo")
        toolbar.setIconSize(QtCore.QSize(16, 16))
        self.addToolBar(toolbar)
        
        # Botón de cambio de modo (por ahora placeholder)
        self.btn_cambio_modo = QPushButton("🌐 MODO")
        self.btn_cambio_modo.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
            }
        """)
        toolbar.addWidget(self.btn_cambio_modo)
        
        # Separador
        toolbar.addSeparator()
        
        # Botón de configuración avanzada
        btn_config_avanzada = QPushButton("⚙️ Configuración")
        btn_config_avanzada.clicked.connect(self.mostrar_configuracion_avanzada)
        toolbar.addWidget(btn_config_avanzada)
        
        # Espacio flexible
        toolbar.addWidget(QLabel(""))
        toolbar.addWidget(QLabel(""))

    def _crear_tab_buscar(self):
        """Crea la pestaña de búsqueda y consulta de bienes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 🔍 PANEL DE FILTROS AVANZADOS
        filtros_layout = QVBoxLayout()

        # Crear panel de filtros avanzados
        self.panel_filtros = PanelFiltrosAvanzados()
        self.panel_filtros.filtros_aplicados.connect(self.aplicar_filtros_avanzados)

        filtros_layout.addWidget(self.panel_filtros)

        # BARRA DE CONTROLES
        controles_layout = QHBoxLayout()

        # Botones de acción
        btn_cargar = QPushButton("🔄 Cargar Datos")
        btn_cargar.clicked.connect(self.cargar_bienes)
        btn_cargar.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)

        btn_nuevo_bien = QPushButton("➕ Nuevo Bien")
        btn_nuevo_bien.clicked.connect(self.abrir_formulario_bien)
        btn_nuevo_bien.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                font-weight: bold; 
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)

        btn_exportar = QPushButton("📊 Exportar Excel")
        btn_exportar.clicked.connect(self.exportar_filtrados)
        btn_exportar.setStyleSheet("""
            QPushButton { 
                background-color: #e67e22; 
                color: white; 
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)

        btn_columnas = QPushButton("⚙️ Columnas Bienes")
        btn_columnas.clicked.connect(self.mostrar_configuracion_columnas)
        btn_columnas.setStyleSheet("""
            QPushButton { 
                background-color: #9b59b6; 
                color: white; 
                padding: 6px 12px;
                border-radius: 4px;
            }
        """)

        # Agregar botones al layout
        controles_layout.addWidget(btn_cargar)
        controles_layout.addWidget(btn_nuevo_bien)
        controles_layout.addWidget(btn_exportar)
        controles_layout.addWidget(btn_columnas)
        controles_layout.addStretch()

        filtros_layout.addLayout(controles_layout)
        layout.addLayout(filtros_layout)
        
        # Etiqueta de columnas activas
        self.label_columnas_activas = QLabel("Columnas visibles: FICHA, TIPO, MARCA, MODELO, SERIE, NOMBRE, APELLIDO, DNI_CUIT, INSTITUCIONAL, ESTADO, PRD")
        self.label_columnas_activas.setStyleSheet("color: #2E86AB; font-size: 11px; padding: 2px;")
        layout.addWidget(self.label_columnas_activas)
        
        # Tabla de bienes
        self.tabla_bienes = QTableWidget()
        self.configurar_columnas_tabla()
        layout.addWidget(self.tabla_bienes)

        # PAGINACIÓN
        paginacion_layout = QHBoxLayout()

        self.btn_pagina_anterior = QPushButton("◀️ Anterior")
        self.btn_pagina_anterior.clicked.connect(self.pagina_anterior)
        self.btn_pagina_anterior.setEnabled(False)

        self.label_pagina = QLabel("Página 1 de 1")
        self.label_pagina.setStyleSheet("font-weight: bold; padding: 5px;")

        self.btn_pagina_siguiente = QPushButton("Siguiente ▶️")
        self.btn_pagina_siguiente.clicked.connect(self.pagina_siguiente)
        self.btn_pagina_siguiente.setEnabled(False)

        self.label_registros = QLabel("Mostrando 0 de 0 registros")
        self.label_registros.setStyleSheet("color: #666; padding: 5px;")

        self.combo_items_pagina = QComboBox()
        self.combo_items_pagina.addItems(["50", "100", "200", "500"])
        self.combo_items_pagina.setCurrentText("50")
        self.combo_items_pagina.currentTextChanged.connect(self.cambiar_items_por_pagina)

        # Agregar al layout
        paginacion_layout.addWidget(self.btn_pagina_anterior)
        paginacion_layout.addWidget(self.label_pagina)
        paginacion_layout.addWidget(self.btn_pagina_siguiente)
        paginacion_layout.addStretch()
        paginacion_layout.addWidget(self.label_registros)
        paginacion_layout.addStretch()
        paginacion_layout.addWidget(QLabel("Items por página:"))
        paginacion_layout.addWidget(self.combo_items_pagina)

        layout.addLayout(paginacion_layout)
        
        # Agregar al tabwidget
        self.tabs.addTab(tab, "🔍 Buscar Bienes")
    def _crear_tab_movimientos(self):
        """Crea la pestaña de movimientos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Barra de controles
        controles_layout = QHBoxLayout()
        
        self.btn_nuevo_movimiento = QPushButton("🔄 Nuevo Movimiento")
        self.btn_nuevo_movimiento.clicked.connect(self.abrir_formulario_movimiento)
        self.btn_nuevo_movimiento.setStyleSheet("QPushButton { background-color: #3498db; color: white; font-weight: bold; padding: 8px; }")
        
        self.btn_actualizar_mov = QPushButton("🔄 Actualizar")
        self.btn_actualizar_mov.clicked.connect(self.cargar_movimientos)
        
        self.btn_exportar_mov = QPushButton("📤 Exportar Movimientos")
        self.btn_exportar_mov.clicked.connect(self.exportar_movimientos)
        self.btn_exportar_mov.setStyleSheet("QPushButton { background-color: #e67e22; color: white; }")
        
        self.btn_columnas_mov = QPushButton("⚙️ Columnas Movimientos")
        self.btn_columnas_mov.clicked.connect(self.mostrar_configuracion_columnas_movimientos)
        self.btn_columnas_mov.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; }")
        
        controles_layout.addWidget(self.btn_nuevo_movimiento)
        controles_layout.addWidget(self.btn_actualizar_mov)
        controles_layout.addWidget(self.btn_exportar_mov)
        controles_layout.addWidget(self.btn_columnas_mov)
        controles_layout.addStretch()
        
        layout.addLayout(controles_layout)
        
        # Etiqueta de columnas activas
        self.label_columnas_mov_activas = QLabel("Columnas visibles: Tipo, Fecha Entrega, N° Transferencia, Responsable, Cantidad Bienes, PRD, PDF")
        self.label_columnas_mov_activas.setStyleSheet("color: #2E86AB; font-size: 11px; padding: 2px;")
        layout.addWidget(self.label_columnas_mov_activas)
        
        # Tabla de movimientos
        self.tabla_movimientos = QTableWidget()
        self.configurar_columnas_movimientos()
        layout.addWidget(self.tabla_movimientos)
        
        self.tabs.addTab(tab, "🔄 Movimientos")

    def _crear_tab_estadisticas(self):
        """Crea el panel de estadísticas ejecutivo"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Header
        header = QLabel("📊 DASHBOARD EJECUTIVO - INVENTARIO AGC")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                font-size: 18px; 
                font-weight: bold; 
                color: #2c3e50; 
                padding: 15px;
                background-color: #3498db;
                color: white;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Tarjetas KPI (placeholders por ahora)
        kpi_layout = QHBoxLayout()
        
        self.kpi_total = self._crear_tarjeta_kpi("📦 TOTAL BIENES", "0", "#3498db")
        self.kpi_deposito = self._crear_tarjeta_kpi("🟢 EN DEPÓSITO", "0", "#27ae60")
        self.kpi_asignados = self._crear_tarjeta_kpi("👤 ASIGNADOS", "0", "#e67e22")
        self.kpi_bajas = self._crear_tarjeta_kpi("📉 BAJAS", "0", "#e74c3c")
        
        kpi_layout.addWidget(self.kpi_total)
        kpi_layout.addWidget(self.kpi_deposito)
        kpi_layout.addWidget(self.kpi_asignados)
        kpi_layout.addWidget(self.kpi_bajas)
        
        layout.addLayout(kpi_layout)
        
        # Gráficos (placeholders)
        graficos_layout = QHBoxLayout()
        
        grafico1_container = QWidget()
        grafico1_layout = QVBoxLayout(grafico1_container)
        grafico1_titulo = QLabel("📊 DISTRIBUCIÓN POR ESTADO")
        grafico1_titulo.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px; padding: 5px;")
        self.grafico_estados = QLabel("Gráfico de Estados - Próximamente")
        self.grafico_estados.setStyleSheet("background-color: #f8f9fa; border: 1px solid #bdc3c7; padding: 20px;")
        self.grafico_estados.setAlignment(Qt.AlignCenter)
        self.grafico_estados.setMinimumHeight(200)
        grafico1_layout.addWidget(grafico1_titulo)
        grafico1_layout.addWidget(self.grafico_estados)
        
        grafico2_container = QWidget()
        grafico2_layout = QVBoxLayout(grafico2_container)
        grafico2_titulo = QLabel("📈 BIENES POR TIPO")
        grafico2_titulo.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px; padding: 5px;")
        self.grafico_tipos = QLabel("Gráfico de Tipos - Próximamente")
        self.grafico_tipos.setStyleSheet("background-color: #f8f9fa; border: 1px solid #bdc3c7; padding: 20px;")
        self.grafico_tipos.setAlignment(Qt.AlignCenter)
        self.grafico_tipos.setMinimumHeight(200)
        grafico2_layout.addWidget(grafico2_titulo)
        grafico2_layout.addWidget(self.grafico_tipos)
        
        graficos_layout.addWidget(grafico1_container)
        graficos_layout.addWidget(grafico2_container)
        layout.addLayout(graficos_layout)
        
        # Controles
        controles_layout = QHBoxLayout()
        
        self.btn_actualizar_stats = QPushButton("🔄 Actualizar")
        self.btn_actualizar_stats.clicked.connect(self.actualizar_estadisticas)
        self.btn_actualizar_stats.setStyleSheet("QPushButton { background-color: #3498db; color: white; padding: 5px 10px; }")
        
        self.btn_exportar_stats = QPushButton("📤 Exportar PDF")
        self.btn_exportar_stats.clicked.connect(self.exportar_estadisticas_pdf)
        self.btn_exportar_stats.setStyleSheet("QPushButton { background-color: #e67e22; color: white; padding: 5px 10px; }")
        
        controles_layout.addStretch()
        controles_layout.addWidget(self.btn_actualizar_stats)
        controles_layout.addWidget(self.btn_exportar_stats)
        layout.addLayout(controles_layout)
        
        self.tabs.addTab(tab, "📊 Dashboard")
        self.actualizar_estadisticas()

    def _crear_tarjeta_kpi(self, titulo, valor, color):
        """Crea una tarjeta KPI individual"""
        container = QWidget()
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout(container)
        
        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        label_titulo.setAlignment(Qt.AlignCenter)
        
        label_valor = QLabel(valor)
        label_valor.setStyleSheet("color: white; font-weight: bold; font-size: 24px;")
        label_valor.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        
        return container
    # ========== MÉTODOS PRINCIPALES ==========

    def configurar_columnas_tabla(self):
        """Configura las columnas de la tabla con headers personalizados"""
        try:
            # Configurar columnas visibles
            columnas_activas = [nombre for nombre, campo in self.mapeo_columnas 
                            if self.columnas_visibles_bienes.get(nombre, False)]
            
            self.tabla_bienes.setColumnCount(len(columnas_activas))
            self.tabla_bienes.setHorizontalHeaderLabels(columnas_activas)
            
            # Header personalizado
            if not isinstance(self.tabla_bienes.horizontalHeader(), HeaderFiltros):
                header = HeaderFiltros(Qt.Horizontal, self.tabla_bienes)
                self.tabla_bienes.setHorizontalHeader(header)
                header.setSectionsMovable(True)
                header.setStretchLastSection(True)
            
            # Actualizar etiqueta
            columnas_texto = ", ".join(columnas_activas)
            if len(columnas_texto) > 80:
                columnas_texto = columnas_texto[:80] + "..."
            
            if hasattr(self, 'label_columnas_activas'):
                self.label_columnas_activas.setText(f"Columnas visibles: {columnas_texto}")
                
        except Exception as e:
            print(f"❌ Error configurando columnas de tabla: {e}")

    def configurar_columnas_movimientos(self):
        """Configura las columnas de la tabla de movimientos"""
        try:
            columnas_activas = [nombre for nombre, campo in self.mapeo_columnas_movimientos 
                            if self.columnas_visibles_movimientos.get(nombre, False)]
            
            self.tabla_movimientos.setColumnCount(len(columnas_activas))
            self.tabla_movimientos.setHorizontalHeaderLabels(columnas_activas)
            
            # Header personalizado
            if not isinstance(self.tabla_movimientos.horizontalHeader(), HeaderFiltros):
                header_mov = HeaderFiltros(Qt.Horizontal, self.tabla_movimientos)
                self.tabla_movimientos.setHorizontalHeader(header_mov)
                header_mov.setSectionsMovable(True)
                header_mov.setStretchLastSection(True)
            
            # Actualizar etiqueta
            columnas_texto = ", ".join(columnas_activas)
            if len(columnas_texto) > 80:
                columnas_texto = columnas_texto[:80] + "..."
            
            if hasattr(self, 'label_columnas_mov_activas'):
                self.label_columnas_mov_activas.setText(f"Columnas visibles: {columnas_texto}")
                
        except Exception as e:
            print(f"❌ Error configurando columnas de movimientos: {e}")

    def cargar_bienes(self):
        """Carga bienes aplicando paginación"""
        try:
            # Obtener TODOS los bienes
            todos_los_bienes = self.db.list_bienes()
            self.total_registros = len(todos_los_bienes)
            
            # Calcular paginación
            self.total_paginas = max(1, (self.total_registros + self.registros_por_pagina - 1) // self.registros_por_pagina)
            
            # Obtener solo los registros de la página actual
            inicio = (self.pagina_actual - 1) * self.registros_por_pagina
            fin = inicio + self.registros_por_pagina
            bienes_paginados = todos_los_bienes[inicio:fin]
            
            # Mostrar en tabla
            self.mostrar_bienes_en_tabla(bienes_paginados)
            
            # Actualizar controles de paginación
            self.actualizar_controles_paginacion()
            
            print(f"✅ Cargados {len(bienes_paginados)} registros (página {self.pagina_actual})")
            
        except Exception as e:
            print(f"❌ Error cargando bienes: {e}")

    def mostrar_bienes_en_tabla(self, bienes):
        """Muestra bienes en tabla"""
        try:
            if not hasattr(self, 'tabla_bienes') or not self.tabla_bienes:
                return
                
            # Limpiar tabla
            self.tabla_bienes.setRowCount(0)
            
            if bienes:
                self.tabla_bienes.setRowCount(len(bienes))
                
                for i, bien in enumerate(bienes):
                    if i >= 500:  # Límite para rendimiento
                        break
                    col_idx = 0
                                       
                    for nombre_columna, campo_bd in self.mapeo_columnas:
                        if not self.columnas_visibles_bienes.get(nombre_columna, False):
                            continue
                            
                        valor = self.safe_get(bien, campo_bd)                        
                       
                        # Lógica especial para el estado
                        if nombre_columna == "ESTADO":
                            estado = valor.lower()
                            nombre = self.safe_get(bien, "nombre")
                            apellido = self.safe_get(bien, "apellido")
                            
                            if (estado == "en depósito" or estado == "stock") and not (nombre.strip() or apellido.strip()):
                                valor = "🟢 Disponible"
                        
                        self.tabla_bienes.setItem(i, col_idx, QTableWidgetItem(str(valor)))
                        col_idx += 1
            
            self.tabla_bienes.resizeColumnsToContents()
            print(f"✅ Tabla actualizada: {min(len(bienes), 500)} registros")

        except Exception as e:
            print(f"❌ Error en mostrar_bienes_en_tabla: {e}")

    def safe_get(self, bien, campo):
        """Obtiene valores de forma segura desde sqlite3.Row"""
        try:
            valor = bien[campo]
            return str(valor) if valor is not None else ""
        except (KeyError, IndexError):
            return ""

    def actualizar_controles_paginacion(self):
        """Actualiza los controles de paginación"""
        try:
            if not hasattr(self, 'btn_pagina_anterior'):
                return
                
            # Calcular rango de registros mostrados
            inicio = (self.pagina_actual - 1) * self.registros_por_pagina + 1
            fin = min(self.pagina_actual * self.registros_por_pagina, self.total_registros)
            
            # Actualizar controles
            self.btn_pagina_anterior.setEnabled(self.pagina_actual > 1)
            self.btn_pagina_siguiente.setEnabled(self.pagina_actual < self.total_paginas)
            
            self.label_pagina.setText(f"Página {self.pagina_actual} de {self.total_paginas}")
            self.label_registros.setText(f"Mostrando {inicio}-{fin} de {self.total_registros} registros")
            
        except Exception as e:
            print(f"❌ Error actualizando controles de paginación: {e}")

    def pagina_anterior(self):
        """Va a la página anterior"""
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.cargar_bienes()

    def pagina_siguiente(self):
        """Va a la página siguiente"""
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual += 1
            self.cargar_bienes()

    def cambiar_items_por_pagina(self):
        """Cambia la cantidad de items por página"""
        try:
            nuevo_limite = int(self.combo_items_pagina.currentText())
            if nuevo_limite != self.registros_por_pagina:
                self.registros_por_pagina = nuevo_limite
                self.pagina_actual = 1
                self.cargar_bienes()
        except Exception as e:
            print(f"❌ Error cambiando items por página: {e}")
    # ========== MÉTODOS DE DIÁLOGOS ==========

    def abrir_formulario_bien(self):
        """Abre el formulario de bienes"""
        try:
            from ui.dialogs.bien_dialog import BienDialog
            dialog = BienDialog(self.db, self)
            if dialog.exec_() == QDialog.Accepted:
                self.cargar_bienes()
                self.actualizar_status_bar()
        except Exception as e:
            print(f"❌ Error abriendo formulario bien: {e}")

    def abrir_formulario_movimiento(self):
        """Abre el formulario de movimientos"""
        try:
            from ui.dialogs.movimiento_dialog import MovimientoDialog
            dialog = MovimientoDialog(self.db, self)
            if dialog.exec_() == QDialog.Accepted:
                self.cargar_movimientos()
                self.cargar_bienes()
                self.actualizar_status_bar()
        except Exception as e:
            print(f"❌ Error abriendo formulario movimiento: {e}")

    def mostrar_configuracion_avanzada(self):
        """Muestra el diálogo de configuración avanzada"""
        try:
            from ui.dialogs.config_modo_dialog import ConfiguracionModoDialog
            dialog = ConfiguracionModoDialog(self)
            dialog.exec_()
        except Exception as e:
            print(f"❌ Error mostrando configuración: {e}")

    # ========== MÉTODOS DE MOVIMIENTOS ==========

    def cargar_movimientos(self):
        """Carga los movimientos en la tabla"""
        try:
            movimientos = self.db.get_movimientos_detallados()
        except:
            movimientos = self.db.list_movimientos()
            
        self.tabla_movimientos.setRowCount(len(movimientos))
        
        for i, mov in enumerate(movimientos):
            col_idx = 0
            for nombre_columna, campo_bd in self.mapeo_columnas_movimientos:
                if not self.columnas_visibles_movimientos.get(nombre_columna, False):
                    continue
                    
                if nombre_columna == "Responsable":
                    responsable_completo = self.safe_get(mov, "responsable")
                    if " - " in responsable_completo:
                        responsable_completo = responsable_completo.split(" - ")[0]
                    if " (CUIT:" in responsable_completo:
                        responsable_completo = responsable_completo.split(" (CUIT:")[0]
                    valor = responsable_completo
                    
                elif nombre_columna == "Fecha Entrega":
                    fecha_original = self.safe_get(mov, "fecha")
                    try:
                        fecha_dt = datetime.strptime(fecha_original, "%Y-%m-%d")
                        valor = fecha_dt.strftime("%d/%m/%Y")
                    except:
                        valor = fecha_original
                        
                elif nombre_columna == "PDF":
                    archivo = self.safe_get(mov, "archivo_path")
                    if archivo and os.path.exists(archivo):
                        valor = "📎 PDF"
                    else:
                        valor = ""
                        
                else:
                    valor = self.safe_get(mov, campo_bd)
                
                self.tabla_movimientos.setItem(i, col_idx, QTableWidgetItem(valor))
                col_idx += 1
        
        self.tabla_movimientos.resizeColumnsToContents()

    # ========== MÉTODOS DE ESTADÍSTICAS ==========

    def actualizar_estadisticas(self):
        """Actualiza todas las estadísticas del dashboard"""
        try:
            stats = self.db.get_estadisticas()
            self._actualizar_tarjetas_kpi(stats)
            self._actualizar_graficos(stats)
        except Exception as e:
            print(f"❌ Error actualizando dashboard: {e}")

    def _actualizar_tarjetas_kpi(self, stats):
        """Actualiza los valores de las tarjetas KPI"""
        try:
            total = stats.get('total', 0)
            por_estado = stats.get('por_estado', {})
            
            # Actualizar cada tarjeta
            self._actualizar_tarjeta_kpi(self.kpi_total, str(total))
            self._actualizar_tarjeta_kpi(self.kpi_deposito, str(por_estado.get('En depósito', 0)))
            self._actualizar_tarjeta_kpi(self.kpi_asignados, str(por_estado.get('Asignado', 0)))
            self._actualizar_tarjeta_kpi(self.kpi_bajas, str(por_estado.get('Baja definitiva', 0)))
        except Exception as e:
            print(f"❌ Error actualizando tarjetas KPI: {e}")

    def _actualizar_tarjeta_kpi(self, tarjeta_widget, nuevo_valor):
        """Actualiza el valor de una tarjeta KPI específica"""
        try:
            layout = tarjeta_widget.layout()
            if layout and layout.itemAt(1):
                label_valor = layout.itemAt(1).widget()
                if isinstance(label_valor, QLabel):
                    label_valor.setText(nuevo_valor)
        except Exception as e:
            print(f"❌ Error actualizando tarjeta: {e}")

    def _actualizar_graficos(self, stats):
        """Actualiza los gráficos (placeholders)"""
        try:
            por_estado = stats.get('por_estado', {})
            
            texto_estados = f"🟢 En depósito: {por_estado.get('En depósito', 0)}\n"
            texto_estados += f"🔵 Asignados: {por_estado.get('Asignado', 0)}\n" 
            texto_estados += f"🔴 Bajas: {por_estado.get('Baja definitiva', 0)}"
            
            self.grafico_estados.setText(texto_estados)
            self.grafico_tipos.setText("Gráfico de Tipos - Próximamente")
        except Exception as e:
            print(f"❌ Error actualizando gráficos: {e}")

    # ========== MÉTODOS AUXILIARES ==========

    def actualizar_status_bar(self):
        """Actualiza la barra de estado"""
        try:
            stats = self.db.get_estadisticas()
            modo = "LOCAL"  # Placeholder por ahora
            rol = self.usuario_actual["rol"].upper()
            
            self.status_bar.showMessage(
                f"👤 {self.usuario_actual['id']} ({rol}) | "
                f"Modo: {modo} | "
                f"Total bienes: {stats['total']} | "
                f"En depósito: {stats['por_estado'].get('En depósito', 0)} | "
                f"Asignados: {stats['por_estado'].get('Asignado', 0)}"
            )
        except Exception as e:
            self.status_bar.showMessage(f"👤 {self.usuario_actual['id']}")

    def exportar_movimientos(self):
        """Placeholder para exportar movimientos"""
        QMessageBox.information(self, "Exportar", "Función de exportación de movimientos - Próximamente")

    def exportar_filtrados(self):
        """Placeholder para exportar bienes filtrados"""
        QMessageBox.information(self, "Exportar", "Función de exportación de bienes - Próximamente")

    def exportar_estadisticas_pdf(self):
        """Placeholder para exportar PDF"""
        QMessageBox.information(self, "Exportar PDF", "Función de exportación PDF - Próximamente")

    def aplicar_filtros_avanzados(self, filtros):
        """Placeholder para filtros avanzados"""
        print(f"🔍 Filtros aplicados: {filtros}")
        QMessageBox.information(self, "Filtros", "Sistema de filtros avanzados - Próximamente")

    def mostrar_configuracion_columnas(self):
        """Placeholder para configuración de columnas"""
        QMessageBox.information(self, "Columnas", "Configuración de columnas - Próximamente")

    def mostrar_configuracion_columnas_movimientos(self):
        """Placeholder para configuración de columnas de movimientos"""
        QMessageBox.information(self, "Columnas Movimientos", "Configuración de columnas - Próximamente")