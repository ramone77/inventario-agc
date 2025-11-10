"""
🔄 GESTOR DE SINCRONIZACIÓN PROFESIONAL - Sistema de Inventario AGC
Maneja sincronización inteligente entre base local y red
"""

import sqlite3
import os
import shutil
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import json

from PyQt5.QtCore import QTimer, QObject, pyqtSignal
from database.db_manager import DB
from config.config_manager import (
    cargar_configuracion, 
    actualizar_ultima_sincronizacion,
    obtener_ruta_db_activa,
    obtener_ruta_db_maestra
)


class SyncManager(QObject):
    """Gestor principal de sincronización"""
    
    # ✅ Señales para comunicación con la UI
    sincronizacion_iniciada = pyqtSignal(str)  # mensaje
    sincronizacion_completada = pyqtSignal(str, bool)  # mensaje, exito
    progreso_sincronizacion = pyqtSignal(int, str)  # porcentaje, estado
    conflicto_detectado = pyqtSignal(dict)  # datos del conflicto
    
    def __init__(self, db_local):
        super().__init__()
        self.db_local = db_local
        self.db_red = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._sincronizar_automatico)
        self._inicializar_sincronizador()

    # ✅ AGREGAR AQUÍ - MÉTODO NUEVO
    def _crear_columnas_sincronizacion(self, db):
        """Crea las columnas necesarias para sincronización si no existen - VERSIÓN COMPLETA"""
        try:
            cursor = db.conn.cursor()
            columnas_creadas = False
            
            # ✅ VERIFICAR COLUMNAS EN TABLA BIENES
            cursor.execute("PRAGMA table_info(bienes)")
            columnas_bienes = [col[1] for col in cursor.fetchall()]
            
            # Lista de columnas necesarias para sincronización
            columnas_necesarias = [
                'fecha_actualizacion',
                'ultima_sincronizacion',
                'usuario_modificacion'
            ]
            
            # Agregar columnas faltantes
            for columna in columnas_necesarias:
                if columna not in columnas_bienes:
                    try:
                        cursor.execute(f"ALTER TABLE bienes ADD COLUMN {columna} TEXT")
                        print(f"✅ Columna '{columna}' agregada a tabla bienes")
                        columnas_creadas = True
                    except sqlite3.OperationalError as e:
                        print(f"⚠️ No se pudo agregar columna '{columna}': {e}")
            
            # ✅ VERIFICAR COLUMNAS EN TABLA MOVIMIENTOS
            cursor.execute("PRAGMA table_info(movimientos)")
            columnas_movimientos = [col[1] for col in cursor.fetchall()]
            
            columnas_movimientos_necesarias = [
                'fecha_actualizacion',
                'usuario_modificacion'
            ]
            
            for columna in columnas_movimientos_necesarias:
                if columna not in columnas_movimientos:
                    try:
                        cursor.execute(f"ALTER TABLE movimientos ADD COLUMN {columna} TEXT")
                        print(f"✅ Columna '{columna}' agregada a tabla movimientos")
                        columnas_creadas = True
                    except sqlite3.OperationalError as e:
                        print(f"⚠️ No se pudo agregar columna '{columna}': {e}")
            
            db.conn.commit()
            return columnas_creadas
            
        except Exception as e:
            print(f"❌ Error crítico creando columnas de sync: {e}")
            try:
                db.conn.rollback()
            except:
                pass
            return False
        
    def _inicializar_sincronizador(self):
        """Inicializa el sistema de sincronización"""
        config = cargar_configuracion()
        
        if config["auto_sincronizar"]:
            intervalo = config["intervalo_sincronizacion"] * 1000  # ms
            self.timer.start(intervalo)
            print(f"🔄 Sincronización automática cada {config['intervalo_sincronizacion']} segundos")
        
    def conectar_db_red(self):
        """Intenta conectar a la base de datos de red - VERSIÓN MEJORADA"""
        try:
            ruta_red = obtener_ruta_db_maestra()
            config = cargar_configuracion()
            
            print(f"🔍 Verificando acceso a red: {os.path.dirname(ruta_red)}")
            
            # ✅ VERIFICAR ACCESO AL DIRECTORIO DE RED
            if not os.path.exists(os.path.dirname(ruta_red)):
                print("❌ No se puede acceder al directorio de red")
                return False
            
            # ✅ VERIFICAR SI EL ARCHIVO DE BD EXISTE
            if not os.path.exists(ruta_red):
                print(f"⚠️ Archivo de BD no existe en red: {ruta_red}")
                # Podríamos crear uno nuevo, pero por ahora retornar False
                return False
            
            # ✅ CONECTAR A LA BASE DE DATOS DE RED
            self.db_red = DB(ruta_red, config["actas_folder_red"])
            
            # ✅ NUEVO: CREAR COLUMNAS DE SINCRONIZACIÓN SI FALTAN
            print("🔧 Verificando columnas de sincronización en BD red...")
            columnas_creadas = self._crear_columnas_sincronizacion(self.db_red)
            
            if columnas_creadas:
                print("✅ Columnas de sincronización verificadas/creadas en BD red")
            else:
                print("⚠️ No se pudieron crear algunas columnas en BD red")
            
            print("✅ Conectado exitosamente a base de datos de red")
            return True
            
        except sqlite3.OperationalError as e:
            print(f"❌ Error operacional conectando a BD red: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado conectando a BD red: {e}")
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
        config = cargar_configuracion()
        
        if not config["auto_sincronizar"]:
            return False
        
        # Verificar si hay conexión a red
        if not self._verificar_conexion_red():
            return False
        
        return True
    
    def _verificar_conexion_red(self):
        """Verifica si hay conexión a la red"""
        try:
            ruta_red = obtener_ruta_db_maestra()
            return os.path.exists(os.path.dirname(ruta_red))
        except:
            return False
    
    def _ejecutar_sincronizacion(self, tipo):
        """Ejecuta el proceso completo de sincronización"""
        try:
            self.progreso_sincronizacion.emit(0, "Conectando con red...")
            
            # 1. Conectar a red
            if not self.conectar_db_red():
                self.sincronizacion_completada.emit("❌ No se pudo conectar a la red", False)
                return False
            
            self.progreso_sincronizacion.emit(20, "Descargando cambios...")
            
            # 2. Descargar cambios desde red
            cambios_descargados = self._descargar_cambios_desde_red()
            
            self.progreso_sincronizacion.emit(60, "Subiendo cambios...")
            
            # 3. Subir cambios locales a red
            cambios_subidos = self._subir_cambios_a_red()
            
            self.progreso_sincronizacion.emit(80, "Resolviendo conflictos...")
            
            # 4. Resolver conflictos
            conflictos = self._resolver_conflictos()
            
            self.progreso_sincronizacion.emit(100, "Completando...")
            
            # 5. Actualizar estado
            actualizar_ultima_sincronizacion()
            
            # 6. Reportar resultados
            mensaje = self._generar_reporte_sincronizacion(
                cambios_descargados, cambios_subidos, conflictos
            )
            
            self.sincronizacion_completada.emit(mensaje, True)
            print(f"✅ Sincronización {tipo} completada: {mensaje}")
            return True
            
        except Exception as e:
            error_msg = f"❌ Error en sincronización: {str(e)}"
            self.sincronizacion_completada.emit(error_msg, False)
            print(error_msg)
            return False
    
    def _descargar_cambios_desde_red(self):
        """Descarga cambios desde la base maestra a local"""
        try:
            cambios = {
                "bienes_nuevos": 0,
                "bienes_actualizados": 0,
                "movimientos_nuevos": 0
            }
            
            # Obtener última sincronización
            config = cargar_configuracion()
            ultima_sync = config.get("ultima_sincronizacion")
            
            if not ultima_sync:
                print("🔄 Primera sincronización - descargando todo")
                return self._descargar_todo_desde_red()
            
            # 🔍 Obtener cambios recientes desde red
            cambios_bienes = self._obtener_bienes_modificados_desde(ultima_sync)
            cambios_movimientos = self._obtener_movimientos_modificados_desde(ultima_sync)
            
            # 📥 Aplicar cambios a local
            for bien in cambios_bienes:
                if self._aplicar_cambio_bien(bien):
                    cambios["bienes_actualizados"] += 1
            
            for movimiento in cambios_movimientos:
                if self._aplicar_cambio_movimiento(movimiento):
                    cambios["movimientos_nuevos"] += 1
            
            print(f"📥 Descargados: {cambios['bienes_actualizados']} bienes, {cambios['movimientos_nuevos']} movimientos")
            return cambios
            
        except Exception as e:
            print(f"❌ Error descargando cambios: {e}")
            return {"error": str(e)}
    
    def _descargar_todo_desde_red(self):
        """Descarga toda la base de datos (primera sincronización)"""
        try:
            # Crear backup de local primero
            self._crear_backup_local()
            
            # Copiar archivo completo de red a local
            ruta_red = obtener_ruta_db_maestra()
            ruta_local = obtener_ruta_db_activa()
            
            if os.path.exists(ruta_red):
                shutil.copy2(ruta_red, ruta_local)
                print("✅ Base completa descargada desde red")
                return {"completa": True, "mensaje": "Base completa sincronizada"}
            else:
                print("❌ No se encontró base en red")
                return {"error": "Base red no encontrada"}
                
        except Exception as e:
            print(f"❌ Error descargando base completa: {e}")
            return {"error": str(e)}
    
    def _obtener_bienes_modificados_desde(self, fecha_desde):
        """Obtiene bienes modificados desde fecha dada"""
        try:
            cursor = self.db_red.conn.cursor()
            query = """
                SELECT * FROM bienes 
                WHERE datetime(fecha_registro) > datetime(?)
                OR datetime(fecha_actualizacion) > datetime(?)
                ORDER BY fecha_actualizacion DESC
            """
            cursor.execute(query, (fecha_desde, fecha_desde))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo bienes modificados: {e}")
            return []
    
    def _obtener_movimientos_modificados_desde(self, fecha_desde):
        """Obtiene movimientos modificados desde fecha dada"""
        try:
            cursor = self.db_red.conn.cursor()
            query = "SELECT * FROM movimientos WHERE datetime(fecha) > datetime(?)"
            cursor.execute(query, (fecha_desde,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo movimientos modificados: {e}")
            return []
    
    def _aplicar_cambio_bien(self, bien_red):
        """Aplica cambio de bien desde red a local"""
        try:
            cursor = self.db_local.conn.cursor()
            
            # Verificar si existe en local
            cursor.execute("SELECT id FROM bienes WHERE id = ?", (bien_red['id'],))
            existe = cursor.fetchone()
            
            if existe:
                # Actualizar existente
                query = """
                    UPDATE bienes SET 
                    ficha=?, tipo=?, marca=?, modelo=?, serie=?, estado=?,
                    nombre=?, apellido=?, dni_cuit=?, institucional=?,
                    prd=?, fecha_actualizacion=?
                    WHERE id=?
                """
                cursor.execute(query, (
                    bien_red['ficha'], bien_red['tipo'], bien_red['marca'],
                    bien_red['modelo'], bien_red['serie'], bien_red['estado'],
                    bien_red['nombre'], bien_red['apellido'], bien_red['dni_cuit'],
                    bien_red['institucional'], bien_red['prd'],
                    datetime.now().isoformat(), bien_red['id']
                ))
            else:
                # Insertar nuevo
                columnas = list(bien_red.keys())
                placeholders = ','.join(['?'] * len(columnas))
                query = f"INSERT INTO bienes ({','.join(columnas)}) VALUES ({placeholders})"
                cursor.execute(query, list(bien_red))
            
            self.db_local.conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error aplicando cambio de bien: {e}")
            self.db_local.conn.rollback()
            return False
    
    def _subir_cambios_a_red(self):
        """Sube cambios locales a la base maestra"""
        try:
            cambios = {
                "bienes_subidos": 0,
                "movimientos_subidos": 0
            }
            
            config = cargar_configuracion()
            ultima_sync = config.get("ultima_sincronizacion")
            
            if not ultima_sync:
                print("⏭️  No hay última sincronización - saltando subida")
                return cambios
            
            # 🔍 Obtener cambios locales
            cambios_bienes = self._obtener_bienes_locales_modificados(ultima_sync)
            cambios_movimientos = self._obtener_movimientos_locales_modificados(ultima_sync)
            
            # 📤 Aplicar cambios a red
            for bien in cambios_bienes:
                if self._subir_bien_a_red(bien):
                    cambios["bienes_subidos"] += 1
            
            for movimiento in cambios_movimientos:
                if self._subir_movimiento_a_red(movimiento):
                    cambios["movimientos_subidos"] += 1
            
            print(f"📤 Subidos: {cambios['bienes_subidos']} bienes, {cambios['movimientos_subidos']} movimientos")
            return cambios
            
        except Exception as e:
            print(f"❌ Error subiendo cambios: {e}")
            return {"error": str(e)}
    
    def _obtener_bienes_locales_modificados(self, fecha_desde):
        """Obtiene bienes locales modificados desde fecha"""
        try:
            cursor = self.db_local.conn.cursor()
            query = """
                SELECT * FROM bienes 
                WHERE datetime(fecha_registro) > datetime(?)
                OR datetime(fecha_actualizacion) > datetime(?)
                ORDER BY fecha_actualizacion DESC
            """
            cursor.execute(query, (fecha_desde, fecha_desde))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo bienes locales: {e}")
            return []
    
    def _obtener_movimientos_locales_modificados(self, fecha_desde):
        """Obtiene movimientos locales modificados desde fecha"""
        try:
            cursor = self.db_local.conn.cursor()
            query = "SELECT * FROM movimientos WHERE datetime(fecha) > datetime(?)"
            cursor.execute(query, (fecha_desde,))
            return cursor.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo movimientos locales: {e}")
            return []
    
    def _subir_bien_a_red(self, bien_local):
        """Sube un bien local a la red"""
        try:
            cursor = self.db_red.conn.cursor()
            
            # Verificar si existe en red
            cursor.execute("SELECT id FROM bienes WHERE id = ?", (bien_local['id'],))
            existe = cursor.fetchone()
            
            if existe:
                # Actualizar existente en red
                query = """
                    UPDATE bienes SET 
                    ficha=?, tipo=?, marca=?, modelo=?, serie=?, estado=?,
                    nombre=?, apellido=?, dni_cuit=?, institucional=?,
                    prd=?, fecha_actualizacion=?
                    WHERE id=?
                """
                cursor.execute(query, (
                    bien_local['ficha'], bien_local['tipo'], bien_local['marca'],
                    bien_local['modelo'], bien_local['serie'], bien_local['estado'],
                    bien_local['nombre'], bien_local['apellido'], bien_local['dni_cuit'],
                    bien_local['institucional'], bien_local['prd'],
                    datetime.now().isoformat(), bien_local['id']
                ))
            else:
                # Insertar nuevo en red
                columnas = list(bien_local.keys())
                placeholders = ','.join(['?'] * len(columnas))
                query = f"INSERT INTO bienes ({','.join(columnas)}) VALUES ({placeholders})"
                cursor.execute(query, list(bien_local))
            
            self.db_red.conn.commit()
            return True
            
        except Exception as e:
            print(f"❌ Error subiendo bien a red: {e}")
            self.db_red.conn.rollback()
            return False
    
    def _resolver_conflictos(self):
        """Detecta y resuelve conflictos (versión básica)"""
        # ✅ POR AHORA: Implementación simple
        # ✅ EN EL FUTURO: Sistema avanzado de detección de conflictos
        return {"conflictos": 0, "resueltos": 0}
    
    def _crear_backup_local(self):
        """Crea backup de la base local antes de sincronizar"""
        try:
            ruta_local = obtener_ruta_db_activa()
            backup_dir = os.path.join(os.path.dirname(ruta_local), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_pre_sync_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            shutil.copy2(ruta_local, backup_path)
            print(f"✅ Backup creado: {backup_name}")
            return backup_path
            
        except Exception as e:
            print(f"⚠️ No se pudo crear backup: {e}")
            return None
    
    def _generar_reporte_sincronizacion(self, descargados, subidos, conflictos):
        """Genera reporte de sincronización"""
        reporte = "🔄 Sincronización completada: "
        
        if "error" in descargados:
            return f"❌ Error: {descargados['error']}"
        
        if "completa" in descargados:
            reporte += "Base completa sincronizada"
        else:
            partes = []
            if descargados.get("bienes_actualizados", 0) > 0:
                partes.append(f"📥 {descargados['bienes_actualizados']} bienes")
            if descargados.get("movimientos_nuevos", 0) > 0:
                partes.append(f"📥 {descargados['movimientos_nuevos']} movimientos")
            if subidos.get("bienes_subidos", 0) > 0:
                partes.append(f"📤 {subidos['bienes_subidos']} bienes")
            if subidos.get("movimientos_subidos", 0) > 0:
                partes.append(f"📤 {subidos['movimientos_subidos']} movimientos")
            
            if partes:
                reporte += " | ".join(partes)
            else:
                reporte += "Sin cambios"
        
        return reporte
    
    def obtener_estado(self):
        """Obtiene estado actual del sincronizador"""
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
        print("⏹️  Sincronización automática detenida")