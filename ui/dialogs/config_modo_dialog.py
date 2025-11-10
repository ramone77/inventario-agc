"""
🎨 DIÁLOGO DE CONFIGURACIÓN PROFESIONAL - Sistema de Inventario AGC
Nueva arquitectura con modo de sincronización - VERSIÓN ACTUALIZADA
"""

import os
import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLabel, QLineEdit, QPushButton, QRadioButton,
                           QGroupBox, QMessageBox, QDialogButtonBox, QApplication,
                           QFrame, QCheckBox)
from PyQt5.QtCore import Qt


# ✅ USAMOS EL NUEVO CONFIG_MANAGER ACTUALIZADO
from config.config_manager import cargar_configuracion, guardar_configuracion, _obtener_ruta_config


class ConfiguracionModoDialog(QDialog):
    """Diálogo para configurar modo profesional con sincronización"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔧 Configuración Profesional del Sistema")
        self.setFixedSize(600, 550)  # ✅ MÁS GRANDE PARA NUEVAS OPCIONES
        
        self.config_actual = cargar_configuracion()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        titulo = QLabel("CONFIGURACIÓN PROFESIONAL - SISTEMA DE INVENTARIO")
        titulo.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #2c3e50; 
            padding: 15px;
            background-color: #3498db;
            color: white;
            border-radius: 8px;
            margin-bottom: 10px;
        """)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        # ✅ NUEVO: Grupo de Modo de Trabajo PROFESIONAL
        grupo_modo = QGroupBox("🎯 MODO DE TRABAJO PROFESIONAL")
        grupo_modo.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        layout_modo = QVBoxLayout(grupo_modo)
        
        # ✅ NUEVOS RADIO BUTTONS PROFESIONALES
        self.radio_sincronizacion = QRadioButton("🔄 MODO SINCRONIZACIÓN (RECOMENDADO)")
        self.radio_sincronizacion.setToolTip("Trabaja localmente rápido + Sincroniza automáticamente con red")
        
        self.radio_red_directo = QRadioButton("🌐 MODO RED DIRECTO (PRODUCCIÓN)")
        self.radio_red_directo.setToolTip("Trabaja directamente en base de red - Más lento pero colaborativo")
        
        self.radio_local_solo = QRadioButton("🏠 MODO LOCAL SOLO (PRUEBAS)")
        self.radio_local_solo.setToolTip("Solo base local - Rápido pero sin colaboración")
        
        # Configurar selección actual
        modo_actual = self.config_actual.get("modo_trabajo", "local_con_sincronizacion")
        if modo_actual == "local_con_sincronizacion":
            self.radio_sincronizacion.setChecked(True)
        elif modo_actual == "red_directo":
            self.radio_red_directo.setChecked(True)
        else:  # local_solo
            self.radio_local_solo.setChecked(True)
        
        layout_modo.addWidget(self.radio_sincronizacion)
        layout_modo.addWidget(self.radio_red_directo)
        layout_modo.addWidget(self.radio_local_solo)
        layout.addWidget(grupo_modo)
        
        # ✅ NUEVO: Configuración de Sincronización (solo visible en modo sincronización)
        self.grupo_sync = QGroupBox("⚙️ CONFIGURACIÓN DE SINCRONIZACIÓN")
        self.grupo_sync.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        layout_sync = QVBoxLayout(self.grupo_sync)
        
        # Auto-sincronización
        self.check_auto_sync = QCheckBox("Sincronización automática")
        self.check_auto_sync.setChecked(self.config_actual.get("auto_sincronizar", True))
        self.check_auto_sync.setToolTip("Sincronizar automáticamente cada 5 minutos")
        layout_sync.addWidget(self.check_auto_sync)
        
        # Intervalo de sincronización
        intervalo_layout = QHBoxLayout()
        intervalo_layout.addWidget(QLabel("Intervalo (minutos):"))
        self.input_intervalo = QLineEdit()
        self.input_intervalo.setText(str(self.config_actual.get("intervalo_sincronizacion", 5)))
        self.input_intervalo.setFixedWidth(50)
        self.input_intervalo.setToolTip("Intervalo en minutos para sincronización automática")
        intervalo_layout.addWidget(self.input_intervalo)
        intervalo_layout.addStretch()
        layout_sync.addLayout(intervalo_layout)
        
        # Notificaciones
        self.check_notificar_conflictos = QCheckBox("Notificar conflictos")
        self.check_notificar_conflictos.setChecked(self.config_actual.get("notificar_conflictos", True))
        self.check_notificar_conflictos.setToolTip("Mostrar alertas cuando se detecten conflictos")
        layout_sync.addWidget(self.check_notificar_conflictos)
        
        layout.addWidget(self.grupo_sync)
        
        # ✅ NUEVO: Configuración de Rutas
        grupo_rutas = QGroupBox("📁 CONFIGURACIÓN DE RUTAS")
        grupo_rutas.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; }")
        form_rutas = QFormLayout(grupo_rutas)
        
        # Base de datos red
        self.input_db_red = QLineEdit()
        self.input_db_red.setText(self.config_actual.get("db_maestra_red", ""))
        self.input_db_red.setPlaceholderText(r"Ej: \\servidor\carpeta\inventario.db")
        self.input_db_red.setToolTip("Ruta de la base de datos maestra en red")
        form_rutas.addRow("Base maestra red:", self.input_db_red)
        
        # Base de datos local
        self.input_db_local = QLineEdit()
        self.input_db_local.setText(self.config_actual.get("db_cache_local", ""))
        self.input_db_local.setPlaceholderText(r"Ej: C:\InventarioApp\inventario_cache.db")
        self.input_db_local.setToolTip("Ruta de la base de datos local (cache)")
        form_rutas.addRow("Base cache local:", self.input_db_local)
        
        # Carpeta actas red
        self.input_actas_red = QLineEdit()
        self.input_actas_red.setText(self.config_actual.get("actas_folder_red", ""))
        self.input_actas_red.setPlaceholderText(r"Ej: \\servidor\carpeta\actas")
        self.input_actas_red.setToolTip("Carpeta de actas en red")
        form_rutas.addRow("Carpeta actas red:", self.input_actas_red)
        
        # Carpeta actas local
        self.input_actas_local = QLineEdit()
        self.input_actas_local.setText(self.config_actual.get("actas_folder_local", ""))
        self.input_actas_local.setPlaceholderText(r"Ej: C:\InventarioApp\actas_local")
        self.input_actas_local.setToolTip("Carpeta de actas local")
        form_rutas.addRow("Carpeta actas local:", self.input_actas_local)
        
        layout.addWidget(grupo_rutas)
        
        # ✅ NUEVO: Información Mejorada
        info = QLabel("""
        💡 <b>INFORMACIÓN PROFESIONAL:</b><br><br>
        
        <b>🔄 MODO SINCRONIZACIÓN (RECOMENDADO):</b><br>
        • <b>Velocidad:</b> Máxima (trabaja local)<br>
        • <b>Colaboración:</b> Total (sincroniza con red)<br>
        • <b>Resiliencia:</b> Alta (funciona sin red)<br>
        • <b>Ideal para:</b> Uso diario de todo el equipo<br><br>
        
        <b>🌐 MODO RED DIRECTO:</b><br>
        • <b>Velocidad:</b> Lenta (depende de red)<br>
        • <b>Colaboración:</b> Total (base compartida)<br>
        • <b>Resiliencia:</b> Baja (no funciona sin red)<br>
        • <b>Ideal para:</b> Administradores en red estable<br><br>
        
        <b>🏠 MODO LOCAL SOLO:</b><br>
        • <b>Velocidad:</b> Máxima (solo local)<br>
        • <b>Colaboración:</b> Ninguna<br>
        • <b>Resiliencia:</b> Total (no necesita red)<br>
        • <b>Ideal para:</b> Pruebas y desarrollo
        """)
        info.setStyleSheet("""
            background-color: #e8f4fd; 
            padding: 15px; 
            border-radius: 8px;
            border: 1px solid #3498db;
            font-size: 11px;
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Botones
        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.guardar_configuracion)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)
        
        # ✅ CONECTAR señales para mostrar/ocultar configuración de sync
        self.radio_sincronizacion.toggled.connect(self._actualizar_visibilidad_sync)
        self._actualizar_visibilidad_sync()

    def _actualizar_visibilidad_sync(self):
        """Muestra u oculta la configuración de sincronización según el modo"""
        sync_visible = self.radio_sincronizacion.isChecked()
        self.grupo_sync.setVisible(sync_visible)
        
        # Ajustar tamaño del diálogo
        if sync_visible:
            self.setFixedHeight(550)
        else:
            self.setFixedHeight(500)

    def guardar_configuracion(self):
        """Guarda la configuración profesional y reinicia la aplicación"""
        try:
            # Determinar modo de trabajo
            if self.radio_sincronizacion.isChecked():
                modo_trabajo = "local_con_sincronizacion"
            elif self.radio_red_directo.isChecked():
                modo_trabajo = "red_directo"
            else:
                modo_trabajo = "local_solo"
            
            # Validar rutas
            if not self.input_db_red.text().strip():
                QMessageBox.warning(self, "Error", "La ruta de la base maestra en red es obligatoria")
                return
                
            if not self.input_db_local.text().strip():
                QMessageBox.warning(self, "Error", "La ruta de la base cache local es obligatoria")
                return
            
            # Validar intervalo
            try:
                intervalo = int(self.input_intervalo.text())
                if intervalo < 1 or intervalo > 60:
                    raise ValueError("Intervalo debe estar entre 1 y 60 minutos")
            except ValueError as e:
                QMessageBox.warning(self, "Error", f"Intervalo inválido: {str(e)}")
                return
            
            # Crear configuración completa
            nueva_config = {
                # Modo de trabajo profesional
                "modo_trabajo": modo_trabajo,
                
                # Rutas
                "db_maestra_red": self.input_db_red.text().strip(),
                "db_cache_local": self.input_db_local.text().strip(),
                "actas_folder_red": self.input_actas_red.text().strip(),
                "actas_folder_local": self.input_actas_local.text().strip(),
                
                # Configuración sincronización
                "auto_sincronizar": self.check_auto_sync.isChecked(),
                "intervalo_sincronizacion": intervalo * 60,  # Convertir a segundos
                "notificar_conflictos": self.check_notificar_conflictos.isChecked(),
                "resolucion_automatica": False,  # Por ahora manual
                "backup_automatico": True,
                "max_backups": 10,
                
                # Mantener compatibilidad con campos legacy
                "modo_local": (modo_trabajo == "local_solo"),
                "db_path_red": self.input_db_red.text().strip(),
                "db_path_local": self.input_db_local.text().strip(),
                
                # Preservar usuario actual si existe
                "usuario_actual": self.config_actual.get("usuario_actual", ""),
                "ultima_sincronizacion": self.config_actual.get("ultima_sincronizacion")
            }
            
            if guardar_configuracion(nueva_config):
                QMessageBox.information(
                    self, 
                    "✅ Configuración Guardada", 
                    "Configuración profesional guardada correctamente.\n\n"
                    "🔄 <b>La aplicación se reiniciará para aplicar los cambios.</b>\n\n"
                    f"📊 <b>Modo activado:</b> {modo_trabajo.replace('_', ' ').title()}",
                    QMessageBox.Ok
                )
                
                self.accept()
                # Reiniciar aplicación
                QApplication.quit()
                os.execl(sys.executable, sys.executable, *sys.argv)
            else:
                QMessageBox.warning(
                    self,
                    "❌ Error",
                    "No se pudo guardar la configuración.\n"
                    "Verifique los permisos de escritura.",
                    QMessageBox.Ok
                )
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error Crítico",
                f"Error inesperado al guardar configuración:\n{str(e)}",
                QMessageBox.Ok
            )