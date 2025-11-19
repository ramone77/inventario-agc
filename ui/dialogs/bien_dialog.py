"""
🎨 DIÁLOGO DE GESTIÓN DE BIENES - Sistema de Inventario AGC
Formulario completo para gestión de bienes - VERSIÓN MODULAR
"""

import os
import pandas as pd
from datetime import datetime

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QComboBox, QTextEdit, QPushButton,
                           QTabWidget, QWidget, QGroupBox, QMessageBox,
                           QFileDialog, QProgressBar, QRadioButton, QStatusBar,
                           QScrollArea, QCheckBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QRegExpValidator, QDoubleValidator, QIntValidator
from PyQt5.QtCore import QRegExp


class BienDialog(QDialog):
    """Diálogo mejorado para gestión de bienes - VERSIÓN MODULAR"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("🏢 Gestión de Bienes - Sistema de Inventario")
        self.setMinimumSize(1000, 750)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
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

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("SISTEMA DE GESTIÓN DE INVENTARIO")
        header.setStyleSheet("""
            QLabel {
                font-size: 18px;
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
        
        # Tabs principales
        self.tabs = QTabWidget()
        self._crear_tab_registro()
        self._crear_tab_importacion()
        self._crear_tab_exportacion()
        
        layout.addWidget(self.tabs)
        
        # Barra de estado
        self.status_bar = QStatusBar()
        self.actualizar_estadisticas()
        layout.addWidget(self.status_bar)

    def _crear_tab_registro(self):
        """Crea la pestaña de registro manual"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        
        # Grupo: Datos Básicos
        grupo_basico = QGroupBox("📦 DATOS BÁSICOS DEL BIEN")
        form_basico = QFormLayout(grupo_basico)
        
        # Fila 1 - Tipo y Ficha
        fila1 = QHBoxLayout()
        self.tipo = QComboBox()
        self.tipo.addItems(["", "Oficina", "Cocina", "Laboratorio", "Celular", "Tablet", "Otro"])
        self.tipo.setPlaceholderText("Seleccionar tipo...")
        
        self.ficha = QLineEdit()
        self.ficha.setPlaceholderText("Número de ficha...")
        self.ficha.setValidator(QRegExpValidator(QRegExp("[0-9]+")))
        
        fila1.addWidget(QLabel("Tipo:*"))
        fila1.addWidget(self.tipo)
        fila1.addWidget(QLabel("Ficha:*"))
        fila1.addWidget(self.ficha)
        form_basico.addRow(fila1)
        
        # Fila 2 - Marca y Modelo
        fila2 = QHBoxLayout()
        self.marca = QLineEdit()
        self.marca.setPlaceholderText("Marca del equipo...")
        
        self.modelo = QLineEdit()
        self.modelo.setPlaceholderText("Modelo específico...")
        
        fila2.addWidget(QLabel("Marca:*"))
        fila2.addWidget(self.marca)
        fila2.addWidget(QLabel("Modelo:*"))
        fila2.addWidget(self.modelo)
        form_basico.addRow(fila2)
        
        # Fila 3 - Serie y Estado
        fila3 = QHBoxLayout()
        self.serie = QLineEdit()
        self.serie.setPlaceholderText("Número de serie...")
        
        self.estado = QComboBox()
        self.estado.addItems(["En depósito", "Asignado", "En reparación", "Baja definitiva"])
        
        fila3.addWidget(QLabel("Serie:*"))
        fila3.addWidget(self.serie)
        fila3.addWidget(QLabel("Estado:*"))
        fila3.addWidget(self.estado)
        form_basico.addRow(fila3)
        
        layout.addWidget(grupo_basico)
        
        # Grupo: Datos Técnicos (condicional)
        self.grupo_tecnico = QGroupBox("📱 DATOS TÉCNICOS - EQUIPOS MÓVILES")
        form_tecnico = QFormLayout(self.grupo_tecnico)
        
        fila_tecnica = QHBoxLayout()
        self.linea = QLineEdit()
        self.linea.setPlaceholderText("Número de línea...")
        
        self.sim = QLineEdit()
        self.sim.setPlaceholderText("Número de SIM...")
        
        self.empresa = QComboBox()
        self.empresa.addItems(["", "Personal", "Claro", "Movistar", "Tuenti", "Otro"])
        
        self.imei = QLineEdit()
        self.imei.setPlaceholderText("IMEI (15 dígitos)...")
        self.imei.setValidator(QRegExpValidator(QRegExp("[0-9]{15}")))
        
        fila_tecnica.addWidget(QLabel("Línea:"))
        fila_tecnica.addWidget(self.linea)
        fila_tecnica.addWidget(QLabel("SIM:"))
        fila_tecnica.addWidget(self.sim)
        fila_tecnica.addWidget(QLabel("Empresa:"))
        fila_tecnica.addWidget(self.empresa)
        fila_tecnica.addWidget(QLabel("IMEI:"))
        fila_tecnica.addWidget(self.imei)
        form_tecnico.addRow(fila_tecnica)
        
        self.grupo_tecnico.setVisible(False)
        self.tipo.currentTextChanged.connect(self._actualizar_campos_tecnicos)
        layout.addWidget(self.grupo_tecnico)
        
        # Grupo: Información Patrimonial
        grupo_patrimonio = QGroupBox("🏛️ INFORMACIÓN PATRIMONIAL")
        form_patrimonio = QFormLayout(grupo_patrimonio)
        
        fila_patrimonio = QHBoxLayout()
        self.prd = QLineEdit()
        self.prd.setPlaceholderText("Ej: 1234-2023")
        
        self.anio_prd = QLineEdit()
        self.anio_prd.setPlaceholderText("Ej: 2023")
        self.anio_prd.setValidator(QIntValidator(2000, 2030))
        
        self.monto_original = QLineEdit()
        self.monto_original.setPlaceholderText("Ej: 150000.50")
        self.monto_original.setValidator(QDoubleValidator(0, 9999999, 2))
        
        fila_patrimonio.addWidget(QLabel("PRD:"))
        fila_patrimonio.addWidget(self.prd)
        fila_patrimonio.addWidget(QLabel("Año PRD:"))
        fila_patrimonio.addWidget(self.anio_prd)
        fila_patrimonio.addWidget(QLabel("Monto $:"))
        fila_patrimonio.addWidget(self.monto_original)
        form_patrimonio.addRow(fila_patrimonio)
        
        layout.addWidget(grupo_patrimonio)
        
        # Grupo: Responsable
        grupo_responsable = QGroupBox("👤 RESPONSABLE DEL BIEN")
        form_responsable = QFormLayout(grupo_responsable)
        
        fila_nombre = QHBoxLayout()
        self.nombre = QLineEdit()
        self.nombre.setPlaceholderText("Nombre...")
        
        self.apellido = QLineEdit()
        self.apellido.setPlaceholderText("Apellido...")
        
        fila_nombre.addWidget(QLabel("Nombre:"))
        fila_nombre.addWidget(self.nombre)
        fila_nombre.addWidget(QLabel("Apellido:"))
        fila_nombre.addWidget(self.apellido)
        form_responsable.addRow(fila_nombre)
        
        fila_institucional = QHBoxLayout()
        self.dni_cuit = QLineEdit()
        self.dni_cuit.setPlaceholderText("DNI o CUIT...")
        
        self.institucional = QComboBox()
        self.institucional.addItems([
            "", "AGENCIA GUBERNAMENTAL DE CONTROL", "UNIDAD OPERATIVA PLANIFICACION Y COORDINACION DE GESTION",
            "DIRECCION EJECUTIVA", "GERENCIA OPERATIVA ESTRATEGIA COMUNICACIONAL", 
            "DIRECCION GENERAL HABILITACIONES Y PERMISOS", "DIRECCION GENERAL DE FISCALIZACION Y CONTROL",
            "DIRECCION GENERAL FISCALIZACION Y CONTROL DE OBRAS", "DIRECCION GENERAL HIGIENE Y SEGURIDAD ALIMENTARIA",
            "DIRECCION GENERAL LEGAL Y TECNICA", "UNIDAD DE AUDITORIA INTERNA",
            "UNION OPERATIVA DE FISCALIZACION INTEGRAL", "UNIDAD DE COORDINACION ADMINISTRATIVA"
        ])
        
        fila_institucional.addWidget(QLabel("DNI/CUIT:"))
        fila_institucional.addWidget(self.dni_cuit)
        fila_institucional.addWidget(QLabel("Institucional:"))
        fila_institucional.addWidget(self.institucional)
        form_responsable.addRow(fila_institucional)
        
        layout.addWidget(grupo_responsable)
        
        # Grupo: Descripción
        grupo_descripcion = QGroupBox("📄 DESCRIPCIÓN Y OBSERVACIONES")
        layout_descripcion = QVBoxLayout(grupo_descripcion)
        self.descripcion = QTextEdit()
        self.descripcion.setPlaceholderText("Descripción detallada del bien, características, observaciones...")
        self.descripcion.setMaximumHeight(100)
        layout_descripcion.addWidget(self.descripcion)
        layout.addWidget(grupo_descripcion)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        self.btn_guardar = QPushButton("💾 GUARDAR BIEN")
        self.btn_guardar.clicked.connect(self.guardar)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        
        self.btn_limpiar = QPushButton("🧹 LIMPIAR FORMULARIO")
        self.btn_limpiar.clicked.connect(self.limpiar_formulario)
        self.btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }
        """)
        
        btn_layout.addWidget(self.btn_guardar)
        btn_layout.addWidget(self.btn_limpiar)
        layout.addLayout(btn_layout)
        
        scroll.setWidget(content)
        tab_layout = QVBoxLayout(tab)
        tab_layout.addWidget(scroll)
        
        self.tabs.addTab(tab, "📝 Nuevo Bien")

    def _crear_tab_importacion(self):
        """Crea la pestaña de importación masiva"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grupo = QGroupBox("📥 IMPORTACIÓN MASIVA DESDE EXCEL")
        form_layout = QFormLayout(grupo)
        
        # Información
        info_text = QLabel("""
        <html>
        <b>Instrucciones para importación:</b><br>
        • Seleccioná un archivo Excel con los datos de los bienes<br>
        • Las columnas deben incluir: <i>ficha, tipo, marca, modelo, serie</i><br>
        • Podés descargar una plantilla para ver el formato requerido<br>
        • Los registros duplicados serán ignorados automáticamente
        </html>
        """)
        info_text.setWordWrap(True)
        info_text.setStyleSheet("background-color: #e8f4fd; padding: 15px; border-radius: 5px;")
        form_layout.addRow(info_text)
        
        # Botones de importación
        btn_layout = QHBoxLayout()
        self.btn_importar = QPushButton("📂 SELECCIONAR ARCHIVO EXCEL")
        self.btn_importar.clicked.connect(self.importar_bienes)
        self.btn_importar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        
        self.btn_plantilla = QPushButton("📋 DESCARGAR PLANTILLA")
        self.btn_plantilla.clicked.connect(self.descargar_plantilla)
        self.btn_plantilla.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        
        btn_layout.addWidget(self.btn_importar)
        btn_layout.addWidget(self.btn_plantilla)
        form_layout.addRow(btn_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        form_layout.addRow("Progreso:", self.progress_bar)
        
        # Área de log
        self.log_area = QTextEdit()
        self.log_area.setPlaceholderText("Los resultados de la importación aparecerán aquí...")
        self.log_area.setMaximumHeight(200)
        form_layout.addRow("Resultados:", self.log_area)
        
        layout.addWidget(grupo)
        layout.addStretch()
        
        self.tabs.addTab(tab, "📥 Importar Excel")

    def _crear_tab_exportacion(self):
        """Crea la pestaña de exportación"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grupo = QGroupBox("📤 EXPORTACIÓN DE DATOS")
        form_layout = QFormLayout(grupo)
        
        # Opciones de exportación
        self.radio_todos = QRadioButton("Exportar TODOS los bienes")
        self.radio_filtrados = QRadioButton("Exportar bienes filtrados (desde búsqueda)")
        self.radio_todos.setChecked(True)
        
        radio_layout = QVBoxLayout()
        radio_layout.addWidget(self.radio_todos)
        radio_layout.addWidget(self.radio_filtrados)
        form_layout.addRow("Alcance de exportación:", radio_layout)
        
        # Botones de exportación
        btn_layout = QHBoxLayout()
        self.btn_exportar_excel = QPushButton("💾 EXPORTAR A EXCEL")
        self.btn_exportar_excel.clicked.connect(self.exportar_bienes)
        self.btn_exportar_excel.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
        """)
        
        btn_layout.addWidget(self.btn_exportar_excel)
        form_layout.addRow(btn_layout)
        
        # Estadísticas
        self.label_stats = QLabel("Calculando estadísticas...")
        self.label_stats.setStyleSheet("font-weight: bold; color: #2c3e50; padding: 10px;")
        form_layout.addRow("Estadísticas del sistema:", self.label_stats)
        
        layout.addWidget(grupo)
        layout.addStretch()
        
        self.tabs.addTab(tab, "📤 Exportar Datos")

    def _actualizar_campos_tecnicos(self):
        """Muestra/oculta campos técnicos según tipo de bien"""
        es_movil = self.tipo.currentText() in ["Celular", "Tablet"]
        self.grupo_tecnico.setVisible(es_movil)

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas en la barra de estado"""
        try:
            stats = self.db.get_estadisticas()
            self.status_bar.showMessage(
                f"Total de bienes: {stats['total']} | "
                f"En depósito: {stats['por_estado'].get('En depósito', 0)} | "
                f"Asignados: {stats['por_estado'].get('Asignado', 0)}"
            )
            self.label_stats.setText(
                f"Total de bienes: {stats['total']}\n"
                f"En depósito: {stats['por_estado'].get('En depósito', 0)}\n"
                f"Asignados: {stats['por_estado'].get('Asignado', 0)}\n"
                f"Bajas: {stats['por_estado'].get('Baja definitiva', 0)}"
            )
        except Exception as e:
            self.status_bar.showMessage("Error calculando estadísticas")

    def guardar(self):
        """Guarda un nuevo bien en la base de datos"""
        # Validaciones básicas
        if not all([self.tipo.currentText(), self.ficha.text(), self.marca.text(), self.modelo.text()]):
            QMessageBox.warning(self, "Campos requeridos", 
                            "Completá al menos: Tipo, Ficha, Marca y Modelo")
            return
        
        # Preparar datos
        bien_data = {
            "ficha": self.ficha.text().strip(),
            "tipo": self.tipo.currentText(),
            "marca": self.marca.text().strip(),
            "modelo": self.modelo.text().strip(),
            "serie": self.serie.text().strip(),
            "linea": self.linea.text().strip(),
            "sim": self.sim.text().strip(),
            "empresa": self.empresa.currentText(),
            "imei": self.imei.text().strip(),
            "nombre": self.nombre.text().strip(),
            "apellido": self.apellido.text().strip(),
            "dni_cuit": self.dni_cuit.text().strip(),
            "institucional": self.institucional.currentText(),
            "descripcion": self.descripcion.toPlainText().strip(),
            "estado": self.estado.currentText(),
            "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "monto_original": self.monto_original.text().strip(),
            "prd": self.prd.text().strip(),
            "anio_prd": self.anio_prd.text().strip()
        }
        
            # Verificar si ya existe - VERSIÓN MEJORADA CON IMEI
# Verificar si ya existe - VERSIÓN MEJORADA CON IMEI
        if self.db.bien_existe(bien_data["ficha"], bien_data["tipo"], 
                            bien_data["marca"], bien_data["modelo"], 
                            bien_data["serie"], bien_data["imei"]):
            QMessageBox.warning(self, "Duplicado", 
                            f"Ya existe un bien con:\n"
                            f"• Ficha: {bien_data['ficha']}\n"
                            f"• Tipo: {bien_data['tipo']}\n" 
                            f"• Marca: {bien_data['marca']}\n"
                            f"• Modelo: {bien_data['modelo']}\n"
                            f"• Serie: {bien_data['serie']}\n"
                            f"• IMEI: {bien_data['imei']}")
            return
        
        # Guardar en base de datos
        if self.db.add_bien(bien_data):
            QMessageBox.information(self, "Éxito", "Bien guardado correctamente")
            self.limpiar_formulario()
            self.actualizar_estadisticas()
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar el bien")

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.ficha.clear()
        self.marca.clear()
        self.modelo.clear()
        self.serie.clear()
        self.linea.clear()
        self.sim.clear()
        self.imei.clear()
        self.nombre.clear()
        self.apellido.clear()
        self.dni_cuit.clear()
        self.descripcion.clear()
        self.prd.clear()
        self.anio_prd.clear()
        self.monto_original.clear()
        self.tipo.setCurrentIndex(0)
        self.empresa.setCurrentIndex(0)
        self.institucional.setCurrentIndex(0)
        self.estado.setCurrentIndex(0)

    def descargar_plantilla(self):
        """Descarga una plantilla Excel para importación"""
        try:
            # Crear datos de ejemplo
            datos = {
                'ficha': ['1001', '1002', '1003'],
                'tipo': ['Oficina', 'Celular', 'Tablet'],
                'marca': ['Ejemplo', 'Ejemplo', 'Ejemplo'],
                'modelo': ['Modelo A', 'Modelo B', 'Modelo C'],
                'serie': ['SN001', 'SN002', 'SN003'],
                'estado': ['En depósito', 'Asignado', 'En depósito'],
                'nombre': ['Juan', 'María', 'Carlos'],
                'apellido': ['Pérez', 'Gómez', 'López'],
                'dni_cuit': ['20123456789', '27123456789', '23123456789'],
                'institucional': ['DIRECCION EJECUTIVA', 'AGENCIA GUBERNAMENTAL DE CONTROL', 'UNIDAD OPERATIVA'],
                'descripcion': ['Equipo oficina', 'Celular corporativo', 'Tablet inspecciones'],
                'prd': ['1234-2023', '1234-2023', '1234-2023'],
                'anio_prd': ['2023', '2023', '2023'],
                'monto_original': ['150000.50', '80000.00', '120000.00'],
                'linea': ['', '1112345678', ''],
                'sim': ['', 'SIM001', ''],
                'empresa': ['', 'Personal', ''],
                'imei': ['', '123456789012345', '']
            }
            
            df = pd.DataFrame(datos)
            ruta, _ = QFileDialog.getSaveFileName(
                self, "Guardar plantilla", 
                f"plantilla_importacion_{datetime.now().strftime('%Y%m%d')}.xlsx",
                "Excel (*.xlsx)"
            )
            
            if ruta:
                df.to_excel(ruta, index=False)
                QMessageBox.information(self, "Plantilla descargada", 
                                      f"Plantilla guardada en:\n{ruta}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear la plantilla:\n{e}")
            
    def _campo_valido(self, valor):
        """Verifica si un campo tiene contenido real después de limpiar"""
        if valor is None:
            return False
        try:
            # Manejar pandas NaN y otros valores especiales
            if hasattr(valor, 'dtype') and pd.isna(valor):
                return False
        except:
            pass
        
        valor_str = str(valor).strip()
        return bool(valor_str) and valor_str.lower() not in ['', 'nan', 'none', 'null', 'nat']

    def importar_bienes(self):
        """Importa bienes desde archivo Excel"""
        ruta, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo Excel", "", "Excel (*.xlsx *.xls)"
        )
        
        if not ruta:
            return
            
        try:
            self.progress_bar.setVisible(True)
            self.log_area.clear()
            
            # Leer Excel
            df = pd.read_excel(ruta).fillna("")
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
            
            # Validar estructura
            columnas_requeridas = {"ficha", "tipo", "marca", "modelo", "serie"}
            if not columnas_requeridas.issubset(set(df.columns)):
                QMessageBox.warning(self, "Formato incorrecto", 
                                f"Faltan columnas requeridas: {columnas_requeridas}")
                return
            
            # Procesar filas
            importados = 0
            errores = []
            
            self.progress_bar.setRange(0, len(df))
            self.progress_bar.setValue(0)

            for i, fila in df.iterrows():
                try:
                    # Validación de duplicados
                    ficha = str(fila.get("ficha", "")).strip()
                    tipo = str(fila.get("tipo", "")).strip() 
                    marca = str(fila.get("marca", "")).strip()
                    modelo = str(fila.get("modelo", "")).strip()
                    serie = str(fila.get("serie", "")).strip()
                    imei = str(fila.get("imei", "")).strip()
        
                    # DEBUG TEMPORAL - ver los datos reales
                    print(f"DEBUG Fila {i+2}: Ficha='{ficha}' Tipo='{tipo}' Marca='{marca}' Modelo='{modelo}'")

                    # Validar campos requeridos - VERSIÓN FLEXIBLE CORREGIDA
                    # Ficha y Tipo son obligatorios, Marca y Modelo pueden estar vacíos
                    campos_faltantes = []
                    if not self._campo_valido(ficha): campos_faltantes.append("ficha")
                    if not self._campo_valido(tipo): campos_faltantes.append("tipo")

                    if campos_faltantes:
                        raise ValueError(f"Campos requeridos vacíos: {', '.join(campos_faltantes)}")

                    # Marca y modelo son opcionales - si están vacíos, usar valores por defecto
                    if not self._campo_valido(marca):
                        marca = "SIN MARCA"
                    if not self._campo_valido(modelo):
                        modelo = "SIN MODELO"

                    # Marca y modelo son opcionales - si están vacíos, usar valores por defecto
                    if not self._campo_valido(marca):
                        marca = "SIN MARCA"
                    if not self._campo_valido(modelo):
                        modelo = "SIN MODELO"
                        
                        raise ValueError(f"Campos requeridos vacíos: {', '.join(campos_faltantes)}")
                    
                    # ✅ VERIFICACIÓN MEJORADA - incluye marca, modelo e IMEI
                    if self.db.bien_existe(ficha, tipo, marca, modelo, serie, imei):
                        raise ValueError(f"Ya existe:\n• Ficha: {ficha}\n• Tipo: {tipo}\n• Marca: {marca}\n• Modelo: {modelo}\n• Serie: '{serie}'\n• IMEI: '{imei}'")
                    
                    # Preparar datos
                    bien_data = {
                        "ficha": str(fila.get("ficha", "")),
                        "tipo": str(fila.get("tipo", "")),
                        "marca": str(fila.get("marca", "")),
                        "modelo": str(fila.get("modelo", "")),
                        "serie": str(fila.get("serie", "")),
                        "linea": str(fila.get("linea", "")),
                        "sim": str(fila.get("sim", "")),
                        "empresa": str(fila.get("empresa", "")),
                        "imei": str(fila.get("imei", "")),
                        "nombre": str(fila.get("nombre", "")),
                        "apellido": str(fila.get("apellido", "")),
                        "dni_cuit": str(fila.get("dni_cuit", "")),
                        "institucional": str(fila.get("institucional", "")),
                        "descripcion": str(fila.get("descripcion", "")),
                        "estado": str(fila.get("estado", "En depósito")),
                        "fecha_registro": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "monto_original": str(fila.get("monto_original", "")),
                        "prd": str(fila.get("prd", "")),
                        "anio_prd": str(fila.get("anio_prd", ""))
                    }
                            
                    # Guardar
                    if self.db.add_bien(bien_data):
                        importados += 1
                    else:
                        raise ValueError("Error al guardar")
                    
                    self.progress_bar.setValue(i + 1)
                        
                except Exception as e:
                    errores.append(f"Fila {i+2}: {str(e)}")
                
            self.progress_bar.setVisible(False)                
            
            # Mostrar resultados
            self.log_area.append(f"✅ IMPORTACIÓN COMPLETADA\n")
            self.log_area.append(f"📊 Registros importados: {importados}")
            self.log_area.append(f"❌ Errores: {len(errores)}")
            
            if errores:
                self.log_area.append("\n🔍 DETALLE DE ERRORES:")
                for error in errores[:10]:
                    self.log_area.append(f"   • {error}")
                if len(errores) > 10:
                    self.log_area.append(f"   ... y {len(errores) - 10} errores más")
            
            QMessageBox.information(self, "Importación finalizada", 
                                f"Se importaron {importados} registros de {len(df)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo importar el archivo:\n{e}")
        finally:
            self.progress_bar.setVisible(False)
            self.actualizar_estadisticas()

    def exportar_bienes(self):
        """Exporta bienes a archivo Excel"""
        try:
            # Obtener datos según selección
            if self.radio_todos.isChecked():
                bienes = self.db.list_bienes()
            else:
                # Por ahora exporta todos, luego implementaremos filtrados
                bienes = self.db.list_bienes()
            
            if not bienes:
                QMessageBox.information(self, "Sin datos", "No hay bienes para exportar")
                return
            
            # Preparar datos
            datos = []
            for bien in bienes:
                datos.append({
                    "ficha": self._safe_get(bien, "ficha"),
                    "tipo": self._safe_get(bien, "tipo"),
                    "marca": self._safe_get(bien, "marca"),
                    "modelo": self._safe_get(bien, "modelo"),
                    "serie": self._safe_get(bien, "serie"),
                    "imei": self._safe_get(bien, "imei"),
                    "linea": self._safe_get(bien, "linea"),
                    "sim": self._safe_get(bien, "sim"),
                    "empresa": self._safe_get(bien, "empresa"),
                    "nombre": self._safe_get(bien, "nombre"),
                    "apellido": self._safe_get(bien, "apellido"),
                    "dni_cuit": self._safe_get(bien, "dni_cuit"),
                    "institucional": self._safe_get(bien, "institucional"),
                    "descripcion": self._safe_get(bien, "descripcion"),
                    "estado": self._safe_get(bien, "estado"),
                    "fecha_registro": self._safe_get(bien, "fecha_registro"),
                    "monto_original": self._safe_get(bien, "monto_original"),
                    "prd": self._safe_get(bien, "prd"),
                    "anio_prd": self._safe_get(bien, "anio_prd")
                })
            
            # Exportar
            df = pd.DataFrame(datos)
            ruta, _ = QFileDialog.getSaveFileName(
                self, "Guardar archivo Excel",
                f"inventario_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                "Excel (*.xlsx)"
            )
            
            if ruta:
                df.to_excel(ruta, index=False)
                QMessageBox.information(self, "Exportación exitosa", 
                                      f"Se exportaron {len(datos)} registros")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{e}")

    def _safe_get(self, bien, campo):
        """Obtiene valores de forma segura"""
        try:
            valor = bien[campo]
            return str(valor) if valor is not None else ""
        except (KeyError, IndexError):
            return ""