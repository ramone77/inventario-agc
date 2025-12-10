"""
🔄 GESTOR DE SINCRONIZACIÓN PROFESIONAL - VERSIÓN CORREGIDA
Sistema de sincronización compatible con tu schema actual
"""

import sqlite3
import os
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import json

from PyQt5.QtCore import QTimer, QObject, pyqtSignal

class SyncManager(QObject):
    """Gestor principal de sincronización - VERSIÓN CORREGIDA"""
    
    # ✅ Señales para comunicación con la UI
    sincronizacion_iniciada = pyqtSignal(str)
    sincronizacion_completada = pyqtSignal(str, bool)
    progreso_sincronizacion = pyqtSignal(int, str)
    conflicto_detectado = pyqtSignal(dict)

    def _importar_config(self):
        """Importa config_manager solo cuando se necesita"""
        from config.config_manager import (
            cargar_configuracion, 
            actualizar_ultima_sincronizacion,
            obtener_ruta_db_activa,
            obtener_ruta_db_maestra
        )
        return cargar_configuracion, actualizar_ultima_sincronizacion, obtener_ruta_db_activa, obtener_ruta_db_maestra

    def __init__(self, db_local):
        super().__init__()
        self.db_local = db_local
        self.db_red = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._sincronizar_automatico)
        self._inicializar_sincronizador()

    def _inicializar_sincronizador(self):
        """Inicializa el sistema de sincronización"""
        cargar_configuracion, _, _, _ = self._importar_config()
        config = cargar_configuracion()
        
        if config["auto_sincronizar"]:
            intervalo = config["intervalo_sincronizacion"] * 1000
            self.timer.start(intervalo)
            print(f"🔄 Sincronización automática cada {config['intervalo_sincronizacion']} segundos")
    
    def conectar_db_red(self):
        """Intenta conectar a la base de datos de red - VERSIÓN CORREGIDA"""
        try:
            _, _, _, obtener_ruta_db_maestra = self._importar_config()
            ruta_red = obtener_ruta_db_maestra()
            cargar_configuracion, _, _, _ = self._importar_config()
            config = cargar_configuracion()
            
            print(f"🔍 Verificando acceso a red: {os.path.dirname(ruta_red)}")
            
            # ✅ VERIFICAR SI EL DIRECTORIO DE RED ES ACCESIBLE
            directorio_red = os.path.dirname(ruta_red)
            if not os.path.exists(directorio_red):
                print(f"❌ No se puede acceder al directorio de red: {directorio_red}")
                print("💡 Verifica que la unidad M: esté mapeada y tengas permisos")
                return False
            
            # ✅ SI NO EXISTE LA BD, CREAR UNA NUEVA
            if not os.path.exists(ruta_red):
                print(f"🆕 Archivo de BD no existe en red. Creando nueva base de datos...")
                try:
                    from database.db_manager import DB
                    self.db_red = DB(ruta_red, config["actas_folder_red"])
                    print(f"✅ Nueva base de datos creada en red: {ruta_red}")
                    return True
                except Exception as e:
                    print(f"❌ No se pudo crear BD en red: {e}")
                    return False
            
            # ✅ CONECTAR A BD EXISTENTE
            from database.db_manager import DB
            self.db_red = DB(ruta_red, config["actas_folder_red"])
            print("✅ Conectado exitosamente a base de datos de red")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a BD red: {e}")
            return False
    
    def sincronizar_manual(self):
        """Sincronización manual iniciada por el usuario"""
        self.sincronizacion_iniciada.emit("Iniciando sincronización manual...")
        return self._ejecutar_sincronizacion("manual")
    
    def _sincronizar_automatico(self):
        """Sincronización automática por timer"""
        if not self._debe_sincronizar():
            return
        
        print("🔄 Sincronización automática iniciada")
        self._ejecutar_sincronizacion("auto")
    
    def _debe_sincronizar(self):
        """Verifica si debe realizar sincronización automática"""
        cargar_configuracion, _, _, _ = self._importar_config()
        config = cargar_configuracion()
        
        if not config["auto_sincronizar"]:
            return False
        
        if not self._verificar_conexion_red():
            return False
        
        return True
    
    def _verificar_conexion_red(self):
        """Verifica si hay conexión a la red"""
        try:
            _, _, _, obtener_ruta_db_maestra = self._importar_config()
            ruta_red = obtener_ruta_db_maestra()
            return os.path.exists(os.path.dirname(ruta_red))
        except:
            return False
    
    def _ejecutar_sincronizacion(self, tipo):
        """Ejecuta el proceso completo de sincronización - VERSIÓN SIMPLIFICADA"""
        try:
            self.progreso_sincronizacion.emit(0, "Conectando con red...")
            
            # 1. Conectar a red
            if not self.conectar_db_red():
                self.sincronizacion_completada.emit("❌ No se pudo conectar a la red", False)
                return False
            
            self.progreso_sincronizacion.emit(30, "Sincronizando base completa...")
            
            # 2. PARA PRIMERA VERSIÓN: Sincronización completa simple
            exito = self._sincronizacion_completa_simple()
            
            if exito:
                self.progreso_sincronizacion.emit(100, "Completando...")
                
                # Actualizar estado
                _, actualizar_ultima_sincronizacion, _, _ = self._importar_config()
                actualizar_ultima_sincronizacion()
                
                mensaje = "✅ Sincronización completa exitosa"
                self.sincronizacion_completada.emit(mensaje, True)
                print(f"✅ Sincronización {tipo} completada")
                return True
            else:
                self.sincronizacion_completada.emit("❌ Error en sincronización", False)
                return False
            
        except Exception as e:
            error_msg = f"❌ Error en sincronización: {str(e)}"
            self.sincronizacion_completada.emit(error_msg, False)
            print(error_msg)
            return False
    
    def _sincronizacion_completa_simple(self):
        """Sincronización completa simple - reemplaza ambas bases"""
        try:
            print("🔄 Iniciando sincronización completa...")
            
            # Crear backup de ambas bases primero
            backup_local = self._crear_backup_local()
            backup_red = self._crear_backup_red()
            
            # Estrategia simple: copiar la base más reciente a la otra
            # Por ahora, copiamos local → red para pruebas
            _, _, obtener_ruta_db_activa, obtener_ruta_db_maestra = self._importar_config()
            ruta_local = obtener_ruta_db_activa()
            ruta_red = obtener_ruta_db_maestra()
            
            if os.path.exists(ruta_local):
                shutil.copy2(ruta_local, ruta_red)
                print("✅ Base local copiada a red")
                return True
            else:
                print("❌ No existe base local para copiar")
                return False
                
        except Exception as e:
            print(f"❌ Error en sincronización completa: {e}")
            
            # Restaurar backups en caso de error
            self._restaurar_backup_si_existe(backup_local, obtener_ruta_db_activa())
            self._restaurar_backup_si_existe(backup_red, obtener_ruta_db_maestra())
            
            return False
    
    def _crear_backup_local(self):
        """Crea backup de la base local"""
        try:
            _, _, obtener_ruta_db_activa, _ = self._importar_config()
            ruta_local = obtener_ruta_db_activa()
            return self._crear_backup(ruta_local, "local")
        except Exception as e:
            print(f"⚠️ No se pudo crear backup local: {e}")
            return None
    
    def _crear_backup_red(self):
        """Crea backup de la base de red"""
        try:
            _, _, _, obtener_ruta_db_maestra = self._importar_config()
            ruta_red = obtener_ruta_db_maestra()
            return self._crear_backup(ruta_red, "red")
        except Exception as e:
            print(f"⚠️ No se pudo crear backup red: {e}")
            return None
    
    def _crear_backup(self, ruta_original, tipo):
        """Crea un backup de una base de datos"""
        try:
            if not os.path.exists(ruta_original):
                print(f"⚠️ No se puede hacer backup de {tipo}: archivo no existe")
                return None
                
            backup_dir = os.path.join(os.path.dirname(ruta_original), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{tipo}_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            shutil.copy2(ruta_original, backup_path)
            print(f"✅ Backup {tipo} creado: {backup_name}")
            return backup_path
            
        except Exception as e:
            print(f"⚠️ Error creando backup {tipo}: {e}")
            return None
    
    def _restaurar_backup_si_existe(self, backup_path, ruta_original):
        """Restaura un backup si existe"""
        try:
            if backup_path and os.path.exists(backup_path):
                shutil.copy2(backup_path, ruta_original)
                print(f"✅ Backup restaurado: {os.path.basename(backup_path)}")
                return True
        except Exception as e:
            print(f"⚠️ Error restaurando backup: {e}")
        return False
    
    def obtener_estado(self):
        """Obtiene estado actual del sincronizador"""
        cargar_configuracion, _, _, _ = self._importar_config()
        config = cargar_configuracion()
        
        return {
            "modo_trabajo": config["modo_trabajo"],
            "auto_sincronizar": config["auto_sincronizar"],
            "ultima_sincronizacion": config["ultima_sincronizacion"],
            "conectado_red": self._verificar_conexion_red(),
            "timer_activo": self.timer.isActive()
        }
    
    def detener_sincronizacion(self):
        """Detiene la sincronización automática"""
        self.timer.stop()
        print("⏹️ Sincronización automática detenida")
        
def sincronizar_archivos_pdf(self):
    """Sincroniza archivos PDF entre local y red"""
    try:
        from config.settings import get_config, get_modo_trabajo
        
        config = get_config()
        modo = get_modo_trabajo()
        
        # Solo sincronizar si estamos en modo de sincronización
        if modo != "local_con_sincronizacion":
            print("📭 Modo no requiere sincronización de archivos")
            return
        
        print("🔄 Sincronizando archivos PDF...")
        
        # 1. LOCAL → RED (subir nuevos archivos locales)
        if os.path.exists(config["actas_folder_local"]):
            archivos_locales = os.listdir(config["actas_folder_local"])
        else:
            archivos_locales = []
        
        if os.path.exists(config["actas_folder_red"]):
            archivos_red = os.listdir(config["actas_folder_red"])
        else:
            archivos_red = []
        
        # Subir archivos nuevos de local a red
        for archivo in archivos_locales:
            if archivo.endswith('.pdf') and archivo not in archivos_red:
                try:
                    origen = os.path.join(config["actas_folder_local"], archivo)
                    destino = os.path.join(config["actas_folder_red"], archivo)
                    shutil.copy2(origen, destino)
                    print(f"  📤 Subido a red: {archivo}")
                except Exception as e:
                    print(f"  ⚠️ Error subiendo {archivo}: {e}")
        
        # 2. RED → LOCAL (descargar archivos nuevos de red)
        for archivo in archivos_red:
            if archivo.endswith('.pdf') and archivo not in archivos_locales:
                try:
                    origen = os.path.join(config["actas_folder_red"], archivo)
                    destino = os.path.join(config["actas_folder_local"], archivo)
                    shutil.copy2(origen, destino)
                    print(f"  📥 Descargado de red: {archivo}")
                except Exception as e:
                    print(f"  ⚠️ Error descargando {archivo}: {e}")
        
        print("✅ Sincronización PDF completada")
        
    except Exception as e:
        print(f"❌ Error sincronizando PDFs: {e}")