"""
🔐 DIÁLOGO DE LOGIN - Sistema de Inventario AGC
Autenticación de usuarios con roles
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QDialogButtonBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class LoginDialog(QDialog):
    """Diálogo de autenticación de usuarios"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.usuario_actual = None
        self.setWindowTitle("🔐 Acceso al Sistema de Inventario")
        self.setFixedSize(400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("SISTEMA DE INVENTARIO AGC")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 15px;
            background-color: #3498db;
            color: white;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        layout.addWidget(titulo)
        
        # Formulario
        form_layout = QFormLayout()
        
        # Usuario
        self.combo_usuario = QComboBox()
        self.combo_usuario.setEditable(False)
        self._cargar_usuarios()
        form_layout.addRow("👤 Usuario:", self.combo_usuario)
        
        # Contraseña
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setPlaceholderText("Ingresa tu contraseña")
        form_layout.addRow("🔒 Contraseña:", self.input_password)
        
        layout.addLayout(form_layout)
        
        # Botones
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Ok).setText("Ingresar")
        botones.button(QDialogButtonBox.Cancel).setText("Salir")
        botones.accepted.connect(self._verificar_login)
        botones.rejected.connect(self.reject)
        
        layout.addWidget(botones)
        
        # Información
        info = QLabel("💡 Usuario de prueba: mario / 1234")
        info.setStyleSheet("""
            color: #7f8c8d;
            font-style: italic;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
            margin-top: 10px;
        """)
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)

    def _cargar_usuarios(self):
        """Carga la lista de usuarios desde la base de datos"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, nombre, rol FROM usuarios WHERE activo = 1")
            usuarios = cursor.fetchall()
            
            for usuario in usuarios:
                texto = f"{usuario['id']} - {usuario['nombre']} ({usuario['rol']})"
                self.combo_usuario.addItem(texto, usuario['id'])
                
        except Exception as e:
            print(f"Error cargando usuarios: {e}")
            # Usuario por defecto
            self.combo_usuario.addItem("mario - Mario Admin (admin)", "mario")

    def _verificar_login(self):
        """Verifica las credenciales del usuario"""
        try:
            # Obtener usuario seleccionado
            usuario_id = self.combo_usuario.currentData()
            password = self.input_password.text()
            
            if not usuario_id or not password:
                QMessageBox.warning(self, "Error", "Por favor completa todos los campos")
                return
            
            # Verificar credenciales
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT id, nombre, rol FROM usuarios WHERE id = ? AND password = ? AND activo = 1",
                (usuario_id, password)
            )
            usuario = cursor.fetchone()
            
            if usuario:
                self.usuario_actual = {
                    'id': usuario['id'],
                    'nombre': usuario['nombre'],
                    'rol': usuario['rol']
                }
                print(f"✅ Usuario autenticado: {usuario['id']} ({usuario['rol']})")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Credenciales incorrectas")
                self.input_password.clear()
                self.input_password.setFocus()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error en autenticación: {str(e)}")

    def obtener_usuario_actual(self):
        """Retorna el usuario actualmente logueado"""
        return self.usuario_actual