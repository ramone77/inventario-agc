"""
🎨 DIÁLOGO DE GESTIÓN DE MOVIMIENTOS - Sistema de Inventario AGC
Formulario completo para gestión de movimientos - VERSIÓN MODULAR
"""

import os
import shutil
from datetime import datetime

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QComboBox, QTextEdit, QPushButton,
                           QGroupBox, QMessageBox, QFileDialog, QListWidget, 
                           QListWidgetItem, QDialogButtonBox, QCalendarWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator


class MovimientoDialog(QDialog):
    """Diálogo mejorado para gestión de movimientos - VERSIÓN MODULAR"""
    
    
    def __init__(self, db, usuario_actual, parent=None):
        super().__init__(parent)
        self.db = db
        self.usuario_actual = usuario_actual
        self.archivo_path = ""
        self.setWindowTitle("🔄 Gestión de Movimientos")
        self.setMinimumSize(900, 700)        
        self._setup_ui()
        # ✅ CONECTAR CAMBIO DE TIPO DE MOVIMIENTO
        self.tipo.currentTextChanged.connect(self._actualizar_visibilidad_boton)
        # Actualizar visibilidad inicial
        self._actualizar_visibilidad_boton()
        self.aplicar_filtros()



    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # ===== DATOS DEL MOVIMIENTO =====
        grupo_movimiento = QGroupBox("📋 DATOS DEL MOVIMIENTO")
        form_movimiento = QFormLayout(grupo_movimiento)
        
        # Tipo y número de transferencia
        fila_tipo = QHBoxLayout()
        self.tipo = QComboBox()
        self.tipo.addItems(["Entrega", "Devolución", "Baja", "Transferencia", "Compra"])
        
        self.numero_transferencia = QLineEdit()
        self.numero_transferencia.setPlaceholderText("Número de transferencia (opcional)")
        
        fila_tipo.addWidget(QLabel("Tipo:*"))
        fila_tipo.addWidget(self.tipo)
        fila_tipo.addWidget(QLabel("N° Transferencia:"))
        fila_tipo.addWidget(self.numero_transferencia)
        form_movimiento.addRow(fila_tipo)
        
        # FECHA DE ENTREGA
        fila_fecha = QHBoxLayout()
        self.fecha_entrega = QLineEdit()
        self.fecha_entrega.setText(datetime.now().strftime("%d/%m/%Y"))
        self.fecha_entrega.setPlaceholderText("DD/MM/AAAA")
        
        self.btn_calendario = QPushButton("📅")
        self.btn_calendario.setFixedWidth(40)
        self.btn_calendario.clicked.connect(self.mostrar_calendario)
        
        fila_fecha.addWidget(QLabel("Fecha de Entrega:*"))
        fila_fecha.addWidget(self.fecha_entrega)
        fila_fecha.addWidget(self.btn_calendario)
        form_movimiento.addRow(fila_fecha)
        
        layout.addWidget(grupo_movimiento)
        
        # ===== DATOS DEL RESPONSABLE =====
        grupo_responsable = QGroupBox("👤 DATOS DEL RESPONSABLE")
        form_responsable = QFormLayout(grupo_responsable)
        
        # Nombre y apellido
        fila_nombre = QHBoxLayout()
        self.responsable_nombre = QLineEdit()
        self.responsable_nombre.setPlaceholderText("Nombre...")
        
        self.responsable_apellido = QLineEdit()
        self.responsable_apellido.setPlaceholderText("Apellido...")
        
        fila_nombre.addWidget(QLabel("Nombre:*"))
        fila_nombre.addWidget(self.responsable_nombre)
        fila_nombre.addWidget(QLabel("Apellido:*"))
        fila_nombre.addWidget(self.responsable_apellido)
        form_responsable.addRow(fila_nombre)
        
        # CUIT e institucional
        fila_institucional = QHBoxLayout()
        self.responsable_cuit = QLineEdit()
        self.responsable_cuit.setPlaceholderText("CUIT/DNI...")
        
        self.responsable_institucional = QComboBox()
        self.responsable_institucional.addItems([
            "", "AGENCIA GUBERNAMENTAL DE CONTROL", "UNIDAD OPERATIVA PLANIFICACION Y COORDINACION DE GESTION",
            "DIRECCION EJECUTIVA", "GERENCIA OPERATIVA ESTRATEGIA COMUNICACIONAL",
            "DIRECCION GENERAL HABILITACIONES Y PERMISOS", "DIRECCION GENERAL DE FISCALIZACION Y CONTROL",
            "DIRECCION GENERAL FISCALIZACION Y CONTROL DE OBRAS", "DIRECCION GENERAL HIGIENE Y SEGURIDAD ALIMENTARIA",
            "DIRECCION GENERAL LEGAL Y TECNICA", "UNIDAD DE AUDITORIA INTERNA",
            "UNION OPERATIVA DE FISCALIZACION INTEGRAL", "UNIDAD DE COORDINACION ADMINISTRATIVA"
        ])
        
        fila_institucional.addWidget(QLabel("CUIT/DNI:"))
        fila_institucional.addWidget(self.responsable_cuit)
        fila_institucional.addWidget(QLabel("Institucional:*"))
        fila_institucional.addWidget(self.responsable_institucional)
        form_responsable.addRow(fila_institucional)
        
        # ✅ NUEVO BOTÓN - SOLO PARA DEVOLUCIÓN (DENTRO del grupo)
        self.btn_cargar_datos = QPushButton("📥 Cargar datos del bien seleccionado")
        self.btn_cargar_datos.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.btn_cargar_datos.clicked.connect(self._cargar_datos_bien)
        self.btn_cargar_datos.setVisible(False)  # Oculto por defecto
        self.btn_cargar_datos.setToolTip("Carga automáticamente los datos del responsable del bien seleccionado")

        # Agregar al formulario del grupo responsable
        form_responsable.addRow(self.btn_cargar_datos)

        # FINALMENTE agregar el grupo al layout principal
        layout.addWidget(grupo_responsable)
        
        # ===== FILTROS PARA BIENES =====
        grupo_filtros = QGroupBox("🔍 FILTROS PARA SELECCIÓN DE BIENES")
        form_filtros = QFormLayout(grupo_filtros)
        
        # Filtro por PRD
        self.filtro_prd = QLineEdit()
        self.filtro_prd.setPlaceholderText("Filtrar por PRD...")
        self.filtro_prd.textChanged.connect(self.aplicar_filtros)
        
        # Rango de fichas
        fila_fichas = QHBoxLayout()
        self.filtro_ficha_desde = QLineEdit()
        self.filtro_ficha_desde.setPlaceholderText("Desde")
        self.filtro_ficha_desde.textChanged.connect(self.aplicar_filtros)
        
        self.filtro_ficha_hasta = QLineEdit()
        self.filtro_ficha_hasta.setPlaceholderText("Hasta")
        self.filtro_ficha_hasta.textChanged.connect(self.aplicar_filtros)
        
        fila_fichas.addWidget(self.filtro_ficha_desde)
        fila_fichas.addWidget(QLabel("a"))
        fila_fichas.addWidget(self.filtro_ficha_hasta)
        
        # Filtros por tipo y estado
        fila_filtros = QHBoxLayout()
        self.filtro_tipo = QComboBox()
        self.filtro_tipo.addItem("Todos los tipos")
        self.filtro_tipo.addItems(["Oficina", "Cocina", "Laboratorio", "Celular", "Tablet", "Otro"])
        self.filtro_tipo.currentTextChanged.connect(self.aplicar_filtros)
        
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItem("Todos los estados")
        self.filtro_estado.addItems(["En depósito", "Asignado", "Baja definitiva"])
        self.filtro_estado.currentTextChanged.connect(self.aplicar_filtros)
        
        fila_filtros.addWidget(QLabel("Tipo:"))
        fila_filtros.addWidget(self.filtro_tipo)
        fila_filtros.addWidget(QLabel("Estado:"))
        fila_filtros.addWidget(self.filtro_estado)
        
        # Botones de filtros
        btn_filtros = QHBoxLayout()
        self.btn_limpiar_filtros = QPushButton("🧹 Limpiar Filtros")
        self.btn_limpiar_filtros.clicked.connect(self.limpiar_filtros)
        
        self.btn_actualizar = QPushButton("🔄 Actualizar")
        self.btn_actualizar.clicked.connect(self.aplicar_filtros)
        
        btn_filtros.addWidget(self.btn_limpiar_filtros)
        btn_filtros.addWidget(self.btn_actualizar)
        
        form_filtros.addRow("PRD:", self.filtro_prd)
        form_filtros.addRow("Rango de fichas:", fila_fichas)
        form_filtros.addRow(fila_filtros)
        form_filtros.addRow(btn_filtros)
        
        layout.addWidget(grupo_filtros)
        
        # ===== LISTA DE BIENES =====
        grupo_bienes = QGroupBox("📦 BIENES INVOLUCRADOS")
        layout_bienes = QVBoxLayout(grupo_bienes)
        
        # Contador de selección
        self.contador_seleccion = QLabel("0 bienes seleccionados")
        self.contador_seleccion.setStyleSheet("font-weight: bold; color: #2E86AB; font-size: 12px;")
        layout_bienes.addWidget(self.contador_seleccion)
        
        # Lista de bienes
        self.lista_bienes = QListWidget()
        self.lista_bienes.setSelectionMode(QListWidget.MultiSelection)
        self.lista_bienes.itemSelectionChanged.connect(self.actualizar_contador)
        layout_bienes.addWidget(self.lista_bienes)
        
        layout.addWidget(grupo_bienes)
        
        # ===== OBSERVACIONES Y PDF =====
        grupo_adicional = QGroupBox("📝 INFORMACIÓN ADICIONAL")
        form_adicional = QFormLayout(grupo_adicional)
        
        self.observaciones = QTextEdit()
        self.observaciones.setPlaceholderText("Observaciones del movimiento...")
        self.observaciones.setMaximumHeight(80)
        
        # PDF
        pdf_layout = QHBoxLayout()
        self.btn_pdf = QPushButton("📎 Seleccionar PDF del acta")
        self.btn_pdf.clicked.connect(self.seleccionar_pdf)
        self.label_pdf = QLabel("No se seleccionó archivo PDF")
        self.label_pdf.setStyleSheet("color: #666; font-style: italic;")
        
        pdf_layout.addWidget(self.btn_pdf)
        pdf_layout.addWidget(self.label_pdf)
        pdf_layout.addStretch()
        
        form_adicional.addRow("Observaciones:", self.observaciones)
        form_adicional.addRow(pdf_layout)
        
        layout.addWidget(grupo_adicional)
        
        # ===== BOTONES FINALES =====
        botones_layout = QHBoxLayout()
        self.botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.botones.accepted.connect(self.guardar)
        self.botones.rejected.connect(self.reject)
        
        botones_layout.addStretch()
        botones_layout.addWidget(self.botones)
        layout.addLayout(botones_layout)

    def mostrar_calendario(self):
        """Muestra un calendario para seleccionar fecha"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📅 Seleccionar Fecha de Entrega")
        dialog.setFixedSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        calendario = QCalendarWidget()
        layout.addWidget(calendario)
        
        btn_layout = QHBoxLayout()
        btn_aceptar = QPushButton("✅ Seleccionar")
        btn_aceptar.clicked.connect(lambda: self.seleccionar_fecha_calendario(calendario, dialog))
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(btn_aceptar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
        
        dialog.exec_()

    def seleccionar_fecha_calendario(self, calendario, dialog):
        """Selecciona la fecha del calendario"""
        fecha = calendario.selectedDate()
        self.fecha_entrega.setText(fecha.toString("dd/MM/yyyy"))
        dialog.accept()

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.filtro_prd.clear()
        self.filtro_ficha_desde.clear()
        self.filtro_ficha_hasta.clear()
        self.filtro_tipo.setCurrentIndex(0)
        self.filtro_estado.setCurrentIndex(0)
        self.aplicar_filtros()

    def actualizar_contador(self):
        """Actualiza el contador de bienes seleccionados"""
        seleccionados = len(self.lista_bienes.selectedItems())
        self.contador_seleccion.setText(f"{seleccionados} bienes seleccionados")

    def seleccionar_pdf(self):
        """Selecciona y copia el PDF del acta"""
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar PDF", "", "PDF (*.pdf)")
        if path:
            nombre = f"{self.tipo.currentText()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            destino = os.path.join(self.db.actas_folder, nombre)
            shutil.copy(path, destino)
            self.archivo_path = destino  # ✅ Usando la variable que ahora existe
            self.label_pdf.setText(f"📄 {os.path.basename(destino)}")
            self.label_pdf.setStyleSheet("color: #27ae60; font-weight: bold;")
            QMessageBox.information(self, "PDF copiado", f"Archivo guardado en:\n{destino}")

    def aplicar_filtros(self):
        """Aplica los filtros a la lista de bienes"""
        self.lista_bienes.clear()
        
        # Obtener valores de filtros
        prd = self.filtro_prd.text().strip().lower()
        ficha_desde = self.filtro_ficha_desde.text().strip()
        ficha_hasta = self.filtro_ficha_hasta.text().strip()
        tipo_filtro = self.filtro_tipo.currentText()
        estado_filtro = self.filtro_estado.currentText()
        
        # Convertir filtros de ficha a número
        try:
            desde_num = int(ficha_desde) if ficha_desde else None
        except ValueError:
            desde_num = None

        try:
            hasta_num = int(ficha_hasta) if ficha_hasta else None
        except ValueError:
            hasta_num = None

        # Aplicar filtros
        for bien in self.db.list_bienes():
            ficha_raw = str(bien["ficha"]).strip()
            tipo_bien = str(bien["tipo"]).strip()
            prd_bien = str(bien["prd"]).strip().lower()
            estado_bien = str(bien["estado"]).strip()

            # Convertir ficha a número
            try:
                ficha_num = int(ficha_raw)
            except ValueError:
                ficha_num = None

            # Aplicar filtros acumulativos
            if prd and prd not in prd_bien:
                continue
            if desde_num is not None and (ficha_num is None or ficha_num < desde_num):
                continue
            if hasta_num is not None and (ficha_num is None or ficha_num > hasta_num):
                continue
            if tipo_filtro != "Todos los tipos" and tipo_filtro != tipo_bien:
                continue
            if estado_filtro != "Todos los estados" and estado_filtro != estado_bien:
                continue

            # Agregar a la lista
            item_text = f"Ficha: {bien['ficha']} | {bien['tipo']} | {bien['marca']} {bien['modelo']} | PRD: {bien['prd']} | Estado: {bien['estado']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, bien["id"])
            self.lista_bienes.addItem(item)
        
        self.actualizar_contador()

    def _actualizar_visibilidad_boton(self):
        """Muestra/oculta el botón según el tipo de movimiento"""
        es_devolucion = (self.tipo.currentText() == "Devolución")
        self.btn_cargar_datos.setVisible(es_devolucion)

    def _cargar_datos_bien(self):
        """Carga los datos del responsable del bien seleccionado"""
        try:
            items_seleccionados = self.lista_bienes.selectedItems()
            if not items_seleccionados:
                QMessageBox.warning(self, "Selección requerida", "Selecciona un bien primero")
                return
            
            # Tomar el primer bien seleccionado
            item = items_seleccionados[0]
            bien_id = item.data(Qt.UserRole)
            
            # Obtener datos completos del bien
            bien = self.db.obtener_bien_por_id(bien_id)
            if not bien:
                QMessageBox.warning(self, "Error", "No se pudieron obtener los datos del bien")
                return
            
            # ✅ CARGAR DATOS EN LOS CAMPOS
            self.responsable_nombre.setText(bien.get('nombre', ''))
            self.responsable_apellido.setText(bien.get('apellido', ''))
            self.responsable_cuit.setText(bien.get('dni_cuit', ''))
            
            # Buscar y seleccionar institucional en el combo
            institucional_bien = bien.get('institucional', '')
            if institucional_bien:
                index = self.responsable_institucional.findText(institucional_bien)
                if index >= 0:
                    self.responsable_institucional.setCurrentIndex(index)
                else:
                    # Si no existe, agregarlo
                    self.responsable_institucional.addItem(institucional_bien)
                    self.responsable_institucional.setCurrentText(institucional_bien)
            
            QMessageBox.information(self, "✅ Éxito", "Datos del bien cargados correctamente")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error cargando datos:\n{str(e)}")
    
    def guardar(self):
        """Guarda el movimiento - VERSIÓN CORREGIDA CON DATOS COMPLETOS"""
        # Validaciones
        bienes_ids = [item.data(Qt.UserRole) for item in self.lista_bienes.selectedItems()]
        if not bienes_ids:
            QMessageBox.warning(self, "Selección requerida", "Seleccioná al menos un bien.")
            return
        
        if not all([self.responsable_nombre.text(), self.responsable_apellido.text(), self.responsable_institucional.currentText()]):
            QMessageBox.warning(self, "Datos incompletos", "Completa nombre, apellido e institucional del responsable.")
            return
        
        # Validar fecha
        try:
            fecha_str = self.fecha_entrega.text().strip()
            fecha_dt = datetime.strptime(fecha_str, "%d/%m/%Y")
            fecha_bd = fecha_dt.strftime("%Y-%m-%d")
        except ValueError:
            QMessageBox.warning(self, "Fecha inválida", "La fecha de entrega debe tener formato DD/MM/AAAA (ej: 25/12/2024)")
            return
        
        # Preparar datos del movimiento
        responsable_completo = f"{self.responsable_nombre.text()} {self.responsable_apellido.text()}"
        
        mov_data = {
            "tipo": self.tipo.currentText(),
            "fecha": fecha_bd,
            "responsable": responsable_completo,
            "responsable_nombre": self.responsable_nombre.text().strip(),
            "responsable_apellido": self.responsable_apellido.text().strip(),
            "responsable_dni_cuit": self.responsable_cuit.text().strip(),
            "responsable_institucional": self.responsable_institucional.currentText(),
            "observaciones": self.observaciones.toPlainText().strip(),
            "archivo_path": self.archivo_path,
            "numero_transferencia": self.numero_transferencia.text().strip()
        }
        
        # ✅ CORREGIDO: Pasar usuario_actual completo (no solo el ID)
        try:
            from core.movimiento_manager import MovimientoManager
            movimiento_mgr = MovimientoManager(self.db)
            
            # ✅ CORRECCIÓN: Pasar self.usuario_actual completo
            movimiento_id, mensaje = movimiento_mgr.crear_movimiento(mov_data, bienes_ids, self.usuario_actual)
            
            if movimiento_id:
                QMessageBox.information(self, "✅ Éxito", f"Movimiento registrado correctamente\n{mensaje}")
                self.accept()
            else:
                QMessageBox.critical(self, "❌ Error", f"No se pudo guardar el movimiento:\n{mensaje}")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Error", f"Error inesperado:\n{str(e)}")