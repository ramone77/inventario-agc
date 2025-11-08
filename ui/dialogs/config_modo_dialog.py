"""
🎨 DIÁLOGO DE CONFIGURACIÓN DE MODO - Sistema de Inventario AGC
Configuración de modo LOCAL/RED - VERSIÓN MODULAR
"""

import os
import sys  # ✅ AGREGADO - FALTABA ESTE IMPORT
import json
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QPushButton, QRadioButton,
                           QGroupBox, QMessageBox, QDialogButtonBox, QApplication)
from PyQt5.QtCore import Qt


# ✅ SOLUCIÓN: COPIAR LAS FUNCIONES DIRECTAMENTE EN EL ARCHIVO
# Para evitar problemas de importación circular

def cargar_configuracion():
    """Carga la configuración desde archivo JSON - VERSIÓN LOCAL"""
    config_file = _obtener_ruta_config()
    
    # Configuración por defecto
    CONFIG_DEFAULT = {
        "modo_local": False,
        "db_path_local": "C:\\InventarioApp\\inventario_local.db",
        "actas_folder_local": "C:\\InventarioApp\\actas_local", 
        "db_path_red": "M:\\Patrimonio\\01 PATRIMONIO\\InventarioApp\\inventario.db",
        "actas_folder_red": "M:\\Patrimonio\\01 PATRIMONIO\\InventarioApp\\actas"
    }
    
    try:
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("✅ Configuración cargada desde archivo")
                return config
        else:
            # Crear archivo con valores por defecto
            guardar_configuracion(CONFIG_DEFAULT)
            print("🆕 Archivo de configuración creado con valores por defecto")
            return CONFIG_DEFAULT
    except Exception as e:
        print(f"⚠️ Error cargando configuración: {e}")
        return CONFIG_DEFAULT


def guardar_configuracion(config):
    """Guarda la configuración en archivo JSON - VERSIÓN LOCAL"""
    config_file = _obtener_ruta_config()
    
    try:
        # Crear directorio si no existe
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print("💾 Configuración guardada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")
        return False


def _obtener_ruta_config():
    """Obtiene la ruta del archivo de configuración - VERSIÓN LOCAL"""
    # Buscar el directorio del proyecto de forma segura
    current_file = Path(__file__)
    # Subir 3 niveles: ui/dialogs/ → ui/ → inventario_agc/ → raíz
    project_root = current_file.parent.parent.parent
    return project_root / "config_modo.json"


class ConfiguracionModoDialog(QDialog):
    """Diálogo para configurar modo local/red - VERSIÓN MODULAR"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 Configuración de Modo")
        self.setFixedSize(500, 400)
        
        self.config_actual = cargar_configuracion()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("CONFIGURACIÓN DE MODO DE OPERACIÓN")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # Grupo: Selección de Modo
        grupo_modo = QGroupBox("🎯 MODO DE OPERACIÓN")
        layout_modo = QVBoxLayout(grupo_modo)
        
        self.radio_local = QRadioButton("🏠 MODO LOCAL (Pruebas/Desarrollo)")
        self.radio_red = QRadioButton("🌐 MODO RED (Producción/Compartido)")
        
        self.radio_local.setChecked(self.config_actual["modo_local"])
        self.radio_red.setChecked(not self.config_actual["modo_local"])
        
        layout_modo.addWidget(self.radio_local)
        layout_modo.addWidget(self.radio_red)
        layout.addWidget(grupo_modo)
        
        # Grupo: Configuración Red
        grupo_red = QGroupBox("🌐 CONFIGURACIÓN MODO RED")
        form_red = QFormLayout(grupo_red)
        
        self.input_db_red = QLineEdit()
        self.input_db_red.setText(self.config_actual["db_path_red"])
        self.input_db_red.setPlaceholderText(r"Ej: \\servidor\carpeta\inventario.db")
        
        self.input_actas_red = QLineEdit()
        self.input_actas_red.setText(self.config_actual["actas_folder_red"])
        self.input_actas_red.setPlaceholderText(r"Ej: \\servidor\carpeta\actas")
        
        form_red.addRow("Base de datos red:", self.input_db_red)
        form_red.addRow("Carpeta actas red:", self.input_actas_red)
        layout.addWidget(grupo_red)
        
        # Información
        info = QLabel("""
        💡 <b>Información:</b><br>
        • <b>MODO LOCAL:</b> Base de datos local para pruebas<br>
        • <b>MODO RED:</b> Base de datos compartida para producción<br>
        • Los cambios requieren reiniciar la aplicación
        """)
        info.setStyleSheet("background-color: #e8f4fd; padding: 10px; border-radius: 5px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Botones
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.guardar_configuracion)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def guardar_configuracion(self):
        """Guarda la configuración y cierra el diálogo"""
        nueva_config = {
            "modo_local": self.radio_local.isChecked(),
            "db_path_local": self.config_actual["db_path_local"],
            "actas_folder_local": self.config_actual["actas_folder_local"],
            "db_path_red": self.input_db_red.text().strip(),
            "actas_folder_red": self.input_actas_red.text().strip()
        }
        
        if guardar_configuracion(nueva_config):
            QMessageBox.information(
                self, 
                "Configuración Guardada", 
                "✅ Configuración guardada correctamente.\n\n"
                "🔄 <b>La aplicación se reiniciará para aplicar los cambios.</b>",
                QMessageBox.Ok
            )
            
            self.accept()
            # ✅ AHORA SYS ESTÁ DEFINIDO
            QApplication.quit()
            os.execl(sys.executable, sys.executable, *sys.argv)
        else:
            QMessageBox.warning(
                self,
                "Error",
                "❌ No se pudo guardar la configuración.",
                QMessageBox.Ok
            )