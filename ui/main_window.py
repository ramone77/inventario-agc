"""
🎨 VENTANA PRINCIPAL - Sistema de Inventario AGC
Ventana principal modularizada - VERSIÓN COMPLETAMENTE FUNCIONAL
"""

import os
import sys
import pandas as pd
from datetime import datetime

# ✅ AGREGAR ESTO PARA IMPORTS ABSOLUTOS
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5 import QtWidgets, QtCore, QtPrintSupport
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QPushButton, QTableWidget, QTableWidgetItem, QLabel, 
                           QLineEdit, QMessageBox, QTabWidget, QStatusBar,
                           QToolBar, QComboBox, QGroupBox, QFormLayout,
                           QScrollArea, QCheckBox, QDialog, QTextEdit,
                           QFileDialog, QProgressBar, QRadioButton,
                           QListWidget, QListWidgetItem, QDialogButtonBox)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QTextDocument, QTextCursor, QTextCharFormat, QFont
# ✅ NUEVAS IMPORTACIONES PARA SINCRONIZACIÓN
from core.sync_manager import SyncManager
from config.config_manager import obtener_estado_sincronizacion, actualizar_ultima_sincronizacion
from core.bien_manager import BienManager  # ← ✅ CORRECTO

# ✅ IMPORTS ABSOLUTOS (ahora funcionarán)
from database.db_manager import DB
from core.bien_manager import BienManager
from utils import excel_handler

# ✅ IMPORTS RELATIVOS (para módulos dentro de ui/)
from .components.header_filtros import HeaderFiltros
from .components.panel_filtros import PanelFiltrosAvanzados
from .dialogs.bien_dialog import BienDialog
from .dialogs.movimiento_dialog import MovimientoDialog
from .dialogs.config_modo_dialog import ConfiguracionModoDialog


class VentanaPrincipal(QMainWindow):
    def __init__(self, db: DB, usuario_actual=None):
        super().__init__()
        self.db = db
        self.usuario_actual = usuario_actual
        
        # ✅ INICIALIZAR MANAGERS PRIMERO
        self.bien_manager = BienManager(db)  # ← PRIMERO esto
        self.sync_manager = SyncManager(db)   # ← LUEGO esto
        
        self.status_bar = None
        self._status_widgets = []
        
        # ✅ LUEGO configurar UI
        self._inicializar_configuracion()
        self._setup_ui()
        
        # ✅ FINALMENTE conectar señales
        self.sync_manager.sincronizacion_iniciada.connect(self._on_sincronizacion_iniciada)
        
        # ✅ CUARTO: Conectar señales (ahora todo existe)
        self.sync_manager.sincronizacion_iniciada.connect(self._on_sincronizacion_iniciada)
        self.sync_manager.sincronizacion_completada.connect(self._on_sincronizacion_completada)
        self.sync_manager.progreso_sincronizacion.connect(self._on_progreso_sincronizacion)
        self.sync_manager.conflicto_detectado.connect(self._on_conflicto_detectado)
        
        # ✅ QUINTO: Actualizar UI final
        self.actualizar_status_bar()
        self._actualizar_estado_sincronizacion_ui()
        
        # Cargar datos iniciales
        self.cargar_bienes()
        self.cargar_movimientos()
        #✅ VERIFICACIÓN FINAL
        print("✅ Sistema completamente inicializado:")
        print(f"   - sync_manager: {'✅' if self.sync_manager else '❌'}")
        print(f"   - bien_manager: {'✅' if self.bien_manager else '❌'}")
        
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
        
        # Cargar datos iniciales
        self.cargar_bienes()
        self.cargar_movimientos()
    # ✅ NUEVO: Actualizar UI de sincronización después de todo está listo
        QtCore.QTimer.singleShot(100, self._actualizar_estado_sincronizacion_ui)

    def _crear_barra_herramientas(self):
        """Crea la barra de herramientas con controles de sincronización - VERSIÓN COMPLETA"""
        toolbar = QToolBar("Modo")
        toolbar.setIconSize(QtCore.QSize(16, 16))
        self.addToolBar(toolbar)
        
        # ✅ NUEVO: Botón de estado de sincronización
        self.btn_estado_sync = QPushButton("🔄 Conectando...")
        self.btn_estado_sync.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 3px;
                border: 1px solid #7f8c8d;
            }
            QPushButton:hover {
                background-color: #859596;
            }
        """)
        self.btn_estado_sync.clicked.connect(self.mostrar_dialogo_sincronizacion)
        self.btn_estado_sync.setToolTip("Haz clic para ver detalles de sincronización")
        toolbar.addWidget(self.btn_estado_sync)
        
        # ✅ NUEVO: Botón de sincronización manual
        self.btn_sync_manual = QPushButton("🔄 Sincronizar")
        self.btn_sync_manual.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
                border: 1px solid #95a5a6;
            }
        """)
        self.btn_sync_manual.clicked.connect(self.sincronizar_manual)
        self.btn_sync_manual.setToolTip("Sincronizar cambios manualmente con la red")
        toolbar.addWidget(self.btn_sync_manual)
        
        # Separador
        toolbar.addSeparator()
        
        # Botón de configuración avanzada (existente)
        btn_config_avanzada = QPushButton("⚙️ Configuración")
        btn_config_avanzada.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        btn_config_avanzada.clicked.connect(self.mostrar_configuracion_avanzada)
        btn_config_avanzada.setToolTip("Configurar modo de trabajo y sincronización")
        toolbar.addWidget(btn_config_avanzada)

        # ✅ NUEVO: BOTÓN GESTIÓN USUARIOS (SOLO PARA ADMINS)
        self.btn_gestion_usuarios = QPushButton("👥 Gestión Usuarios")
        self.btn_gestion_usuarios.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.btn_gestion_usuarios.clicked.connect(self.mostrar_gestion_usuarios)
        self.btn_gestion_usuarios.setToolTip("Gestionar usuarios del sistema (solo administradores)")
        
        # ✅ MOSTRAR SOLO SI ES ADMIN
        self.btn_gestion_usuarios.setVisible(self.usuario_actual['rol'] == 'admin')
        
        toolbar.addWidget(self.btn_gestion_usuarios)
        
        # Espacio flexible
        toolbar.addWidget(QLabel(""))
        toolbar.addWidget(QLabel(""))
        
        # ✅ NUEVO: Etiqueta informativa del modo actual
        self.label_info_modo = QLabel("Modo: Cargando...")
        self.label_info_modo.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 3px;
                border: 1px solid #bdc3c7;
            }
        """)
        toolbar.addWidget(self.label_info_modo)
        
        # ✅ NUEVO: Actualizar estado inicial
        self._actualizar_estado_sincronizacion_ui()
        
    def mostrar_gestion_usuarios(self):
        """Muestra el diálogo de gestión de usuarios"""
        try:
            from .dialogs.gestion_usuarios_dialog import GestionUsuariosDialog
            dialog = GestionUsuariosDialog(self.db, self.usuario_actual, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir gestión de usuarios:\n{str(e)}")        

    # ========== 🆕 MÉTODOS DE SINCRONIZACIÓN ==========

    def _actualizar_estado_sincronizacion_ui(self):
        """Actualiza la UI con el estado actual de sincronización - VERSIÓN ROBUSTA"""
        try:
            # ✅ VERIFICACIÓN EXTRA ROBUSTA - COMPROBAR TODOS LOS COMPONENTES
            componentes_requeridos = [
                'btn_estado_sync', 'label_info_modo', 'sync_manager', 
                'status_bar', 'btn_sync_manual'
            ]
            
            for componente in componentes_requeridos:
                if not hasattr(self, componente) or getattr(self, componente) is None:
                    print(f"⚠️ Componente '{componente}' no está listo aún")
                    return
            
            # ✅ VERIFICAR QUE EL SYNC MANAGER ESTÉ INICIALIZADO CORRECTAMENTE
            estado = self.sync_manager.obtener_estado()
            if not estado:
                print("⚠️ No se pudo obtener estado del SyncManager")
                return
                
            modo = estado.get("modo_trabajo", "desconocido")
            conectado = estado.get("conectado_red", False)
            ultima_sync = estado.get("ultima_sincronizacion")
            
            # ✅ ACTUALIZAR ETIQUETA INFORMATIVA CON MEJOR DISEÑO
            modo_texto = ""
            color_modo = ""
            icono_modo = ""
            
            if modo == "local_con_sincronizacion":
                modo_texto = "MODO SINCRONIZACIÓN"
                color_modo = "#27ae60"  # Verde
                icono_modo = "🔄"
            elif modo == "red_directo":
                modo_texto = "MODO RED DIRECTO"  
                color_modo = "#e67e22"  # Naranja
                icono_modo = "🌐"
            else:  # local_solo
                modo_texto = "MODO LOCAL SOLO"
                color_modo = "#e74c3c"  # Rojo
                icono_modo = "🏠"
                
            self.label_info_modo.setText(f"{icono_modo} {modo_texto}")
            self.label_info_modo.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    font-weight: bold;
                    padding: 6px 12px;
                    background-color: {color_modo};
                    border-radius: 15px;
                    border: 2px solid {color_modo};
                    font-size: 11px;
                }}
            """)
            
            # ✅ ACTUALIZAR BOTÓN DE ESTADO CON MEJOR DISEÑO
            if conectado:
                if ultima_sync:
                    try:
                        from datetime import datetime
                        fecha_dt = datetime.fromisoformat(ultima_sync.replace('Z', '+00:00'))
                        fecha_str = fecha_dt.strftime("%H:%M")
                        texto = f"✅ Sync: {fecha_str}"
                        color = "#27ae60"  # Verde
                        tooltip = f"Última sincronización: {fecha_dt.strftime('%d/%m/%Y %H:%M')}"
                    except Exception as date_error:
                        print(f"⚠️ Error formateando fecha: {date_error}")
                        texto = "✅ Conectado"
                        color = "#27ae60"
                        tooltip = "Conectado a la red"
                else:
                    texto = "🔄 Primer Sync"
                    color = "#f39c12"  # Naranja
                    tooltip = "Primera sincronización pendiente"
            else:
                texto = "❌ Sin Red"
                color = "#e74c3c"  # Rojo
                tooltip = "Sin conexión a la red - Modo local activo"
            
            self.btn_estado_sync.setText(texto)
            self.btn_estado_sync.setToolTip(tooltip)
            self.btn_estado_sync.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-weight: bold;
                    padding: 6px 12px;
                    border-radius: 15px;
                    border: 2px solid {color};
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    opacity: 0.9;
                }}
                QPushButton:pressed {{
                    background-color: {color};
                    opacity: 0.8;
                }}
            """)
            
            # ✅ HABILITAR/DESHABILITAR BOTÓN MANUAL
            self.btn_sync_manual.setEnabled(conectado)
            self.btn_sync_manual.setToolTip("Sincronizar manualmente con la red" if conectado else "No hay conexión a la red")
            
            # ✅ ACTUALIZAR BARRA DE ESTADO COMPLETA
            if hasattr(self, 'actualizar_status_bar'):
                self.actualizar_status_bar()
            
            print(f"✅ UI de sincronización actualizada: {modo_texto} - {texto}")
            
        except Exception as e:
            print(f"⚠️ Error recuperable en UI sync: {e}")
            # No hacemos nada, es un error temporal que se resolverá en el próximo intento

    def sincronizar_manual(self):
        """Inicia sincronización manual"""
        try:
            self.btn_sync_manual.setEnabled(False)
            self.btn_sync_manual.setText("🔄 Sincronizando...")
            self.sync_manager.sincronizar_manual()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error iniciando sincronización: {str(e)}")
            self.btn_sync_manual.setEnabled(True)
            self.btn_sync_manual.setText("🔄 Sincronizar")

    def _on_sincronizacion_iniciada(self, mensaje):
        """Maneja el inicio de sincronización"""
        print(f"🔄 {mensaje}")
        self.status_bar.showMessage(mensaje)

    def _on_sincronizacion_completada(self, mensaje, exito):
        """Maneja la finalización de sincronización - VERSIÓN CORREGIDA"""
        print(f"✅ Sincronización completada: {mensaje}")
        
        # ✅ CORREGIDO: Verificar que status_bar existe antes de usarlo
        if hasattr(self, 'status_bar') and self.status_bar is not None:
            if exito:
                self.status_bar.showMessage(f"✅ {mensaje}", 5000)
            else:
                self.status_bar.showMessage(f"❌ {mensaje}", 5000)
        else:
            # Si no existe status_bar, solo mostrar en consola
            print(f"📢 {mensaje}")
        
        # Restaurar botón
        self.btn_sync_manual.setEnabled(True)
        self.btn_sync_manual.setText("🔄 Sincronizar")
        
        # Actualizar UI
        self._actualizar_estado_sincronizacion_ui()
        
        # Recargar datos si hubo cambios y éxito
        if exito:
            self.cargar_bienes()
            self.cargar_movimientos()
            
        # Mostrar mensaje si fue error
        if not exito and "Error" in mensaje:
            QMessageBox.warning(self, "Sincronización", mensaje)

    def _on_progreso_sincronizacion(self, porcentaje, estado):
        """Maneja actualizaciones de progreso - VERSIÓN CORREGIDA"""
        # ✅ CORREGIDO: Verificar que status_bar existe
        if hasattr(self, 'status_bar') and self.status_bar is not None:
            self.status_bar.showMessage(f"🔄 {estado} ({porcentaje}%)")
        else:
            print(f"🔄 {estado} ({porcentaje}%)")

    def _on_conflicto_detectado(self, conflicto):
        """Maneja conflictos detectados"""
        print(f"⚠️ Conflicto detectado: {conflicto}")
        # Por ahora solo mostrar advertencia
        QMessageBox.warning(self, "Conflicto", 
                        f"Se detectó un conflicto en la sincronización.\n\n"
                        f"ID: {conflicto.get('id', 'N/A')}\n"
                        f"Tipo: {conflicto.get('tipo', 'N/A')}")

    def mostrar_dialogo_sincronizacion(self):
        """Muestra diálogo con información detallada de sincronización"""
        try:
            estado = self.sync_manager.obtener_estado()
            
            mensaje = f"""
    🔄 ESTADO DE SINCRONIZACIÓN

    📊 Modo de trabajo: {estado['modo_trabajo'].replace('_', ' ').title()}
    🌐 Conexión red: {'✅ Conectado' if estado['conectado_red'] else '❌ Sin conexión'}
    🕒 Última sincronización: {estado['ultima_sincronizacion'] or 'Nunca'}
    🔄 Sincronización automática: {'✅ Activada' if estado['auto_sincronizar'] else '❌ Desactivada'}
    ⏰ Timer activo: {'✅ Sí' if estado['timer_activo'] else '❌ No'}

    💡 Información:
    • La sincronización automática mantiene tu copia local actualizada
    • Los cambios se suben automáticamente a la red
    • Puedes sincronizar manualmente en cualquier momento
            """
            
            QMessageBox.information(self, "Estado de Sincronización", mensaje.strip())
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error obteniendo estado: {str(e)}")

    def _crear_tab_buscar(self):
        """Crea la pestaña de búsqueda y consulta de bienes"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 🔍 PANEL DE FILTROS AVANZADOS
        filtros_layout = QVBoxLayout()

        # Crear panel de filtros avanzados - ✅ ASEGURAR QUE SE PASE self.db
        self.panel_filtros = PanelFiltrosAvanzados(db=self.db)  # ← CON BD
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

        # BOTÓN EXCEL (verde)
        btn_exportar_excel = QPushButton("📊 Exportar Excel")
        btn_exportar_excel.clicked.connect(self.exportar_filtrados)
        btn_exportar_excel.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)

        # BOTÓN PDF (rojo)
        btn_exportar_pdf = QPushButton("📄 Exportar PDF")
        btn_exportar_pdf.clicked.connect(self.exportar_filtrados_pdf)
        btn_exportar_pdf.setStyleSheet("""
            QPushButton { 
                background-color: #e74c3c; 
                color: white; 
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        btn_columnas = QPushButton("⚙️ Columnas Bienes")
        # ✅ NUEVO BOTÓN: GENERAR ACTA
        btn_generar_acta = QPushButton("📋 Generar Acta")
        btn_generar_acta.clicked.connect(self.generar_acta_seleccionado)
        btn_generar_acta.setStyleSheet("""
            QPushButton { 
                background-color: #9b59b6; 
                color: white; 
                padding: 6px 12px;
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
        btn_generar_acta.setToolTip("Generar acta para el bien seleccionado")
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
        controles_layout.addWidget(btn_exportar_excel)
        controles_layout.addWidget(btn_exportar_pdf)
        controles_layout.addWidget(btn_columnas)
        controles_layout.addWidget(btn_generar_acta)
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
        # ✅ AGREGAR ESTA LÍNEA JUSTO DESPUÉS DE CREAR LA TABLA:
        self.tabla_bienes.doubleClicked.connect(self.mostrar_historial_bien)

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
        
        # BOTÓN EXCEL MOVIMIENTOS (verde)
        self.btn_exportar_mov_excel = QPushButton("📤 Exportar Excel")
        self.btn_exportar_mov_excel.clicked.connect(self.exportar_movimientos)
        self.btn_exportar_mov_excel.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white; 
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)

        # BOTÓN PDF MOVIMIENTOS (rojo)
        self.btn_exportar_mov_pdf = QPushButton("📄 Exportar PDF")  
        self.btn_exportar_mov_pdf.clicked.connect(self.exportar_movimientos_pdf)
        self.btn_exportar_mov_pdf.setStyleSheet("""
            QPushButton { 
                background-color: #e74c3c; 
                color: white; 
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self.btn_columnas_mov = QPushButton("⚙️ Columnas Movimientos")
        self.btn_columnas_mov.clicked.connect(self.mostrar_configuracion_columnas_movimientos)
        self.btn_columnas_mov.setStyleSheet("QPushButton { background-color: #9b59b6; color: white; }")
        
        controles_layout.addWidget(self.btn_nuevo_movimiento)
        controles_layout.addWidget(self.btn_actualizar_mov)
        controles_layout.addWidget(self.btn_exportar_mov_excel)
        controles_layout.addWidget(self.btn_exportar_mov_pdf)
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
                            elif estado == "asignado":
                                valor = "🔵 Asignado"
                            elif estado == "en reparación":
                                valor = "🟡 En reparación" 
                            elif estado == "baja definitiva":
                                valor = "🔴 Baja"
                        
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

    # ========== MÉTODOS DE FILTROS AVANZADOS ==========

    def aplicar_filtros_avanzados(self, filtros):
        """Aplica filtros avanzados REALES usando BienManager - VERSIÓN CORREGIDA"""
        try:
            print(f"🎯 Filtros recibidos en main_window: {filtros}")
            
            # ✅ VERIFICACIÓN CRÍTICA: ¿bien_manager existe?
            if not hasattr(self, 'bien_manager') or self.bien_manager is None:
                print("❌ ERROR CRÍTICO: bien_manager no está inicializado")
                print("🔄 Intentando inicializar bien_manager...")
                
                # ✅ CORREGIDO: Importar desde core/
                try:
                    from core.bien_manager import BienManager  # ← ¡CORREGIDO!
                    self.bien_manager = BienManager(self.db)
                    print("✅ bien_manager inicializado exitosamente desde core/")
                except Exception as init_error:
                    print(f"❌ No se pudo inicializar bien_manager: {init_error}")
                    self.status_bar.showMessage("❌ Error: Sistema no inicializado correctamente")
                    return
            
            # Guardar filtros activos
            self.filtros_activos = filtros
            
            if not filtros:
                # Si no hay filtros, cargar todos los bienes normalmente
                self.cargar_bienes()
                self.status_bar.showMessage("✅ Todos los filtros limpiados")
                return
            
            # ✅ USAR BienManager para aplicar filtros (AHORA SEGURO)
            bienes_filtrados = self.bien_manager.buscar_bienes(filtros)
            
            # Actualizar la tabla con los resultados filtrados
            self.total_registros = len(bienes_filtrados)
            self.pagina_actual = 1
            self.total_paginas = max(1, (self.total_registros + self.registros_por_pagina - 1) // self.registros_por_pagina)
            
            # Obtener registros de la página actual
            inicio = (self.pagina_actual - 1) * self.registros_por_pagina
            fin = inicio + self.registros_por_pagina
            bienes_paginados = bienes_filtrados[inicio:fin]
            
            # Mostrar en tabla
            self.mostrar_bienes_en_tabla(bienes_paginados)
            
            # Actualizar controles de paginación
            self.actualizar_controles_paginacion()
            
            # Actualizar status
            criterios = len(filtros)
            self.status_bar.showMessage(f"✅ Filtros aplicados: {criterios} criterios, {self.total_registros} resultados")
            
            print(f"✅ Filtros procesados: {criterios} criterios, {len(bienes_filtrados)} registros")
            
        except Exception as e:
            print(f"❌ Error aplicando filtros: {e}")
            self.status_bar.showMessage("❌ Error aplicando filtros")
            # Fallback: cargar bienes normales
            self.cargar_bienes()

    # ========== MÉTODOS DE DIÁLOGOS ==========

    def abrir_formulario_bien(self):
        """Abre el formulario de bienes"""
        try:
            dialog = BienDialog(self.db, self)
            if dialog.exec_() == QDialog.Accepted:
                self.cargar_bienes()
                self.actualizar_status_bar()
                self.panel_filtros.actualizar_tipos_dinamicos()
        except Exception as e:
            print(f"❌ Error abriendo formulario bien: {e}")

    def abrir_formulario_movimiento(self):
        """Abre el formulario de movimientos"""
        try:
            # ❌ ANTES:
            # dialog = MovimientoDialog(self.db, self)
            
            # ✅ AHORA: Pasar usuario_actual
            dialog = MovimientoDialog(self.db, self.usuario_actual, self)
            
            if dialog.exec_() == QDialog.Accepted:
                self.cargar_movimientos()
                self.cargar_bienes()
                self.actualizar_status_bar()
        except Exception as e:
            print(f"❌ Error abriendo formulario movimiento: {e}")

    def mostrar_configuracion_avanzada(self):
        """Muestra el diálogo de configuración avanzada"""
        try:
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
        """Actualiza la barra de estado con información de sincronización - VERSIÓN ROBUSTA"""
        try:
            # ✅ VERIFICAR QUE SYNC_MANAGER EXISTA
            if not hasattr(self, 'sync_manager') or self.sync_manager is None:
                # Estado temporal hasta que sync_manager esté listo
                stats = self.db.get_estadisticas()
                total_bienes = stats.get('total', 0)
                mensaje = f"👤 {self.usuario_actual['id']} | 📦 Total: {total_bienes} | 🔧 Inicializando..."
                self.status_bar.showMessage(mensaje)
                return
                
            # ✅ SI SYNC_MANAGER EXISTE, PROCEDER NORMALMENTE
            stats = self.db.get_estadisticas()
            estado_sync = self.sync_manager.obtener_estado()
            
            # Formatear modo de trabajo
            modo_trabajo = estado_sync.get("modo_trabajo", "desconocido").replace('_', ' ').title()
            
            # Estado de conexión
            if estado_sync.get("conectado_red", False):
                conexion = "🌐 Conectado"
                color_conexion = "#27ae60"  # Verde
            else:
                conexion = "❌ Sin Red" 
                color_conexion = "#e74c3c"  # Rojo
            
            # Formatear última sincronización
            ultima_sync = estado_sync.get("ultima_sincronizacion")
            if ultima_sync:
                from datetime import datetime
                try:
                    if 'Z' in ultima_sync:
                        fecha_dt = datetime.fromisoformat(ultima_sync.replace('Z', '+00:00'))
                    else:
                        fecha_dt = datetime.fromisoformat(ultima_sync)
                    
                    sync_str = f"Última sync: {fecha_dt.strftime('%H:%M')}"
                    color_sync = "#27ae60"  # Verde
                except Exception as e:
                    print(f"⚠️ Error formateando fecha sync: {e}")
                    sync_str = "Sync: Activo"
                    color_sync = "#f39c12"  # Naranja
            else:
                sync_str = "Sync: Pendiente"
                color_sync = "#f39c12"  # Naranja
            
            # Estadísticas de bienes
            total_bienes = stats.get('total', 0)
            en_deposito = stats.get('por_estado', {}).get('En depósito', 0)
            asignados = stats.get('por_estado', {}).get('Asignado', 0)
            bajas = stats.get('por_estado', {}).get('Baja definitiva', 0)
            
            # Construir mensaje de estado
            mensaje_estado = (
                f"👤 {self.usuario_actual['id']} | "
                f"📊 Modo: {modo_trabajo} | "
                f"{conexion} | "
                f"{sync_str} | "
                f"📦 Total: {total_bienes} | "
                f"🟢 En depósito: {en_deposito} | "
                f"🔵 Asignados: {asignados} | "
                f"🔴 Bajas: {bajas}"
            )
            
            # Mostrar en barra de estado
            self.status_bar.showMessage(mensaje_estado)
            
            # ✅ OPCIONAL: Agregar widgets (solo si sync_manager existe)
            if hasattr(self, '_actualizar_widgets_status_bar'):
                self._actualizar_widgets_status_bar(estado_sync, stats)
            
        except Exception as e:
            # Mensaje de fallback en caso de error
            error_msg = f"👤 {self.usuario_actual['id']} | Error actualizando estado: {str(e)}"
            if hasattr(self, 'status_bar') and self.status_bar is not None:
                self.status_bar.showMessage(error_msg)
            print(f"❌ Error en actualizar_status_bar: {e}")

    def _actualizar_widgets_status_bar(self, estado_sync, stats):
        """Agrega widgets visuales a la barra de estado - VERSIÓN ROBUSTA"""
        try:
            # ✅ NUEVO: Limpiar widgets existentes de forma segura
            if hasattr(self, '_status_widgets'):
                for widget in self._status_widgets:
                    try:
                        self.status_bar.removeWidget(widget)
                        widget.deleteLater()
                    except:
                        pass
            
            self._status_widgets = []
            
            # ✅ WIDGET DE CONEXIÓN
            label_conexion = QLabel()
            if estado_sync["conectado_red"]:
                label_conexion.setText("🌐")
                label_conexion.setToolTip("Conectado a la red")
                label_conexion.setStyleSheet("""
                    QLabel {
                        color: #27ae60; 
                        font-weight: bold; 
                        padding: 0 8px;
                        background-color: #d5f4e6;
                        border-radius: 10px;
                        margin: 2px;
                    }
                """)
            else:
                label_conexion.setText("❌")
                label_conexion.setToolTip("Sin conexión a la red")
                label_conexion.setStyleSheet("""
                    QLabel {
                        color: #e74c3c; 
                        font-weight: bold; 
                        padding: 0 8px;
                        background-color: #fadbd8;
                        border-radius: 10px;
                        margin: 2px;
                    }
                """)
            
            self.status_bar.addPermanentWidget(label_conexion)
            self._status_widgets.append(label_conexion)
            
            # ✅ WIDGET DE BIENES TOTALES
            total_bienes = stats.get('total', 0)
            label_bienes = QLabel(f"📦 {total_bienes}")
            label_bienes.setToolTip(f"Total de bienes en inventario: {total_bienes}")
            label_bienes.setStyleSheet("""
                QLabel {
                    color: #3498db; 
                    font-weight: bold; 
                    padding: 0 8px;
                    background-color: #d6eaf8;
                    border-radius: 10px;
                    margin: 2px;
                }
            """)
            self.status_bar.addPermanentWidget(label_bienes)
            self._status_widgets.append(label_bienes)
            
            # ✅ WIDGET DE BIENES EN DEPÓSITO
            en_deposito = stats.get('por_estado', {}).get('En depósito', 0)
            label_deposito = QLabel(f"🟢 {en_deposito}")
            label_deposito.setToolTip(f"Bienes disponibles en depósito: {en_deposito}")
            label_deposito.setStyleSheet("""
                QLabel {
                    color: #27ae60; 
                    font-weight: bold; 
                    padding: 0 8px;
                    background-color: #d5f4e6;
                    border-radius: 10px;
                    margin: 2px;
                }
            """)
            self.status_bar.addPermanentWidget(label_deposito)
            self._status_widgets.append(label_deposito)
            
            # ✅ WIDGET DE BIENES ASIGNADOS
            asignados = stats.get('por_estado', {}).get('Asignado', 0)
            if asignados > 0:
                label_asignados = QLabel(f"👤 {asignados}")
                label_asignados.setToolTip(f"Bienes asignados: {asignados}")
                label_asignados.setStyleSheet("""
                    QLabel {
                        color: #e67e22; 
                        font-weight: bold; 
                        padding: 0 8px;
                        background-color: #fdebd0;
                        border-radius: 10px;
                        margin: 2px;
                    }
                """)
                self.status_bar.addPermanentWidget(label_asignados)
                self._status_widgets.append(label_asignados)
            
            # ✅ WIDGET DE HORA ACTUAL
            from datetime import datetime
            hora_actual = datetime.now().strftime("%H:%M")
            label_hora = QLabel(f"🕒 {hora_actual}")
            label_hora.setToolTip("Hora actual del sistema")
            label_hora.setStyleSheet("""
                QLabel {
                    color: #9b59b6; 
                    font-weight: bold; 
                    padding: 0 8px;
                    background-color: #e8daef;
                    border-radius: 10px;
                    margin: 2px;
                }
            """)
            self.status_bar.addPermanentWidget(label_hora)
            self._status_widgets.append(label_hora)
            
            print("✅ Widgets de estado actualizados correctamente")
            
        except Exception as e:
            print(f"⚠️ Error en widgets de estado: {e}")
            # Fallback seguro: solo mostrar mensaje básico
            try:
                total_bienes = stats.get('total', 0)
                self.status_bar.showMessage(f"📦 Total bienes: {total_bienes}")
            except:
                pass

# ========== MÉTODOS DE EXPORTACIÓN REALES ==========

    def exportar_movimientos(self):
        """Exporta movimientos a Excel"""
        try:
            # Obtener movimientos
            movimientos = self.db.get_movimientos_detallados()
            
            if not movimientos:
                QMessageBox.warning(self, "Exportar", "No hay movimientos para exportar")
                return
            
            # Seleccionar archivo de destino
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Movimientos a Excel", 
                f"movimientos_agc_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                # Crear DataFrame con columnas visibles
                datos_exportar = []
                for mov in movimientos:
                    fila = {}
                    for nombre_col, campo_bd in self.mapeo_columnas_movimientos:
                        if self.columnas_visibles_movimientos.get(nombre_col, False):
                            valor = self.safe_get(mov, campo_bd)
                            if nombre_col == "Fecha Entrega":
                                try:
                                    fecha_dt = datetime.strptime(valor, "%Y-%m-%d")
                                    valor = fecha_dt.strftime("%d/%m/%Y")
                                except:
                                    pass
                            fila[nombre_col] = valor
                    datos_exportar.append(fila)
                
                df = pd.DataFrame(datos_exportar)
                
                # Exportar a Excel
                df.to_excel(file_path, index=False, engine='openpyxl')
                
                QMessageBox.information(self, "Éxito", 
                                    f"Movimientos exportados correctamente:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar movimientos: {str(e)}")

    def exportar_filtrados(self):
        """Exporta bienes filtrados a Excel"""
        try:
            # Obtener bienes (filtrados si hay filtros activos, sino todos)
            if self.filtros_activos:
                bienes = self.bien_manager.buscar_bienes(self.filtros_activos)
                tipo_export = "filtrados"
            else:
                bienes = self.db.list_bienes(limite=10000)
                tipo_export = "completo"
            
            if not bienes:
                QMessageBox.warning(self, "Exportar", "No hay datos para exportar")
                return
            
            # Seleccionar archivo de destino
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Bienes a Excel", 
                f"bienes_agc_{tipo_export}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Excel Files (*.xlsx)"
            )
            
            if file_path:
                # Crear DataFrame con columnas visibles
                datos_exportar = []
                for bien in bienes:
                    fila = {}
                    for nombre_col, campo_bd in self.mapeo_columnas:
                        if self.columnas_visibles_bienes.get(nombre_col, False):
                            fila[nombre_col] = self.safe_get(bien, campo_bd)
                    datos_exportar.append(fila)
                
                df = pd.DataFrame(datos_exportar)
                
                # Exportar a Excel
                df.to_excel(file_path, index=False, engine='openpyxl')
                
                QMessageBox.information(self, "Éxito", 
                                    f"Bienes exportados correctamente:\n{file_path}\n"
                                    f"Total: {len(bienes)} registros")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar bienes: {str(e)}")

    def exportar_estadisticas_pdf(self):
        """Exporta estadísticas a PDF"""
        try:
            # Obtener estadísticas
            stats = self.db.get_estadisticas()
            
            # Crear documento PDF
            document = QTextDocument()
            cursor = QTextCursor(document)
            
            # Estilos
            title_format = QTextCharFormat()
            title_format.setFont(QFont("Arial", 16, QFont.Bold))
            
            header_format = QTextCharFormat()
            header_format.setFont(QFont("Arial", 12, QFont.Bold))
            
            normal_format = QTextCharFormat()
            normal_format.setFont(QFont("Arial", 10))
            
            # Título
            cursor.insertText("📊 INFORME ESTADÍSTICO - INVENTARIO AGC\n", title_format)
            cursor.insertText(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n", normal_format)
            cursor.insertText(f"Usuario: {self.usuario_actual['id']}\n\n", normal_format)
            
            # Estadísticas generales
            cursor.insertText("ESTADÍSTICAS GENERALES\n", header_format)
            cursor.insertText(f"Total de bienes: {stats.get('total', 0)}\n", normal_format)
            
            # Distribución por estado
            cursor.insertText("\nDISTRIBUCIÓN POR ESTADO\n", header_format)
            por_estado = stats.get('por_estado', {})
            for estado, cantidad in por_estado.items():
                cursor.insertText(f"• {estado}: {cantidad}\n", normal_format)
            
            # Distribución por tipo
            cursor.insertText("\nDISTRIBUCIÓN POR TIPO\n", header_format)
            por_tipo = stats.get('por_tipo', {})
            for tipo, cantidad in por_tipo.items():
                cursor.insertText(f"• {tipo}: {cantidad}\n", normal_format)
            
            # Seleccionar archivo de destino
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Estadísticas a PDF", 
                f"estadisticas_agc_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Exportar a PDF
                printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
                printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                
                document.print_(printer)
                QMessageBox.information(self, "Éxito", f"Estadísticas exportadas a PDF:\n{file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar PDF: {str(e)}")

    def mostrar_configuracion_columnas(self):
        """Diálogo para configurar columnas visibles de bienes"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("⚙️ Configurar Columnas - Bienes")
            dialog.setModal(True)
            dialog.resize(400, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            title = QLabel("Seleccione las columnas visibles:")
            title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
            layout.addWidget(title)
            
            # Lista de checkboxes
            scroll = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            self.checkboxes_bienes = {}
            for nombre_col, _ in self.mapeo_columnas:
                checkbox = QCheckBox(nombre_col)
                checkbox.setChecked(self.columnas_visibles_bienes.get(nombre_col, False))
                scroll_layout.addWidget(checkbox)
                self.checkboxes_bienes[nombre_col] = checkbox
            
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)
            
            # Botones
            button_layout = QHBoxLayout()
            btn_aceptar = QPushButton("✅ Aplicar")
            btn_cancelar = QPushButton("❌ Cancelar")
            
            btn_aceptar.clicked.connect(lambda: self._aplicar_configuracion_columnas_bienes(dialog))
            btn_cancelar.clicked.connect(dialog.reject)
            
            button_layout.addWidget(btn_aceptar)
            button_layout.addWidget(btn_cancelar)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en configuración de columnas: {str(e)}")

    def _aplicar_configuracion_columnas_bienes(self, dialog):
        """Aplica la configuración de columnas de bienes"""
        try:
            # Actualizar configuración
            for nombre_col, checkbox in self.checkboxes_bienes.items():
                self.columnas_visibles_bienes[nombre_col] = checkbox.isChecked()
            
            # Reconfigurar tabla
            self.configurar_columnas_tabla()
            
            # Recargar datos
            self.cargar_bienes()
            
            dialog.accept()
            QMessageBox.information(self, "Éxito", "Configuración de columnas aplicada correctamente")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error aplicando configuración: {str(e)}")

    def mostrar_configuracion_columnas_movimientos(self):
        """Diálogo para configurar columnas visibles de movimientos"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("⚙️ Configurar Columnas - Movimientos")
            dialog.setModal(True)
            dialog.resize(400, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Título
            title = QLabel("Seleccione las columnas visibles:")
            title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
            layout.addWidget(title)
            
            # Lista de checkboxes
            scroll = QScrollArea()
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout(scroll_widget)
            
            self.checkboxes_movimientos = {}
            for nombre_col, _ in self.mapeo_columnas_movimientos:
                checkbox = QCheckBox(nombre_col)
                checkbox.setChecked(self.columnas_visibles_movimientos.get(nombre_col, False))
                scroll_layout.addWidget(checkbox)
                self.checkboxes_movimientos[nombre_col] = checkbox
            
            scroll.setWidget(scroll_widget)
            layout.addWidget(scroll)
            
            # Botones
            button_layout = QHBoxLayout()
            btn_aceptar = QPushButton("✅ Aplicar")
            btn_cancelar = QPushButton("❌ Cancelar")
            
            btn_aceptar.clicked.connect(lambda: self._aplicar_configuracion_columnas_movimientos(dialog))
            btn_cancelar.clicked.connect(dialog.reject)
            
            button_layout.addWidget(btn_aceptar)
            button_layout.addWidget(btn_cancelar)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en configuración de columnas: {str(e)}")

    def _aplicar_configuracion_columnas_movimientos(self, dialog):
        """Aplica la configuración de columnas de movimientos"""
        try:
            # Actualizar configuración
            for nombre_col, checkbox in self.checkboxes_movimientos.items():
                self.columnas_visibles_movimientos[nombre_col] = checkbox.isChecked()
            
            # Reconfigurar tabla
            self.configurar_columnas_movimientos()
            
            # Recargar datos
            self.cargar_movimientos()
            
            dialog.accept()
            QMessageBox.information(self, "Éxito", "Configuración de columnas aplicada correctamente")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error aplicando configuración: {str(e)}")

# ========== 🆕 NUEVOS MÉTODOS PDF - AGREGAR DESDE AQUÍ ==========

    def exportar_filtrados_pdf(self):
        """Exporta bienes filtrados a PDF con formato horizontal mejorado"""
        try:
            # Obtener bienes (filtrados si hay filtros activos, sino todos)
            if self.filtros_activos:
                bienes = self.bien_manager.buscar_bienes(self.filtros_activos)
                tipo_export = "filtrados"
            else:
                bienes = self.db.list_bienes(limite=10000)
                tipo_export = "completo"
            
            if not bienes:
                QMessageBox.warning(self, "Exportar PDF", "No hay datos para exportar")
                return
            
            # Crear documento PDF (SIN setPageSize aquí)
            document = QTextDocument()
            cursor = QTextCursor(document)
            
            # Estilos profesionales
            title_format = QTextCharFormat()
            title_format.setFont(QFont("Arial", 16, QFont.Bold))
            title_format.setForeground(Qt.darkBlue)
            
            subtitle_format = QTextCharFormat()
            subtitle_format.setFont(QFont("Arial", 12, QFont.Bold))
            subtitle_format.setForeground(Qt.darkGreen)
            
            header_format = QTextCharFormat()
            header_format.setFont(QFont("Arial", 9, QFont.Bold))
            header_format.setBackground(Qt.lightGray)
            header_format.setForeground(Qt.black)
            
            normal_format = QTextCharFormat()
            normal_format.setFont(QFont("Arial", 8))
            
            small_format = QTextCharFormat()
            small_format.setFont(QFont("Arial", 7))
            
            # Título principal
            cursor.insertBlock()
            cursor.insertText("🏢 INVENTARIO AGC - LISTADO DE BIENES\n", title_format)
            cursor.insertBlock()
            cursor.insertText(f"📅 Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | ", normal_format)
            cursor.insertText(f"👤 Usuario: {self.usuario_actual['id']} | ", normal_format)
            cursor.insertText(f"📊 Tipo: {tipo_export.upper()} | ", normal_format)
            cursor.insertText(f"📦 Total: {len(bienes)} registros\n", normal_format)
            cursor.insertBlock()
            
            # Crear tabla con MISMAS columnas que se ven en pantalla
            columnas_activas = [nombre for nombre, campo in self.mapeo_columnas 
                              if self.columnas_visibles_bienes.get(nombre, False)]
            
            # Encabezados de tabla
            cursor.insertText("LISTADO DE BIENES\n", subtitle_format)
            cursor.insertBlock()
            
            # Crear tabla con formato de ancho fijo
            ancho_columna = 15  # Caracteres por columna
            
            # Encabezados de tabla (formateados con ancho fijo)
            headers = ""
            for columna in columnas_activas:
                header = columna[:ancho_columna].ljust(ancho_columna)
                headers += header + " "
            
            cursor.insertText(headers + "\n", header_format)
            
            # Línea separadora
            separador = "-" * (len(columnas_activas) * (ancho_columna + 1))
            cursor.insertText(separador + "\n", normal_format)
            
            # Datos de la tabla
            registros_mostrados = 0
            for i, bien in enumerate(bienes):
                if registros_mostrados >= 100:  # Máximo 100 registros por página
                    break
                    
                fila = ""
                for nombre_col, campo_bd in self.mapeo_columnas:
                    if not self.columnas_visibles_bienes.get(nombre_col, False):
                        continue
                        
                    valor = self.safe_get(bien, campo_bd)
                    
                    # Aplicar misma lógica de visualización que en tabla
                    if nombre_col == "ESTADO":
                        estado = valor.lower()
                        nombre = self.safe_get(bien, "nombre")
                        apellido = self.safe_get(bien, "apellido")
                        
                        if (estado == "en depósito" or estado == "stock") and not (nombre.strip() or apellido.strip()):
                            valor = "🟢 Disp."
                    
                    # Formatear valor para ancho fijo
                    if len(str(valor)) > ancho_columna:
                        valor = str(valor)[:ancho_columna-2] + ".."
                    else:
                        valor = str(valor).ljust(ancho_columna)
                    
                    fila += valor + " "
                
                cursor.insertText(fila + "\n", small_format)
                registros_mostrados += 1
            
            # Información de paginación
            cursor.insertBlock()
            if len(bienes) > registros_mostrados:
                cursor.insertText(f"⚠️ Mostrando {registros_mostrados} de {len(bienes)} registros. Use Excel para lista completa.\n", normal_format)
            else:
                cursor.insertText(f"✅ Mostrando todos los {len(bienes)} registros.\n", normal_format)
            
            # Seleccionar archivo de destino
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Bienes a PDF", 
                f"bienes_agc_{tipo_export}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                # Configurar impresora PDF en horizontal
                printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
                printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QtPrintSupport.QPrinter.A4)
                printer.setOrientation(QtPrintSupport.QPrinter.Landscape)  # ← MODO HORIZONTAL
                printer.setPageMargins(10, 10, 10, 10, QtPrintSupport.QPrinter.Millimeter)
                
                # Generar PDF
                document.print_(printer)
                
                QMessageBox.information(self, "✅ Éxito", 
                                    f"📄 PDF generado correctamente:\n{file_path}\n"
                                    f"📊 Registros: {registros_mostrados} de {len(bienes)}")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al exportar PDF: {str(e)}")

    def exportar_movimientos_pdf(self):
        """Exporta movimientos a PDF con formato horizontal mejorado"""
        try:
            # Obtener movimientos
            movimientos = self.db.get_movimientos_detallados()
            
            if not movimientos:
                QMessageBox.warning(self, "Exportar PDF", "No hay movimientos para exportar")
                return
            
            # Crear documento PDF (SIN setPageSize aquí)
            document = QTextDocument()
            cursor = QTextCursor(document)
            
            # Estilos
            title_format = QTextCharFormat()
            title_format.setFont(QFont("Arial", 16, QFont.Bold))
            title_format.setForeground(Qt.darkBlue)
            
            subtitle_format = QTextCharFormat()
            subtitle_format.setFont(QFont("Arial", 12, QFont.Bold))
            subtitle_format.setForeground(Qt.darkGreen)
            
            header_format = QTextCharFormat()
            header_format.setFont(QFont("Arial", 9, QFont.Bold))
            header_format.setBackground(Qt.lightGray)
            
            small_format = QTextCharFormat()
            small_format.setFont(QFont("Arial", 7))
            
            normal_format = QTextCharFormat()
            normal_format.setFont(QFont("Arial", 8))
            
            # Título
            cursor.insertBlock()
            cursor.insertText("🔄 INVENTARIO AGC - MOVIMIENTOS\n", title_format)
            cursor.insertBlock()
            cursor.insertText(f"📅 Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')} | ", normal_format)
            cursor.insertText(f"👤 Usuario: {self.usuario_actual['id']} | ", normal_format)
            cursor.insertText(f"📋 Total: {len(movimientos)} movimientos\n", normal_format)
            cursor.insertBlock()
            
            # Columnas activas
            columnas_activas = [nombre for nombre, campo in self.mapeo_columnas_movimientos 
                              if self.columnas_visibles_movimientos.get(nombre, False)]
            
            cursor.insertText("LISTADO DE MOVIMIENTOS\n", subtitle_format)
            cursor.insertBlock()
            
            # Configurar ancho de columnas
            ancho_columna = 18
            
            # Encabezados
            headers = ""
            for columna in columnas_activas:
                header = columna[:ancho_columna].ljust(ancho_columna)
                headers += header + " "
            
            cursor.insertText(headers + "\n", header_format)
            
            # Línea separadora
            separador = "-" * (len(columnas_activas) * (ancho_columna + 1))
            cursor.insertText(separador + "\n", normal_format)
            
            # Datos
            movimientos_mostrados = 0
            for mov in movimientos:
                if movimientos_mostrados >= 80:  # Límite por página
                    break
                    
                fila = ""
                for nombre_col, campo_bd in self.mapeo_columnas_movimientos:
                    if not self.columnas_visibles_movimientos.get(nombre_col, False):
                        continue
                        
                    valor = self.safe_get(mov, campo_bd)
                    
                    # Misma lógica de visualización que en tabla
                    if nombre_col == "Responsable":
                        if " - " in valor:
                            valor = valor.split(" - ")[0]
                        if " (CUIT:" in valor:
                            valor = valor.split(" (CUIT:")[0]
                            
                    elif nombre_col == "Fecha Entrega":
                        try:
                            fecha_dt = datetime.strptime(valor, "%Y-%m-%d")
                            valor = fecha_dt.strftime("%d/%m/%Y")
                        except:
                            pass
                            
                    elif nombre_col == "PDF":
                        valor = "📎 PDF" if valor and os.path.exists(valor) else ""
                    
                    # Formatear para ancho fijo
                    if len(str(valor)) > ancho_columna:
                        valor = str(valor)[:ancho_columna-2] + ".."
                    else:
                        valor = str(valor).ljust(ancho_columna)
                    
                    fila += valor + " "
                
                cursor.insertText(fila + "\n", small_format)
                movimientos_mostrados += 1
            
            # Información de paginación
            cursor.insertBlock()
            if len(movimientos) > movimientos_mostrados:
                cursor.insertText(f"⚠️ Mostrando {movimientos_mostrados} de {len(movimientos)} movimientos.\n", normal_format)
            
            # Seleccionar archivo
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Movimientos a PDF", 
                f"movimientos_agc_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if file_path:
                printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.HighResolution)
                printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                printer.setPageSize(QtPrintSupport.QPrinter.A4)
                printer.setOrientation(QtPrintSupport.QPrinter.Landscape)  # ← MODO HORIZONTAL
                printer.setPageMargins(10, 10, 10, 10, QtPrintSupport.QPrinter.Millimeter)
                
                document.print_(printer)
                QMessageBox.information(self, "✅ Éxito", 
                                    f"📄 PDF de movimientos generado:\n{file_path}\n"
                                    f"📋 Movimientos: {movimientos_mostrados} de {len(movimientos)}")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error al exportar movimientos PDF: {str(e)}")

    def mostrar_historial_bien(self, index):
        """Muestra el historial del bien al hacer doble click - VERSIÓN CORREGIDA"""
        try:
            fila = index.row()
            if fila >= 0:
                # Obtener ficha del bien (columna 0 - FICHA)
                ficha = self.tabla_bienes.item(fila, 0).text()
                
                print(f"🎯 Doble click en fila {fila}, ficha: {ficha}")
                
                # Buscar el bien completo por ficha
                bien = self.db.obtener_bien_por_ficha(ficha)
                if bien:
                    print(f"✅ Bien encontrado: ID {bien['id']} - {bien['ficha']} - {bien['tipo']}")
                    
                    # Abrir diálogo de historial
                    from .dialogs.historial_dialog import HistorialDialog
                    dialog = HistorialDialog(self.db, bien, self)
                    dialog.exec_()
                else:
                    QMessageBox.warning(self, "Historial", f"No se encontró el bien con ficha: {ficha}")
                    
        except Exception as e:
            print(f"❌ Error mostrando historial: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo abrir el historial:\n{str(e)}")
    def generar_acta_seleccionado(self):
        """Genera acta para el bien seleccionado en la tabla"""
        try:
            # Obtener fila seleccionada
            fila_seleccionada = self.tabla_bienes.currentRow()
            if fila_seleccionada == -1:
                QMessageBox.warning(self, "Generar Acta", "❌ Por favor, selecciona un bien de la tabla")
                return
            
            # Obtener datos del bien seleccionado
            ficha = self.tabla_bienes.item(fila_seleccionada, 0).text()  # Columna FICHA
            
            # Buscar el bien completo en la base de datos
            bien = self.db.obtener_bien_por_ficha(ficha)
            if not bien:
                QMessageBox.warning(self, "Generar Acta", f"❌ No se encontró el bien con ficha: {ficha}")
                return
            
            # Determinar tipo de acta automáticamente
            estado = bien.get('estado', '').lower()
            if estado in ['asignado', 'en uso']:
                tipo_acta = "entrega"
            else:
                tipo_acta = "recepcion"
            
            # Generar acta
            from generador_actas import GeneradorActas
            generador = GeneradorActas()
            print(f"🔍 DEBUG - usuario_actual completo:")
            print(f"   {self.usuario_actual}")
            if tipo_acta == "entrega":
                ruta_acta = generador.generar_acta_entrega(bien, self.usuario_actual)  # ← Sin ['id']
            else:
                ruta_acta = generador.generar_acta_recepcion(bien, self.usuario_actual)  # ← Sin ['id']
            
            if ruta_acta and not ruta_acta.startswith('❌'):
                QMessageBox.information(self, "✅ Éxito", 
                                    f"Acta de {tipo_acta.upper()} generada:\n{ruta_acta}\n\n"
                                    f"📁 Guardada en: actas_generadas/")
                
                # Abrir el archivo generado
                import os
                os.startfile(ruta_acta)  # Solo Windows
            else:
                QMessageBox.critical(self, "❌ Error", f"No se pudo generar el acta:\n{ruta_acta}")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error generando acta:\n{str(e)}")