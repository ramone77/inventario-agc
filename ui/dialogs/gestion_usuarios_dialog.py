"""
👥 GESTIÓN DE USUARIOS - Sistema de Inventario AGC
Diálogo para administrar usuarios (solo administradores)
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QPushButton, QMessageBox,
                           QDialogButtonBox, QComboBox, QTableWidget,
                           QTableWidgetItem, QTabWidget, QWidget, QCheckBox,
                           QHeaderView, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon


class GestionUsuariosDialog(QDialog):
    """Diálogo de gestión completa de usuarios"""
    
    def __init__(self, db, usuario_actual, parent=None):
        super().__init__(parent)
        self.db = db
        self.usuario_actual = usuario_actual
        self.setWindowTitle("👥 Gestión de Usuarios - Sistema AGC")
        self.setMinimumSize(1000, 700)
        
        self._setup_ui()
        self._cargar_usuarios()

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # ===== TÍTULO =====
        titulo = QLabel("👥 GESTIÓN DE USUARIOS - SISTEMA AGC")
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                padding: 15px;
                background-color: #2c3e50;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(titulo)
        
        # ===== TABS =====
        self.tabs = QTabWidget()
        
        # Tab 1: Lista de usuarios
        self.tab_lista = self._crear_tab_lista()
        self.tabs.addTab(self.tab_lista, "📋 Lista de Usuarios")
        
        # Tab 2: Nuevo usuario
        self.tab_nuevo = self._crear_tab_nuevo()
        self.tabs.addTab(self.tab_nuevo, "➕ Nuevo Usuario")
        
        layout.addWidget(self.tabs)
        
        # ===== BOTONES =====
        botones = QDialogButtonBox(QDialogButtonBox.Close)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _crear_tab_lista(self):
        """Crea la pestaña de lista de usuarios"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de usuarios
        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(8)
        self.tabla_usuarios.setHorizontalHeaderLabels([
            "ID", "Nombre", "Apellido", "Cargo", "DNI/CUIT", "Email", "Rol", "Activo"
        ])
        
        # ✅ CONFIGURACIÓN BALANCEADA - ANCHOS FIJOS
        header = self.tabla_usuarios.horizontalHeader()
        
        # Anchos balanceados (en píxeles)
        self.tabla_usuarios.setColumnWidth(0, 80)    # ID
        self.tabla_usuarios.setColumnWidth(1, 100)   # Nombre
        self.tabla_usuarios.setColumnWidth(2, 100)   # Apellido
        self.tabla_usuarios.setColumnWidth(3, 150)   # Cargo
        self.tabla_usuarios.setColumnWidth(4, 100)   # DNI/CUIT
        self.tabla_usuarios.setColumnWidth(5, 150)   # Email
        self.tabla_usuarios.setColumnWidth(6, 80)    # Rol
        self.tabla_usuarios.setColumnWidth(7, 70)    # Activo
        
        # Permitir que el usuario ajuste manualmente
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        layout.addWidget(self.tabla_usuarios)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        
        self.btn_editar = QPushButton("✏️ Editar Usuario")
        self.btn_editar.clicked.connect(self._editar_usuario)
        self.btn_editar.setStyleSheet("QPushButton { background-color: #3498db; color: white; padding: 8px; }")
        
        self.btn_desactivar = QPushButton("🚫 Desactivar/Activar")
        self.btn_desactivar.clicked.connect(self._cambiar_estado_usuario)
        self.btn_desactivar.setStyleSheet("QPushButton { background-color: #e67e22; color: white; padding: 8px; }")
        
        self.btn_actualizar = QPushButton("🔄 Actualizar Lista")
        self.btn_actualizar.clicked.connect(self._cargar_usuarios)
        self.btn_actualizar.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 8px; }")
        
        btn_layout.addWidget(self.btn_editar)
        btn_layout.addWidget(self.btn_desactivar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_actualizar)
        
        layout.addLayout(btn_layout)
        
        return tab

    def _crear_tab_nuevo(self):
        """Crea la pestaña para nuevo usuario"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        grupo = QGroupBox("📝 Datos del Nuevo Usuario")
        form = QFormLayout(grupo)
        
        # Campos del formulario
        self.nuevo_id = QLineEdit()
        self.nuevo_id.setPlaceholderText("Usuario único (ej: jperez)")
        
        self.nuevo_nombre = QLineEdit()
        self.nuevo_nombre.setPlaceholderText("Nombre...")
        
        self.nuevo_apellido = QLineEdit()
        self.nuevo_apellido.setPlaceholderText("Apellido...")
        
        self.nuevo_cargo = QLineEdit()
        self.nuevo_cargo.setPlaceholderText("Cargo...")
        
        self.nuevo_dni = QLineEdit()
        self.nuevo_dni.setPlaceholderText("DNI o CUIT...")
        
        self.nuevo_email = QLineEdit()
        self.nuevo_email.setPlaceholderText("email@agc.gob.ar")
        
        self.nuevo_password = QLineEdit()
        self.nuevo_password.setPlaceholderText("Contraseña temporal")
        self.nuevo_password.setEchoMode(QLineEdit.Password)
        
        self.nuevo_rol = QComboBox()
        self.nuevo_rol.addItems(["operador", "supervisor", "admin"])
        
        self.nuevo_activo = QCheckBox("Usuario activo")
        self.nuevo_activo.setChecked(True)
        
        # Agregar campos al formulario
        form.addRow("👤 ID Usuario:*", self.nuevo_id)
        form.addRow("📛 Nombre:*", self.nuevo_nombre)
        form.addRow("📛 Apellido:*", self.nuevo_apellido)
        form.addRow("💼 Cargo:*", self.nuevo_cargo)
        form.addRow("🆔 DNI/CUIT:", self.nuevo_dni)
        form.addRow("📧 Email:", self.nuevo_email)
        form.addRow("🔒 Contraseña:*", self.nuevo_password)
        form.addRow("🎭 Rol:*", self.nuevo_rol)
        form.addRow(self.nuevo_activo)
        
        layout.addWidget(grupo)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_limpiar = QPushButton("🧹 Limpiar Formulario")
        self.btn_limpiar.clicked.connect(self._limpiar_formulario)
        self.btn_limpiar.setStyleSheet("QPushButton { background-color: #95a5a6; color: white; padding: 8px; }")
        
        self.btn_crear = QPushButton("✅ Crear Usuario")
        self.btn_crear.clicked.connect(self._crear_usuario)
        self.btn_crear.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 8px; font-weight: bold; }")
        
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_crear)
        
        layout.addLayout(btn_layout)
        layout.addStretch()
        
        return tab

    def _cargar_usuarios(self):
        """Carga todos los usuarios en la tabla"""
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT id, nombre, apellido, cargo, dni_cuit, email, rol, activo
                FROM usuarios 
                ORDER BY apellido, nombre
            """)
            usuarios = cursor.fetchall()
            
            self.tabla_usuarios.setRowCount(len(usuarios))
            
            for i, usuario in enumerate(usuarios):
                self.tabla_usuarios.setItem(i, 0, QTableWidgetItem(usuario['id']))
                self.tabla_usuarios.setItem(i, 1, QTableWidgetItem(usuario['nombre']))
                self.tabla_usuarios.setItem(i, 2, QTableWidgetItem(usuario['apellido']))
                self.tabla_usuarios.setItem(i, 3, QTableWidgetItem(usuario['cargo']))
                self.tabla_usuarios.setItem(i, 4, QTableWidgetItem(usuario['dni_cuit'] or ""))
                self.tabla_usuarios.setItem(i, 5, QTableWidgetItem(usuario['email'] or ""))
                self.tabla_usuarios.setItem(i, 6, QTableWidgetItem(usuario['rol']))
                
                # Estado con icono
                estado_item = QTableWidgetItem("✅ Activo" if usuario['activo'] else "❌ Inactivo")
                estado_item.setData(Qt.UserRole, usuario['activo'])
                self.tabla_usuarios.setItem(i, 7, estado_item)
            
            print(f"✅ {len(usuarios)} usuarios cargados en gestión")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cargando usuarios: {str(e)}")

    def _limpiar_formulario(self):
        """Limpia el formulario de nuevo usuario"""
        self.nuevo_id.clear()
        self.nuevo_nombre.clear()
        self.nuevo_apellido.clear()
        self.nuevo_cargo.clear()
        self.nuevo_dni.clear()
        self.nuevo_email.clear()
        self.nuevo_password.clear()
        self.nuevo_rol.setCurrentIndex(0)
        self.nuevo_activo.setChecked(True)

    def _crear_usuario(self):
        """Crea un nuevo usuario"""
        try:
            # Validar campos obligatorios
            if not all([self.nuevo_id.text(), self.nuevo_nombre.text(), 
                       self.nuevo_apellido.text(), self.nuevo_cargo.text(),
                       self.nuevo_password.text()]):
                QMessageBox.warning(self, "Error", "Completa los campos obligatorios (*)")
                return
            
            # Verificar que el ID no exista
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM usuarios WHERE id = ?", (self.nuevo_id.text(),))
            if cursor.fetchone()[0] > 0:
                QMessageBox.warning(self, "Error", "El ID de usuario ya existe")
                return
            
            # Insertar nuevo usuario
            cursor.execute("""
                INSERT INTO usuarios 
                (id, nombre, apellido, cargo, dni_cuit, email, password, rol, activo, usuario_creacion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.nuevo_id.text(),
                self.nuevo_nombre.text(),
                self.nuevo_apellido.text(),
                self.nuevo_cargo.text(),
                self.nuevo_dni.text() or None,
                self.nuevo_email.text() or None,
                self.nuevo_password.text(),
                self.nuevo_rol.currentText(),
                1 if self.nuevo_activo.isChecked() else 0,
                self.usuario_actual['id']
            ))
            
            self.db.conn.commit()
            
            QMessageBox.information(self, "Éxito", f"Usuario {self.nuevo_id.text()} creado correctamente")
            self._limpiar_formulario()
            self._cargar_usuarios()
            self.tabs.setCurrentIndex(0)  # Volver a la lista
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error creando usuario: {str(e)}")

    def _editar_usuario(self):
        """Abre diálogo para editar usuario seleccionado"""
        fila = self.tabla_usuarios.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Error", "Selecciona un usuario para editar")
            return
        
        usuario_id = self.tabla_usuarios.item(fila, 0).text()
        
        try:
            # Obtener datos actuales del usuario
            cursor = self.db.conn.cursor()
            cursor.execute("""
                SELECT id, nombre, apellido, cargo, dni_cuit, email, rol, activo
                FROM usuarios WHERE id = ?
            """, (usuario_id,))
            usuario = cursor.fetchone()
            
            if not usuario:
                QMessageBox.warning(self, "Error", "Usuario no encontrado")
                return
            
            # Crear diálogo de edición
            dialog = QDialog(self)
            dialog.setWindowTitle(f"✏️ Editar Usuario: {usuario['id']}")
            dialog.setFixedSize(500, 650)
            
            layout = QVBoxLayout(dialog)
            
            # Formulario de edición
            grupo = QGroupBox("📝 Editar Datos del Usuario")
            form = QFormLayout(grupo)
            
            # ID (solo lectura)
            id_label = QLabel(usuario['id'])
            id_label.setStyleSheet("background-color: #f8f9fa; padding: 8px; border: 1px solid #bdc3c7;")
            form.addRow("👤 ID Usuario:", id_label)
            
            # Nombre
            edit_nombre = QLineEdit(usuario['nombre'])
            edit_nombre.setPlaceholderText("Nombre...")
            
            # Apellido
            edit_apellido = QLineEdit(usuario['apellido'])
            edit_apellido.setPlaceholderText("Apellido...")
            
            # Cargo
            edit_cargo = QLineEdit(usuario['cargo'])
            edit_cargo.setPlaceholderText("Cargo...")
            
            # DNI/CUIT
            edit_dni = QLineEdit(usuario['dni_cuit'] or "")
            edit_dni.setPlaceholderText("DNI o CUIT...")
            
            # Email
            edit_email = QLineEdit(usuario['email'] or "")
            edit_email.setPlaceholderText("email@agc.gob.ar")
            
            # Rol
            edit_rol = QComboBox()
            edit_rol.addItems(["operador", "supervisor", "admin"])
            edit_rol.setCurrentText(usuario['rol'])
            
            # ✅ NUEVO: Campo de contraseña
            edit_password = QLineEdit()
            edit_password.setPlaceholderText("Dejar vacío para mantener contraseña actual")
            edit_password.setEchoMode(QLineEdit.Password)
            
            # Activo
            edit_activo = QCheckBox("Usuario activo")
            edit_activo.setChecked(bool(usuario['activo']))
            
            # Agregar campos al formulario
            form.addRow("📛 Nombre:*", edit_nombre)
            form.addRow("📛 Apellido:*", edit_apellido)
            form.addRow("💼 Cargo:*", edit_cargo)
            form.addRow("🆔 DNI/CUIT:", edit_dni)
            form.addRow("📧 Email:", edit_email)
            form.addRow("🎭 Rol:*", edit_rol)
            form.addRow("🔒 Nueva Contraseña:", edit_password)
            form.addRow(edit_activo)
            
            layout.addWidget(grupo)
            
            # Botones
            btn_layout = QHBoxLayout()
            btn_guardar = QPushButton("💾 Guardar Cambios")
            btn_guardar.setStyleSheet("QPushButton { background-color: #27ae60; color: white; padding: 10px; font-weight: bold; }")
            
            btn_cancelar = QPushButton("❌ Cancelar")
            btn_cancelar.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; padding: 10px; }")
            
            btn_layout.addWidget(btn_guardar)
            btn_layout.addWidget(btn_cancelar)
            layout.addLayout(btn_layout)
            
            # ✅ CORREGIDO: Usar lambda para conectar el botón
            btn_guardar.clicked.connect(lambda: self._guardar_cambios_usuario(
                dialog, cursor, usuario_id, edit_nombre, edit_apellido, 
                edit_cargo, edit_dni, edit_email, edit_rol, edit_password, edit_activo
            ))
            
            btn_cancelar.clicked.connect(dialog.reject)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error editando usuario: {str(e)}")

    def _guardar_cambios_usuario(self, dialog, cursor, usuario_id, edit_nombre, edit_apellido, 
                                edit_cargo, edit_dni, edit_email, edit_rol, edit_password, edit_activo):
        """Guarda los cambios del usuario editado"""
        if not all([edit_nombre.text(), edit_apellido.text(), edit_cargo.text()]):
            QMessageBox.warning(dialog, "Error", "Completa los campos obligatorios (*)")
            return
        
        try:
            # ✅ ACTUALIZACIÓN MEJORADA - Manejo de contraseña
            if edit_password.text():  # Si se ingresó nueva contraseña
                cursor.execute("""
                    UPDATE usuarios SET 
                    nombre=?, apellido=?, cargo=?, dni_cuit=?, email=?, rol=?, activo=?, password=?
                    WHERE id=?
                """, (
                    edit_nombre.text(),
                    edit_apellido.text(),
                    edit_cargo.text(),
                    edit_dni.text() or None,
                    edit_email.text() or None,
                    edit_rol.currentText(),
                    1 if edit_activo.isChecked() else 0,
                    edit_password.text(),  # Nueva contraseña
                    usuario_id
                ))
                mensaje = f"Usuario {usuario_id} actualizado correctamente\n\n🔐 Contraseña cambiada"
            else:  # Mantener contraseña actual
                cursor.execute("""
                    UPDATE usuarios SET 
                    nombre=?, apellido=?, cargo=?, dni_cuit=?, email=?, rol=?, activo=?
                    WHERE id=?
                """, (
                    edit_nombre.text(),
                    edit_apellido.text(),
                    edit_cargo.text(),
                    edit_dni.text() or None,
                    edit_email.text() or None,
                    edit_rol.currentText(),
                    1 if edit_activo.isChecked() else 0,
                    usuario_id
                ))
                mensaje = f"Usuario {usuario_id} actualizado correctamente\n\n🔐 Contraseña mantenida"
            
            self.db.conn.commit()
            QMessageBox.information(dialog, "Éxito", mensaje)
            dialog.accept()
            self._cargar_usuarios()  # Actualizar lista
            
        except Exception as e:
            QMessageBox.critical(dialog, "Error", f"Error actualizando usuario: {str(e)}")

    def _cambiar_estado_usuario(self):
        """Activa/desactiva el usuario seleccionado"""
        fila = self.tabla_usuarios.currentRow()
        if fila == -1:
            QMessageBox.warning(self, "Error", "Selecciona un usuario")
            return
        
        usuario_id = self.tabla_usuarios.item(fila, 0).text()
        estado_actual = self.tabla_usuarios.item(fila, 7).data(Qt.UserRole)
        nuevo_estado = 0 if estado_actual else 1
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "UPDATE usuarios SET activo = ? WHERE id = ?",
                (nuevo_estado, usuario_id)
            )
            self.db.conn.commit()
            
            estado_texto = "activado" if nuevo_estado else "desactivado"
            QMessageBox.information(self, "Éxito", f"Usuario {usuario_id} {estado_texto}")
            self._cargar_usuarios()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error cambiando estado: {str(e)}")

# ✅ AGREGAR ESTO AL FINAL PARA PRUEBAS RÁPIDAS
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    from database.db_manager import DB
    
    app = QApplication(sys.argv)
    
    # Conexión de prueba
    db = DB("inventario_local.db", "actas_local")
    
    # Usuario de prueba
    usuario_prueba = {
        'id': 'admin_test',
        'nombre': 'Admin',
        'apellido': 'Test', 
        'rol': 'admin'
    }
    
    dialog = GestionUsuariosDialog(db, usuario_prueba)
    dialog.exec_()