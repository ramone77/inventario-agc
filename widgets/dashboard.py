"""
📊 DASHBOARD Y GRÁFICOS - Sistema de Inventario AGC
Widgets para el dashboard ejecutivo
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt


class TarjetaKPI(QWidget):
    """Widget de tarjeta KPI para el dashboard"""
    
    def __init__(self, titulo, valor, color, parent=None):
        super().__init__(parent)
        self.titulo = titulo
        self.valor = valor
        self.color = color
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.label_titulo = QLabel(self.titulo)
        self.label_titulo.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        self.label_titulo.setAlignment(Qt.AlignCenter)
        
        self.label_valor = QLabel(self.valor)
        self.label_valor.setStyleSheet("color: white; font-weight: bold; font-size: 24px;")
        self.label_valor.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.label_titulo)
        layout.addWidget(self.label_valor)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.color};
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }}
        """)
    
    def actualizar_valor(self, nuevo_valor):
        """Actualiza el valor de la tarjeta"""
        self.label_valor.setText(str(nuevo_valor))