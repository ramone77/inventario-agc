"""
🗑️ DIÁLOGO DE ELIMINACIÓN DE MOVIMIENTO - Sistema de Inventario AGC
Diálogo simple para confirmar eliminación con motivo
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QTextEdit, QMessageBox,
                             QFrame, QSizePolicy)
from PyQt5.QtCore import Qt


class EliminarMovimientoDialog(QDialog):
    """Diálogo para confirmar eliminación de movimiento con motivo"""
    
    def __init__(self, movimiento_info, parent=None):
        super().__init__(parent)
        self.movimiento_info = movimiento_info
        self.motivo = ""
        
        self.setWindowTitle("🗑️ Confirmar Eliminación")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        
        # ===== ENCABEZADO CON ADVERTENCIA =====
        header_widget = QFrame()
        header_widget.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border: 2px solid #ffeaa7;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        header_layout = QVBoxLayout(header_widget)
        
        # Icono y título
        titulo = QLabel("⚠️ CONFIRMAR ELIMINACIÓN")
        titulo.setStyleSheet("""
            QLabel {
                color: #856404;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
            }
        """)
        
        # Información del movimiento
        info_text = f"""
        <b>Movimiento #{self.movimiento_info.get('id', 'N/A')}</b><br>
        Tipo: {self.movimiento_info.get('tipo', 'N/A')}<br>
        Fecha: {self.movimiento_info.get('fecha', 'N/A')}<br>
        Responsable: {self.movimiento_info.get('responsable_nombre', '')} {self.movimiento_info.get('responsable_apellido', '')}<br>
        Bienes: {self.movimiento_info.get('cantidad_bienes', 0)}<br>
        <br>
        <span style='color: #dc3545; font-weight: bold;'>
        Esta acción marcará el movimiento como "eliminado".<br>
        No se podrá revertir automáticamente.
        </span>
        """
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #333;")
        info_label.setWordWrap(True)
        
        header_layout.addWidget(titulo)
        header_layout.addWidget(info_label)
        
        layout.addWidget(header_widget)
        
        # ===== SELECCIÓN DE MOTIVO =====
        motivo_group = QFrame()
        motivo_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 15px;
                margin-top: 10px;
            }
        """)
        
        motivo_layout = QVBoxLayout(motivo_group)
        
        motivo_label = QLabel("📝 <b>Motivo de eliminación:</b>")
        motivo_label.setStyleSheet("margin-bottom: 8px;")
        
        # ComboBox con motivos predefinidos
        self.combo_motivo = QComboBox()
        self.combo_motivo.addItems([
            "Seleccione un motivo...",
            "Error de tipeo en datos",
            "Movimiento duplicado",
            "Datos del responsable incorrectos", 
            "Bienes incorrectos en el movimiento",
            "Error en tipo de movimiento",
            "Fecha incorrecta",
            "Acta firmada incorrecta o faltante",
            "Otro (especificar)"
        ])
        self.combo_motivo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
        """)
        self.combo_motivo.currentTextChanged.connect(self._actualizar_campo_detalle)
        
        motivo_layout.addWidget(motivo_label)
        motivo_layout.addWidget(self.combo_motivo)
        
        # ===== DETALLE ADICIONAL (opcional) =====
        detalle_label = QLabel("💬 <b>Detalle adicional (opcional):</b>")
        detalle_label.setStyleSheet("margin-top: 15px; margin-bottom: 8px;")
        
        self.text_detalle = QTextEdit()
        self.text_detalle.setPlaceholderText("Ej: El nombre estaba mal escrito, la fecha era incorrecta...")
        self.text_detalle.setMaximumHeight(80)
        self.text_detalle.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        
        motivo_layout.addWidget(detalle_label)
        motivo_layout.addWidget(self.text_detalle)
        
        layout.addWidget(motivo_group)
        
        # ===== BOTONES =====
        botones_layout = QHBoxLayout()
        
        # Botón Cancelar
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        
        # Botón Confirmar
        self.btn_confirmar = QPushButton("✅ Confirmar Eliminación")
        self.btn_confirmar.setEnabled(False)  # Inicialmente deshabilitado
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #e9ecef;
                color: #6c757d;
                border: 1px solid #ced4da;
            }
        """)
        self.btn_confirmar.clicked.connect(self._confirmar_eliminacion)
        
        botones_layout.addWidget(btn_cancelar)
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_confirmar)
        
        layout.addLayout(botones_layout)
        
        # ===== INSTRUCCIONES FINALES =====
        instrucciones = QLabel("💡 <i>El movimiento se marcará como 'eliminado' pero permanecerá en la base de datos para auditoría.</i>")
        instrucciones.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                margin-top: 10px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        instrucciones.setWordWrap(True)
        layout.addWidget(instrucciones)
    
    def _actualizar_campo_detalle(self, texto):
        """Habilita/deshabilita botón según selección de motivo"""
        if texto == "Seleccione un motivo...":
            self.btn_confirmar.setEnabled(False)
        else:
            self.btn_confirmar.setEnabled(True)
    
    def _confirmar_eliminacion(self):
        """Confirma la eliminación y construye el motivo completo"""
        motivo_base = self.combo_motivo.currentText()
        detalle = self.text_detalle.toPlainText().strip()
        
        if motivo_base == "Seleccione un motivo...":
            QMessageBox.warning(self, "Motivo requerido", 
                              "Por favor, seleccione un motivo de eliminación.")
            return
        
        # Construir motivo completo
        if detalle:
            self.motivo = f"{motivo_base} - {detalle}"
        else:
            self.motivo = motivo_base
        
        # Confirmación final
        confirmacion = QMessageBox.question(
            self,
            "Confirmación final",
            f"¿Está seguro de eliminar el movimiento #{self.movimiento_info.get('id', 'N/A')}?\n\n"
            f"Motivo: {self.motivo}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirmacion == QMessageBox.Yes:
            self.accept()