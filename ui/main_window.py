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
                           QListWidget, QListWidgetItem, QDialogButtonBox, QHeaderView)
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
            "Fecha": True,
            "N° Transferencia": False,
            #"Responsable": False,
            "Nombre": True,
            "Apellido": True,  
            "DNI/CUIT": False,
            "Área": True,
            "Cantidad Bienes": True,
            "PRD": True,
            "Fichas": False,
            "Observaciones": False,
            "Acta": True,
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
            ("Fecha", "fecha"),
            ("N° Transferencia", "numero_transferencia"),
            ("Responsable", "responsable"),  # ← MANTENER PARA COMPATIBILIDAD
            ("Nombre", "responsable_nombre"),
            ("Apellido", "responsable_apellido"),
            ("DNI/CUIT", "responsable_dni_cuit"),
            ("Área", "responsable_institucional"),
            ("Cantidad Bienes", "cantidad_bienes"),
            ("PRD", "prds"),
            ("Fichas", "fichas"),
            ("Observaciones", "observaciones"),
            ("Acta", "archivo_path"),
            ("Acciones", "id")  # ← NUEVO: Usar "id" como campo base para acciones
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
        
        # 🔍 BARRA DE BÚSQUEDA RÁPIDA - PASO 1
        busqueda_layout = QHBoxLayout()

        self.buscador_movimientos = QLineEdit()
        self.buscador_movimientos.setPlaceholderText("🔍 Buscar por responsable, área, tipo, observaciones...")
        self.buscador_movimientos.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                font-size: 12px;
                border: 2px solid #3498db;
                border-radius: 5px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #2980b9;
            }
        """)
        self.buscador_movimientos.textChanged.connect(self.filtrar_movimientos_tiempo_real)

        busqueda_layout.addWidget(QLabel("Buscar:"))
        busqueda_layout.addWidget(self.buscador_movimientos)
        busqueda_layout.addStretch()

        layout.addLayout(busqueda_layout)
        # 🎯 FILTROS RÁPIDOS POR TIPO - PASO 2
        filtros_rapidos_layout = QHBoxLayout()

        # Botones de filtro rápido
        self.btn_todos_movimientos = QPushButton("📋 Todos")
        self.btn_entregas = QPushButton("📤 Entregas")
        self.btn_devoluciones = QPushButton("📥 Devoluciones") 
        self.btn_bajas = QPushButton("🗑️ Bajas")
        self.btn_hoy = QPushButton("🔄 Hoy")

        # Estilo para los botones de filtro
        estilo_boton_filtro = """
            QPushButton {
                padding: 6px 12px;
                font-size: 11px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #ecf0f1;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #a6acaf;
            }
            QPushButton:checked {
                background-color: #3498db;
                color: white;
                border-color: #2980b9;
            }
        """

        # Aplicar estilo a todos los botones de filtro
        for btn in [self.btn_todos_movimientos, self.btn_entregas, self.btn_devoluciones, self.btn_bajas, self.btn_hoy]:
            btn.setStyleSheet(estilo_boton_filtro)
            btn.setCheckable(True)  # Para que se mantengan presionados

        # Botón "Todos" activado por defecto
        self.btn_todos_movimientos.setChecked(True)

        # Conectar botones a funciones de filtro
        self.btn_todos_movimientos.clicked.connect(lambda: self.filtrar_por_tipo_movimiento("TODOS"))
        self.btn_entregas.clicked.connect(lambda: self.filtrar_por_tipo_movimiento("Entrega"))
        self.btn_devoluciones.clicked.connect(lambda: self.filtrar_por_tipo_movimiento("Devolución"))
        self.btn_bajas.clicked.connect(lambda: self.filtrar_por_tipo_movimiento("Baja"))
        self.btn_hoy.clicked.connect(self.filtrar_movimientos_hoy)

        # Agregar botones al layout
        filtros_rapidos_layout.addWidget(QLabel("Filtrar:"))
        filtros_rapidos_layout.addWidget(self.btn_todos_movimientos)
        filtros_rapidos_layout.addWidget(self.btn_entregas)
        filtros_rapidos_layout.addWidget(self.btn_devoluciones)
        filtros_rapidos_layout.addWidget(self.btn_bajas)
        filtros_rapidos_layout.addWidget(self.btn_hoy)
        filtros_rapidos_layout.addStretch()

        layout.addLayout(filtros_rapidos_layout)
        
        # Etiqueta de columnas activas
        self.label_columnas_mov_activas = QLabel("Columnas visibles: Tipo, Fecha Entrega, N° Transferencia, Responsable, Cantidad Bienes, PRD, PDF")
        self.label_columnas_mov_activas.setStyleSheet("color: #2E86AB; font-size: 11px; padding: 2px;")
        layout.addWidget(self.label_columnas_mov_activas)
        
        # Tabla de movimientos
        self.tabla_movimientos = QTableWidget()
        self.tabla_movimientos.cellClicked.connect(self._manejar_click_acta)
        self.configurar_columnas_movimientos()
        layout.addWidget(self.tabla_movimientos)
        # ✅ CONECTAR DOBLE CLICK A FUNCIÓN DE RESUMEN
        self.tabla_movimientos.doubleClicked.connect(self.mostrar_resumen_movimiento)
        self.tabs.addTab(tab, "🔄 Movimientos")

    def _crear_tab_estadisticas(self):
        """Crea el panel de estadísticas ejecutivo - VERSIÓN INTERACTIVA"""
        from widgets.dashboard import DashboardConfigurableWidget
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # ✅ MODIFICADO: Pasar 'self' como parent para interactividad
        self.dashboard_widget = DashboardConfigurableWidget(self.db, self)  # ← ¡AGREGAR self!
        layout.addWidget(self.dashboard_widget)

        self.tabs.addTab(tab, "📊 Dashboard")

        # Opcional: Actualizar dashboard cada vez que se entra a la pestaña
        def actualizar_al_mostrar(index):
            if self.tabs.tabText(index) == "📊 Dashboard":
                if hasattr(self.dashboard_widget, 'filtros_actuales') and self.dashboard_widget.filtros_actuales:
                    self.dashboard_widget._cargar_datos_con_filtros(self.dashboard_widget.filtros_actuales)
                else:
                    self.dashboard_widget.cargar_datos_iniciales()

        self.tabs.currentChanged.connect(actualizar_al_mostrar)

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
        """Carga movimientos con diseño optimizado - SIN COLUMNA ACCIONES"""
        try:
            movimientos = self.db.get_movimientos_detallados()
                
            self.tabla_movimientos.setRowCount(len(movimientos))
            
            for i, mov in enumerate(movimientos):
                col_idx = 0
                for nombre_columna, campo_bd in self.mapeo_columnas_movimientos:
                    if not self.columnas_visibles_movimientos.get(nombre_columna, False):
                        continue
                        
                    # ✅ SOLO COLUMNAS DE DATOS - SIN WIDGETS COMPLEJOS
                    if nombre_columna == "Acta":
                        archivo_item = self._crear_item_acta_simple(mov)
                        self.tabla_movimientos.setItem(i, col_idx, archivo_item)
                        
                    elif nombre_columna == "Fecha":
                        fecha_original = self.safe_get(mov, "fecha")
                        try:
                            fecha_dt = datetime.strptime(fecha_original, "%Y-%m-%d")
                            valor = fecha_dt.strftime("%d/%m")  # Formato corto
                        except:
                            valor = fecha_original
                        self.tabla_movimientos.setItem(i, col_idx, QTableWidgetItem(valor))
                        
                    elif nombre_columna == "Área":
                        area_completa = self.safe_get(mov, "responsable_institucional")
                        # Acortar nombres largos de áreas
                        if len(area_completa) > 20:
                            valor = area_completa[:18] + ".."
                        else:
                            valor = area_completa
                        self.tabla_movimientos.setItem(i, col_idx, QTableWidgetItem(valor))
                        
                    elif nombre_columna == "Cantidad Bienes":
                        cantidad = self.safe_get(mov, "cantidad_bienes")
                        valor = f"{cantidad}📦" if cantidad and cantidad != "0" else "0"
                        item = QTableWidgetItem(valor)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.tabla_movimientos.setItem(i, col_idx, item)
                        
                    elif nombre_columna in ["Tipo", "PRD"]:
                        valor = self.safe_get(mov, campo_bd)
                        item = QTableWidgetItem(valor)
                        item.setTextAlignment(Qt.AlignCenter)
                        self.tabla_movimientos.setItem(i, col_idx, item)
                        
                    else:
                        # Para las demás columnas (Nombre, Apellido, etc.)
                        valor = self.safe_get(mov, campo_bd)
                        self.tabla_movimientos.setItem(i, col_idx, QTableWidgetItem(valor))
                    
                    col_idx += 1
                
                # ✅ LÍMITE DE RENDIMIENTO
                if i >= 1000:
                    print(f"⚠️ Límite de rendimiento alcanzado: 1000 filas")
                    break
                
            # ✅ AJUSTES FINALES CON EL MÉTODO NUEVO
            self._aplicar_ajustes_tabla_movimientos_optimizada()
            
            # ✅ FEEDBACK AL USUARIO
            movimientos_cargados = min(len(movimientos), 1000)
            self.status_bar.showMessage(
                f"✅ Cargados {movimientos_cargados} movimientos - " 
                f"🖱️ Doble click para detalles completos", 
                5000
            )
            
            print(f"✅ Tabla de movimientos optimizada: {movimientos_cargados} registros")
            
        except Exception as e:
            print(f"❌ Error cargando movimientos: {e}")
            import traceback
            traceback.print_exc()
            self.status_bar.showMessage("❌ Error cargando movimientos", 3000)

    def _aplicar_ajustes_tabla_movimientos(self):
        """Aplica ajustes finales a la tabla de movimientos"""
        try:
            # Ajustar automáticamente el tamaño de columnas
            self.tabla_movimientos.resizeColumnsToContents()
            
            # Configurar anchos fijos para columnas clave
            header = self.tabla_movimientos.horizontalHeader()
            
            # Mapeo de anchos fijos recomendados
            anchos_fijos = {
                "Tipo": 80,
                "Fecha": 70,
                "Nombre": 100,
                "Apellido": 100,
                "Área": 120,
                "Cantidad Bienes": 80,
                "PRD": 80,
                "Acta": 70,
                "Acciones": 70
            }
            
            # Aplicar anchos fijos
            col_idx = 0
            for nombre_columna, campo_bd in self.mapeo_columnas_movimientos:
                if not self.columnas_visibles_movimientos.get(nombre_columna, False):
                    continue
                    
                if nombre_columna in anchos_fijos:
                    header.setSectionResizeMode(col_idx, QHeaderView.Fixed)
                    self.tabla_movimientos.setColumnWidth(col_idx, anchos_fijos[nombre_columna])
                else:
                    header.setSectionResizeMode(col_idx, QHeaderView.Interactive)
                
                col_idx += 1
                
            # Permitir que la última columna se expanda
            header.setStretchLastSection(True)
            
        except Exception as e:
            print(f"❌ Error aplicando ajustes de tabla: {e}")

    def _crear_item_acta_simple(self, movimiento):
        """Crea item de acta SIMPLIFICADO - solo PDF firmado o subir"""
        try:
            archivo_item = QTableWidgetItem()
            
            # 1. Solo verificar PDF (DOCX es temporal, no lo mostramos)
            archivo_pdf = self.safe_get(movimiento, "archivo_path_pdf")
            
            # 2. Compatibilidad con campo antiguo
            if not archivo_pdf:
                archivo_pdf = self.safe_get(movimiento, "archivo_path")
            
            # 3. Verificar existencia del PDF
            pdf_existe = False
            if archivo_pdf:
                # Intentar verificar si el archivo existe
                try:
                    pdf_existe = os.path.exists(archivo_pdf)
                except:
                    pdf_existe = False
            
            # 4. Obtener ID del movimiento PARA SUBIR
            movimiento_id = None
            try:
                # Usar safe_get para obtener el ID
                movimiento_id_str = self.safe_get(movimiento, 'id')
                if movimiento_id_str and movimiento_id_str.strip():
                    movimiento_id = int(movimiento_id_str)
            except (ValueError, TypeError) as e:
                print(f"⚠️ Error obteniendo ID del movimiento: {e}")
                movimiento_id = None
            
            # 5. DEBUG
            print(f"🔍 Creando item acta - PDF: {archivo_pdf}, Existe: {pdf_existe}, ID: {movimiento_id}")
            
            # 6. Asignar texto simple según estado
            if pdf_existe:
                archivo_item.setText("✅ ACTA FIRMADA")
                archivo_item.setToolTip(f"Acta firmada: {os.path.basename(archivo_pdf)}\nClick para abrir")
                archivo_item.setForeground(Qt.darkGreen)
                archivo_item.setData(Qt.UserRole, {"pdf": archivo_pdf})
                
            elif movimiento_id:
                archivo_item.setText("📤 SUBIR ACTA")
                archivo_item.setToolTip(f"Click para subir acta firmada (PDF)\nMovimiento ID: {movimiento_id}")
                archivo_item.setForeground(Qt.darkBlue)
                archivo_item.setData(Qt.UserRole, {"movimiento_id": movimiento_id})
                
            else:
                # Caso error: no hay PDF ni ID válido
                archivo_item.setText("❌ ERROR")
                archivo_item.setToolTip("Error: No se puede identificar el movimiento")
                archivo_item.setForeground(Qt.darkRed)
            
            archivo_item.setTextAlignment(Qt.AlignCenter)
            return archivo_item
            
        except Exception as e:
            print(f"❌ Error creando item de acta: {e}")
            import traceback
            traceback.print_exc()
            item = QTableWidgetItem("❌")
            item.setTextAlignment(Qt.AlignCenter)
            item.setToolTip("Error cargando información")
            return item
        
    def _manejar_click_acta(self, row, column):
        """Maneja clicks en la columna 'Acta' - abre o sube PDF"""
        try:
            # 1. Verificar que el click sea en columna "Acta"
            nombre_columna = self._obtener_nombre_columna_por_indice(column)
            if nombre_columna != "Acta":
                return  # No es la columna de acta, ignorar
                
            # 2. Obtener el item de la tabla
            item = self.tabla_movimientos.item(row, column)
            if not item:
                print(f"⚠️ No hay item en fila {row}, columna {column}")
                return
                
            # 3. Obtener datos almacenados en UserRole
            datos = item.data(Qt.UserRole)
            
            # 4. DEBUG: Ver qué datos tenemos
            print(f"🔍 Click en acta - fila {row}, datos: {datos}")
            
            # 5. Si no hay datos, mostrar advertencia
            if not datos:
                QMessageBox.warning(self, "Atención", 
                                "No se puede procesar este movimiento.\n"
                                "Falta información de identificación.")
                return
                
            # 6. Si tiene PDF, abrirlo
            if "pdf" in datos and datos["pdf"]:
                pdf_path = datos["pdf"]
                print(f"📄 Abriendo PDF: {pdf_path}")
                self.abrir_archivo_desde_ruta(pdf_path)
                
            # 7. Si tiene movimiento_id, subir acta
            elif "movimiento_id" in datos and datos["movimiento_id"]:
                movimiento_id = datos["movimiento_id"]
                print(f"📤 Subiendo acta para movimiento ID: {movimiento_id}")
                self._subir_acta_firmada(movimiento_id)
                
            # 8. Si no coincide con ningún caso
            else:
                QMessageBox.information(self, "Información", 
                                    "Estado del acta no reconocido.\n"
                                    "Contacte al administrador.")
                
        except Exception as e:
            print(f"❌ Error manejando click en acta: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", 
                            f"No se pudo procesar la solicitud:\n{str(e)}")
            
    def _subir_acta_firmada(self, movimiento_id):
        """Abre diálogo para subir acta firmada (PDF) y actualiza BD"""
        try:
            print(f"📤 Iniciando subida de acta para movimiento ID: {movimiento_id}")
            
            # 1. Diálogo para seleccionar archivo PDF
            file_path, _ = QFileDialog.getOpenFileName(
                self, 
                "Seleccionar Acta Firmada (PDF)",
                "",  # Directorio inicial vacío
                "Archivos PDF (*.pdf);;Todos los archivos (*.*)"
            )
            
            if not file_path or not os.path.exists(file_path):
                print("❌ Usuario canceló o archivo no existe")
                return  # Usuario canceló o archivo inválido
                
            # 2. Verificar que sea PDF
            if not file_path.lower().endswith('.pdf'):
                QMessageBox.warning(self, "Formato incorrecto", 
                                "Por favor, seleccione un archivo PDF (.pdf).")
                return
            
            # 3. Verificar tamaño (opcional, máximo 10MB)
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:  # 10MB
                QMessageBox.warning(self, "Archivo muy grande",
                                "El archivo PDF es muy grande (máximo 10MB).")
                return
            
            # 4. Obtener datos del movimiento para nombre descriptivo
            movimiento = self.db.obtener_movimiento_por_id(movimiento_id)
            if not movimiento:
                QMessageBox.critical(self, "Error", 
                                f"No se encontró el movimiento ID: {movimiento_id}")
                return
            
            print(f"✅ Movimiento encontrado: {movimiento.get('tipo', 'N/A')}")
            
            # 5. Usar MovimientoManager para guardar correctamente
            try:
                from core.movimiento_manager import MovimientoManager
                movimiento_manager = MovimientoManager(self.db)
                
                ruta_pdf_final = movimiento_manager._guardar_pdf_correctamente(
                    file_path, 
                    movimiento_id, 
                    movimiento
                )
                
                if not ruta_pdf_final:
                    QMessageBox.critical(self, "Error", 
                                    "No se pudo guardar el PDF en la carpeta local.")
                    return
                    
                print(f"✅ PDF guardado en: {ruta_pdf_final}")
                
            except Exception as mgr_error:
                print(f"⚠️ Error con MovimientoManager: {mgr_error}")
                # Fallback: guardar directamente
                import shutil
                import datetime
                
                # Crear carpeta si no existe
                os.makedirs("actas_local", exist_ok=True)
                
                # Nombre descriptivo
                fecha = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                nombre = f"ACTA_{movimiento_id}_{fecha}.pdf"
                ruta_pdf_final = os.path.join("actas_local", nombre)
                
                shutil.copy2(file_path, ruta_pdf_final)
                print(f"✅ PDF guardado (fallback): {ruta_pdf_final}")
            
            # 6. Actualizar base de datos
            if self.db.actualizar_pdf_movimiento(movimiento_id, ruta_pdf_final):
                print(f"✅ Base de datos actualizada para movimiento {movimiento_id}")
                
                # 7. Actualizar tabla visualmente
                self.cargar_movimientos()
                
                # 8. Mostrar confirmación
                QMessageBox.information(self, "✅ Éxito", 
                                    f"Acta firmada guardada exitosamente.\n\n"
                                    f"📄 Archivo: {os.path.basename(ruta_pdf_final)}\n"
                                    f"📁 Ubicación: actas_local/\n"
                                    f"🆔 Movimiento: {movimiento_id}")
            else:
                QMessageBox.critical(self, "Error", 
                                "No se pudo actualizar la base de datos.\n"
                                "El archivo se guardó pero no se vinculó al movimiento.")
                
        except Exception as e:
            print(f"❌ Error subiendo acta: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", 
                            f"No se pudo subir el acta:\n{str(e)}")
        

    def _manejar_click_tabla_movimientos(self, row, column):
        """Maneja los clicks en la tabla de movimientos"""
        try:
            # Obtener nombre de la columna clickeada
            nombre_columna = None
            col_idx = 0
            for nombre, campo in self.mapeo_columnas_movimientos:
                if self.columnas_visibles_movimientos.get(nombre, False):
                    if col_idx == column:
                        nombre_columna = nombre
                        break
                    col_idx += 1
            
            if nombre_columna == "PDF":
                self._abrir_archivo_movimiento(row, column)
                
        except Exception as e:
            print(f"❌ Error manejando click en tabla: {e}")

    def _abrir_archivo_movimiento(self, row, column):
        """Abre el archivo PDF o DOCX asociado al movimiento - VERSIÓN ACTUALIZADA"""
        try:
            item = self.tabla_movimientos.item(row, column)
            if not item:
                return
                
            archivos_data = item.data(Qt.UserRole)
            
            if not archivos_data:
                QMessageBox.information(self, "Sin archivos", 
                                    "No hay archivos adjuntos para este movimiento.")
                return
            
            # Si hay múltiples archivos, preguntar cuál abrir
            if isinstance(archivos_data, dict):
                if 'pdf' in archivos_data and 'docx' in archivos_data:
                    respuesta = QMessageBox.question(
                        self, 
                        "Seleccionar archivo",
                        "Este movimiento tiene ambos archivos:\n\n"
                        f"📄 PDF: {os.path.basename(archivos_data['pdf'])}\n"
                        f"📝 DOCX: {os.path.basename(archivos_data['docx'])}\n\n"
                        "¿Qué archivo deseas abrir?",
                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                        QMessageBox.Yes
                    )
                    
                    if respuesta == QMessageBox.Yes:
                        # ✅ CAMBIAR: Usar el nuevo método
                        self.abrir_archivo_desde_ruta(archivos_data['pdf'])
                    elif respuesta == QMessageBox.No:
                        # ✅ CAMBIAR: Usar el nuevo método
                        self.abrir_archivo_desde_ruta(archivos_data['docx'])
                    
                elif 'pdf' in archivos_data:
                    # ✅ CAMBIAR: Usar el nuevo método
                    self.abrir_archivo_desde_ruta(archivos_data['pdf'])
                elif 'docx' in archivos_data:
                    # ✅ CAMBIAR: Usar el nuevo método
                    self.abrir_archivo_desde_ruta(archivos_data['docx'])
                    
        except Exception as e:
            print(f"❌ Error abriendo archivo del movimiento: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo abrir el archivo:\n{str(e)}")

    def abrir_archivo_desde_ruta(self, ruta_archivo):
        """Abre un archivo con la aplicación por defecto del sistema"""
        try:
            if os.path.exists(ruta_archivo):
                import platform
                sistema = platform.system()
                
                if sistema == "Windows":
                    os.startfile(ruta_archivo)
                elif sistema == "Darwin":  # macOS
                    import subprocess
                    subprocess.run(["open", ruta_archivo])
                else:  # Linux y otros
                    import subprocess
                    subprocess.run(["xdg-open", ruta_archivo])
                    
                print(f"✅ Archivo abierto: {ruta_archivo}")
            else:
                QMessageBox.warning(self, "Archivo no encontrado", 
                                f"El archivo no existe:\n{ruta_archivo}")
                
        except Exception as e:
            print(f"❌ Error abriendo archivo: {e}")
            QMessageBox.critical(self, "Error", 
                            f"No se pudo abrir el archivo:\n{str(e)}\n\n"
                            f"Ruta: {ruta_archivo}")

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
            
    def filtrar_movimientos_tiempo_real(self, texto_busqueda):
        """Filtra movimientos en tiempo real según el texto de búsqueda - PASO 1"""
        try:
            if not texto_busqueda.strip():
                # Si no hay texto, mostrar todos los movimientos
                self.cargar_movimientos()
                return
                
            texto = texto_busqueda.lower().strip()
            
            # Obtener todos los movimientos
            movimientos = self.db.get_movimientos_detallados()
            if not movimientos:
                return
                
            # Filtrar movimientos
            movimientos_filtrados = []
            for mov in movimientos:
                # Convertir a diccionario si es sqlite.Row
                if hasattr(mov, 'keys'):
                    mov_dict = dict(mov)
                else:
                    mov_dict = mov
                    
                # Buscar en diferentes campos
                campos_busqueda = [
                    str(mov_dict.get('tipo', '')).lower(),
                    str(mov_dict.get('responsable', '')).lower(),
                    str(mov_dict.get('responsable_nombre', '')).lower(),
                    str(mov_dict.get('responsable_apellido', '')).lower(),
                    str(mov_dict.get('responsable_institucional', '')).lower(),
                    str(mov_dict.get('observaciones', '')).lower(),
                    str(mov_dict.get('fichas', '')).lower(),
                    str(mov_dict.get('prds', '')).lower()
                ]
                
                # Si alguno de los campos contiene el texto
                if any(texto in campo for campo in campos_busqueda):
                    movimientos_filtrados.append(mov)
            
            # Mostrar resultados filtrados
            self.mostrar_movimientos_filtrados(movimientos_filtrados)
            
        except Exception as e:
            print(f"❌ Error en búsqueda en tiempo real: {e}")

    def mostrar_movimientos_filtrados(self, movimientos_filtrados):
        """Muestra movimientos filtrados en la tabla - PASO 1"""
        try:
            self.tabla_movimientos.setRowCount(len(movimientos_filtrados))
            
            for i, mov in enumerate(movimientos_filtrados):
                col_idx = 0
                for nombre_columna, campo_bd in self.mapeo_columnas_movimientos:
                    if not self.columnas_visibles_movimientos.get(nombre_columna, False):
                        continue
                        
                    if nombre_columna == "PDF":
                        archivo_item = self._crear_item_archivo_movimiento(mov)
                        self.tabla_movimientos.setItem(i, col_idx, archivo_item)
                        
                    elif nombre_columna == "Responsable":
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
                            
                    else:
                        valor = self.safe_get(mov, campo_bd)
                    
                    if nombre_columna != "PDF":
                        self.tabla_movimientos.setItem(i, col_idx, QTableWidgetItem(valor))
                    
                    col_idx += 1
            
            # Actualizar estado
            self.status_bar.showMessage(f"✅ Encontrados {len(movimientos_filtrados)} movimientos", 3000)
            
        except Exception as e:
            print(f"❌ Error mostrando movimientos filtrados: {e}")
            
    def mostrar_resumen_movimiento(self, index):
        """Doble click muestra TODO en una sola pantalla - VERSIÓN MEJORADA"""
        try:
            row = index.row()
            column = index.column()
            
            # ✅ DETECTAR SI ES CLICK EN COLUMNA "ACTA"
            nombre_columna = self._obtener_nombre_columna_por_indice(column)
            
            if nombre_columna == "Acta":
                # 📄 ACCESO RÁPIDO A ARCHIVOS
                self._abrir_archivos_directo(row)
                return
                
            # 📊 ACCESO A RESUMEN COMPLETO
            movimientos = self.db.get_movimientos_detallados()
            if row >= len(movimientos):
                print(f"⚠️ Fila {row} fuera de rango")
                return
                
            movimiento_row = movimientos[row]
            movimiento = dict(movimiento_row)
            movimiento_id = movimiento['id']

            # Obtener bienes del movimiento
            bienes_movimiento = self.db.get_bienes_de_movimiento(movimiento_id)
            
            # ✅ FEEDBACK VISUAL
            self.status_bar.showMessage(f"🔍 Cargando detalles del movimiento #{movimiento_id}...")
            
            # Abrir diálogo de resumen completo
            from ui.dialogs.resumen_movimiento_dialog import ResumenMovimientoDialog
            dialog = ResumenMovimientoDialog(movimiento, bienes_movimiento, self)
            dialog.exec_()
            
            # ✅ FEEDBACK FINAL
            self.status_bar.showMessage(f"✅ Movimiento #{movimiento_id} revisado", 2000)

        except Exception as e:
            print(f"❌ Error en doble click: {e}")
            QMessageBox.critical(self, "Error", 
                            f"No se pudo abrir el resumen:\n{str(e)}\n\n"
                            f"💡 Asegúrate de que el movimiento tenga datos válidos.")

    def _obtener_nombre_columna_por_indice(self, column_index):
        """Obtiene el nombre de la columna por su índice"""
        try:
            col_idx = 0
            for nombre_col, campo_bd in self.mapeo_columnas_movimientos:
                if not self.columnas_visibles_movimientos.get(nombre_col, False):
                    continue
                if col_idx == column_index:
                    return nombre_col
                col_idx += 1
            return None
        except:
            return None

    def _abrir_archivos_directo(self, row):
        """Abre archivos directamente al hacer click en columna Acta"""
        try:
            movimientos = self.db.get_movimientos_detallados()
            if row < len(movimientos):
                movimiento = dict(movimientos[row])
                movimiento_id = movimiento['id']
                
                # ✅ USAR TU MÉTODO EXISTENTE
                self.abrir_acta_movimiento(movimiento_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                            f"No se pudieron abrir los archivos:\n{str(e)}")
            
    def filtrar_por_tipo_movimiento(self, tipo):
        """Filtra movimientos por tipo - PASO 2"""
        try:
            # Desmarcar todos los botones primero
            self.btn_todos_movimientos.setChecked(False)
            self.btn_entregas.setChecked(False)
            self.btn_devoluciones.setChecked(False)
            self.btn_bajas.setChecked(False)
            
            # Marcar el botón actual
            if tipo == "TODOS":
                self.btn_todos_movimientos.setChecked(True)
                self.cargar_movimientos()
                self.status_bar.showMessage("✅ Mostrando todos los movimientos", 2000)
                return
            elif tipo == "Entrega":
                self.btn_entregas.setChecked(True)
            elif tipo == "Devolución":
                self.btn_devoluciones.setChecked(True)
            elif tipo == "Baja":
                self.btn_bajas.setChecked(True)
            
            # Obtener todos los movimientos y filtrar
            movimientos = self.db.get_movimientos_detallados()
            if not movimientos:
                return
                
            movimientos_filtrados = []
            for mov in movimientos:
                mov_tipo = self.safe_get(mov, "tipo")
                if mov_tipo.lower() == tipo.lower():
                    movimientos_filtrados.append(mov)
            
            # Mostrar resultados
            self.mostrar_movimientos_filtrados(movimientos_filtrados)
            self.status_bar.showMessage(f"✅ {len(movimientos_filtrados)} movimientos de {tipo}", 3000)
            
        except Exception as e:
            print(f"❌ Error filtrando por tipo: {e}")

    def filtrar_movimientos_hoy(self):
        """Filtra movimientos del día actual - PASO 2"""
        try:
            from datetime import datetime
            
            hoy = datetime.now().strftime("%Y-%m-%d")
            
            # Obtener todos los movimientos
            movimientos = self.db.get_movimientos_detallados()
            if not movimientos:
                return
                
            movimientos_hoy = []
            for mov in movimientos:
                fecha_mov = self.safe_get(mov, "fecha")
                if fecha_mov == hoy:
                    movimientos_hoy.append(mov)
            
            # Mostrar resultados
            self.mostrar_movimientos_filtrados(movimientos_hoy)
            
            # Actualizar estado de botones
            self.btn_todos_movimientos.setChecked(False)
            self.btn_entregas.setChecked(False)
            self.btn_devoluciones.setChecked(False)
            self.btn_bajas.setChecked(False)
            self.btn_hoy.setChecked(True)
            
            self.status_bar.showMessage(f"✅ {len(movimientos_hoy)} movimientos de hoy", 3000)
            
        except Exception as e:
            print(f"❌ Error filtrando movimientos de hoy: {e}")
            
    def abrir_acta_movimiento(self, movimiento_id):
        """Abre el acta del movimiento para visualización - PASO 4 CORREGIDO"""
        try:
            print(f"📄 Abriendo acta del movimiento: {movimiento_id}")
            
            # Obtener datos del movimiento
            movimiento_data = self.db.obtener_movimiento_por_id(movimiento_id)
            if not movimiento_data:
                QMessageBox.warning(self, "Abrir Acta", "No se encontró el movimiento")
                return
            
            # Buscar archivos de acta
            archivo_pdf = movimiento_data.get('archivo_path_pdf', '')
            archivo_docx = movimiento_data.get('archivo_path_docx', '')
            
            # Si no hay archivo_path_pdf, intentar con archivo_path (compatibilidad)
            if not archivo_pdf:
                archivo_pdf = movimiento_data.get('archivo_path', '')
            
            # Verificar qué archivos existen
            pdf_existe = archivo_pdf and os.path.exists(archivo_pdf)
            docx_existe = archivo_docx and os.path.exists(archivo_docx)
            
            if not pdf_existe and not docx_existe:
                QMessageBox.information(self, "Abrir Acta", 
                                    "Este movimiento no tiene actas disponibles.")
                return
            
            # Si hay múltiples archivos, preguntar cuál abrir
            if pdf_existe and docx_existe:
                respuesta = QMessageBox.question(
                    self, 
                    "Seleccionar Acta",
                    "¿Qué acta deseas abrir?\n\n"
                    f"📄 PDF Firmado: {os.path.basename(archivo_pdf)}\n"
                    f"📝 DOCX Temporal: {os.path.basename(archivo_docx)}",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if respuesta == QMessageBox.Yes:
                    archivo_a_abrir = archivo_pdf
                else:
                    archivo_a_abrir = archivo_docx
                    
            elif pdf_existe:
                archivo_a_abrir = archivo_pdf
            else:
                archivo_a_abrir = archivo_docx
            
            # Abrir archivo con aplicación por defecto
            self.abrir_archivo_desde_ruta(archivo_a_abrir)
            
        except Exception as e:
            print(f"❌ Error abriendo acta: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo abrir el acta:\n{str(e)}")
            
    def _aplicar_ajustes_tabla_movimientos_optimizada(self):
        """Ajustes optimizados para tabla SIN columna Acciones - MÉTODO NUEVO"""
        try:
            print("🎯 Aplicando ajustes optimizados de tabla...")
            
            # 1. Ajustar automáticamente el tamaño primero
            self.tabla_movimientos.resizeColumnsToContents()
            
            # 2. Configurar header
            header = self.tabla_movimientos.horizontalHeader()
            
            # 3. Anchos fijos optimizados para columnas clave
            anchos_fijos = {
                "Tipo": 80,           # Ancho fijo para tipo
                "Fecha": 70,          # Ancho fijo para fecha corta
                "Nombre": 100,        # Ancho fijo para nombre
                "Apellido": 100,      # Ancho fijo para apellido  
                "Área": 120,          # Ancho fijo para área (puede ser más ancho)
                "Cantidad Bienes": 80, # Ancho fijo para cantidad
                "PRD": 80,            # Ancho fijo para PRD
                "Acta": 70            # Ancho fijo para acta
            }
            
            # 4. Aplicar anchos fijos columna por columna
            col_idx = 0
            for nombre_col, campo_bd in self.mapeo_columnas_movimientos:
                if not self.columnas_visibles_movimientos.get(nombre_col, False):
                    continue
                    
                if nombre_col in anchos_fijos:
                    # Columna con ancho fijo
                    header.setSectionResizeMode(col_idx, QHeaderView.Fixed)
                    self.tabla_movimientos.setColumnWidth(col_idx, anchos_fijos[nombre_col])
                    print(f"   📏 {nombre_col}: {anchos_fijos[nombre_col]}px (fijo)")
                else:
                    # Columna con tamaño interactivo
                    header.setSectionResizeMode(col_idx, QHeaderView.Interactive)
                    print(f"   📏 {nombre_col}: tamaño automático")
                
                col_idx += 1
                
            # 5. Permitir que la última columna se expanda si hay espacio
            header.setStretchLastSection(True)
            
            # 6. TOOLTIP PARA USUARIO - Muy importante!
            self.tabla_movimientos.setToolTip(
                "🖱️ Doble click en cualquier fila para ver detalles completos\n"
                "📄 Click en columna 'Acta' para abrir archivos directamente"
            )
            
            # 7. También agregar tooltip al header para mayor visibilidad
            header.setToolTip("Doble click en filas para detalles completos")
            
            print("✅ Ajustes de tabla aplicados correctamente")
            
        except Exception as e:
            print(f"❌ Error aplicando ajustes de tabla: {e}")
            # Fallback básico
            try:
                self.tabla_movimientos.resizeColumnsToContents()
                header = self.tabla_movimientos.horizontalHeader()
                header.setStretchLastSection(True)
            except:
                pass
            
