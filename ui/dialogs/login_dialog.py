"""
🎨 DIÁLOGO DE LOGIN - Sistema de Inventario AGC
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt


"""
🎨 DIÁLOGO DE LOGIN - Sistema de Inventario AGC
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                             QLineEdit, QPushButton, QLabel, QMessageBox)
from PyQt5.QtCore import Qt


class LoginDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db  # ✅ GUARDAR LA BASE DE DATOS
        self.usuario_actual = None  # ✅ INICIALIZAR PROPERTY
        self.setWindowTitle("🔐 Acceso al Sistema de Inventario")
        self.setFixedSize(350, 200)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
    
        # Logo/título
        titulo = QLabel("🏢 SISTEMA DE INVENTARIO - PATRIMONIO Y SUMINISTROS - AGC")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setWordWrap(True)
        titulo.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; margin: 10px; padding: 5px;")
            
        # Formulario
        form_layout = QFormLayout()
        
        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Tu número de legajo...")
        
        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Contraseña...")
        self.input_password.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("👤 Usuario:", self.input_usuario)
        form_layout.addRow("🔒 Contraseña:", self.input_password)
        
        # Botones
        btn_ingresar = QPushButton("✅ Ingresar al Sistema")
        btn_ingresar.clicked.connect(self.verificar_login)
        btn_ingresar.setStyleSheet("QPushButton { background-color: #27ae60; color: white; font-weight: bold; padding: 8px; }")
        
        layout.addWidget(titulo)
        layout.addLayout(form_layout)
        layout.addWidget(btn_ingresar)
    
    def verificar_login(self):
        """Verifica credenciales contra la base de datos"""
        usuario = self.input_usuario.text().strip()
        password = self.input_password.text().strip()
        
        if not usuario or not password:
            QMessageBox.warning(self, "Campos vacíos", "Por favor complete todos los campos")
            return
            
        try:
            # ✅ VERIFICAR SI LA TABLA USUARIOS EXISTE
            cur = self.db.conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
            tabla_existe = cur.fetchone() is not None
            
            if not tabla_existe:
                # Si no existe la tabla, usar usuarios hardcodeados
                self._usar_usuarios_hardcodeados(usuario, password)
                return
                
            # ✅ CONSULTAR USUARIO EN LA BASE DE DATOS REAL
            query = "SELECT id, nombre, rol FROM usuarios WHERE id = ? AND password = ? AND activo = 1"
            result = self.db.fetch_one(query, (usuario, password))
            
            if result:
                self.usuario_actual = {
                    "id": result[0],
                    "nombre": result[1],
                    "rol": result[2]
                }
                self.accept()  # ✅ LOGIN EXITOSO
            else:
                # Fallback a usuarios hardcodeados si no encuentra en BD
                self._usar_usuarios_hardcodeados(usuario, password)
                
        except Exception as e:
            print(f"❌ Error en login: {e}")
            # Fallback a usuarios hardcodeados en caso de error
            self._usar_usuarios_hardcodeados(usuario, password)

    def _usar_usuarios_hardcodeados(self, usuario, password):
        """Usa usuarios hardcodeados como fallback"""
        usuarios = {
            "20929508727": {"password": "admin123", "rol": "admin", "nombre": "Admin Principal"},
            "user2": {"password": "super123", "rol": "supervisor", "nombre": "Supervisor 1"},
            "user3": {"password": "super456", "rol": "supervisor", "nombre": "Supervisor 2"},
            "user4": {"password": "oper123", "rol": "operador", "nombre": "Operador 1"},
            "user5": {"password": "oper456", "rol": "operador", "nombre": "Operador 2"},
            "mario": {"password": "1234", "rol": "admin", "nombre": "Mario Admin"}
        }
        
        if usuario in usuarios and usuarios[usuario]["password"] == password:
            self.usuario_actual = {
                "id": usuario,
                "nombre": usuarios[usuario]["nombre"],
                "rol": usuarios[usuario]["rol"]
            }
            self.accept()
        else:
            QMessageBox.warning(self, "Error de acceso", 
                              "Usuario o contraseña incorrectos\n\n"
                              "💡 Usuarios de prueba:\n"
                              "Admin: mario / 1234\n"
                              "Supervisor: user2 / super123\n"
                              "Operador: user4 / oper123")