"""
🗄️ GESTOR DE BASE DE DATOS - Sistema de Inventario AGC
Clase principal para operaciones de base de datos SQLite
"""

import sqlite3
import os
import shutil
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMessageBox
import sys


class DB:
    """Maneja todas las operaciones de base de datos - VERSIÓN COMPLETA MIGRADA"""
    
    def __init__(self, path, actas_folder):
        self.path = path
        self.actas_folder = actas_folder
        self.conn = None
        self._conectar_db()

    def _conectar_db(self):
        """Intenta conectar a la base de datos con manejo de errores"""
        max_intentos = 3
        for intento in range(max_intentos):
            try:
                print(f"🔗 Intentando conectar a la base de datos... (Intento {intento + 1}/{max_intentos})")
                print(f"📍 Ruta: {self.path}")
                
                # ✅ MEJORADO: Crear directorio automáticamente
                directorio = os.path.dirname(self.path)
                if not os.path.exists(directorio):
                    print(f"⚠️  El directorio no existe: {directorio}")
                    print("💡 Creando directorio automáticamente...")
                    try:
                        os.makedirs(directorio, exist_ok=True)
                        print(f"✅ Directorio creado: {directorio}")
                    except Exception as e:
                        print(f"❌ No se pudo crear el directorio: {e}")
                        # Cambiar automáticamente a modo local
                        self._cambiar_a_modo_local_emergencia()
                        return
                
                self.conn = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
                self.conn.row_factory = sqlite3.Row
                print(f"✅ Conectado exitosamente a: {os.path.basename(self.path)}")
                self._init_db()
                return
                
            except sqlite3.OperationalError as e:
                print(f"❌ Error en intento {intento + 1}: {e}")
                
                if intento < max_intentos - 1:
                    print("🔄 Reintentando en 3 segundos...")
                    time.sleep(3)
                else:
                    print(f"💡 No se pudo conectar después de {max_intentos} intentos")
                    # Cambiar automáticamente a modo local
                    self._cambiar_a_modo_local_emergencia()
                    return

    def _cambiar_a_modo_local_emergencia(self):
        """Cambia automáticamente a modo local en caso de error"""
        print("🔄 Cambiando automáticamente a MODO LOCAL...")
        
        # Usar ruta local por defecto
        local_db = "inventario_local.db"
        local_actas = "actas_local"
        
        print(f"📍 Nueva ruta local: {local_db}")
        
        try:
            self.conn = sqlite3.connect(local_db, check_same_thread=False, timeout=30)
            self.conn.row_factory = sqlite3.Row
            print(f"✅ Conectado exitosamente a base de datos local")
            self._init_db()
        except Exception as e:
            print(f"❌ Error crítico: No se pudo conectar ni siquiera en modo local: {e}")
            raise e

    def _cambiar_a_modo_local(self):
        """Cambia automáticamente a modo local - VERSIÓN SIN IMPORTS CIRCULARES"""
        print("🔄 Cambiando a MODO LOCAL...")
        
        # Usar ruta local por defecto directamente
        local_db = "inventario_local.db"
        local_actas = "actas_local"
        
        print(f"📍 Nueva ruta local: {local_db}")
        
        try:
            self.conn = sqlite3.connect(local_db, check_same_thread=False, timeout=30)
            self.conn.row_factory = sqlite3.Row
            print(f"✅ Conectado exitosamente a base de datos local")
            self._init_db()
            
            # Mostrar mensaje al usuario
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(None, "Modo Local", 
                                "Se cambió automáticamente a modo local.\n\n"
                                "Los datos se guardarán localmente hasta que se restablezca la conexión de red.")
                                
        except Exception as e:
            print(f"❌ Error crítico: No se pudo conectar ni siquiera en modo local: {e}")
            raise e

    def _init_db(self):
        """Inicializa las tablas de la base de datos - VERSIÓN MEJORADA"""
        cur = self.conn.cursor()
        
        print("🔧 Inicializando base de datos...")
        
        # PRIMERO: Crear tabla bienes si no existe
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bienes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ficha TEXT NOT NULL,
                tipo TEXT NOT NULL,
                marca TEXT,
                modelo TEXT,
                serie TEXT,
                linea TEXT,
                sim TEXT,
                empresa TEXT,
                imei TEXT,
                responsable TEXT,
                nombre TEXT,
                apellido TEXT,
                dni_cuit TEXT,
                institucional TEXT,
                descripcion TEXT,
                estado TEXT DEFAULT 'En depósito',
                fecha_registro TEXT,
                monto_original TEXT,
                prd TEXT,
                anio_prd TEXT
            )
        """)
        print("✅ Tabla 'bienes' verificada")

        # ✅ ESTRUCTURA MEJORADA (COMPLETA)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                cargo TEXT NOT NULL,
                dni_cuit TEXT UNIQUE,
                email TEXT,
                password TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'operador',
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
                ultimo_acceso TEXT,
                usuario_creacion TEXT
            )
        """)
        self._actualizar_estructura_usuarios()
        print("✅ Tabla 'usuarios' verificada")
        
        # ✅ USUARIO DE PRUEBA MEJORADO
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE id = 'mario'")
        if cur.fetchone()[0] == 0:
            cur.execute(
                """INSERT INTO usuarios 
                (id, nombre, apellido, cargo, dni_cuit, email, password, rol, usuario_creacion) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("mario", "Mario", "Admin", "Administrador del Sistema", 
                "20123456789", "mario@agc.gob.ar", "1234", "admin", "sistema")
            )
            print("✅ Usuario de prueba 'mario' creado con datos completos")
        
        # ✅ NUEVA LÍNEA: Verificar y agregar columnas de asignación
        self.verificar_y_agregar_columnas_asignacion()
        
        # SEGUNDO: Agregar columnas faltantes si es necesario
        self._agregar_columnas_faltantes()
        
        # TERCERO: Crear tabla movimientos MEJORADA - VERSIÓN CON CAMPOS SEPARADOS PARA DOCX Y PDF
        cur.execute("""
            CREATE TABLE IF NOT EXISTS movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                fecha TEXT NOT NULL,
                responsable TEXT NOT NULL,
                responsable_nombre TEXT,
                responsable_apellido TEXT,
                responsable_dni_cuit TEXT,
                responsable_institucional TEXT,
                observaciones TEXT,
                archivo_path_docx TEXT,         
                archivo_path_pdf TEXT,          
                numero_transferencia TEXT,
                eliminado INTEGER DEFAULT 0,
                fecha_eliminacion TEXT,
                motivo_eliminacion TEXT
            )
        """)
        print("✅ Tabla 'movimientos' actualizada con campos de eliminación")
        
        # CUARTO: Verificar y agregar columnas nuevas a movimientos si es necesario
        self._agregar_columnas_movimientos()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bienes_movimientos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_bien INTEGER NOT NULL,
                id_movimiento INTEGER NOT NULL,
                FOREIGN KEY(id_bien) REFERENCES bienes(id),
                FOREIGN KEY(id_movimiento) REFERENCES movimientos(id)
            )
        """)
        
        # QUINTO: Crear tabla de logs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs_actividad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL,
                accion TEXT NOT NULL,
                detalles TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # SEXTO: Crear índices
        self._crear_indices_seguros()
        
        self.conn.commit()
        print("✅ Base de datos inicializada correctamente")

    # ... (aquí van todos los demás métodos de la clase DB)
    # Los pongo en el siguiente mensaje para no hacerlo muy largo
    # ... (continuación de los métodos de la clase DB)

    def _agregar_columnas_movimientos(self):
        """Agrega columnas faltantes a la tabla movimientos de forma segura"""
        try:
            cur = self.conn.cursor()
            
            # Verificar qué columnas existen
            cur.execute("PRAGMA table_info(movimientos)")
            columnas_existentes = [col[1] for col in cur.fetchall()]
            print(f"🔍 Columnas existentes en movimientos: {columnas_existentes}")
            
            # Lista de TODAS las columnas que deberían existir
            columnas_necesarias = [
                'responsable_nombre', 
                'responsable_apellido', 
                'responsable_dni_cuit', 
                'responsable_institucional',
                'eliminado',           # ← NUEVA
                'fecha_eliminacion',   # ← NUEVA  
                'motivo_eliminacion'   # ← NUEVA
            ]
            
            # Agregar columnas faltantes
            columnas_agregadas = []
            for columna in columnas_necesarias:
                if columna not in columnas_existentes:
                    try:
                        if columna == 'eliminado':
                            cur.execute(f"ALTER TABLE movimientos ADD COLUMN {columna} INTEGER DEFAULT 0")
                        else:
                            cur.execute(f"ALTER TABLE movimientos ADD COLUMN {columna} TEXT")
                        
                        columnas_agregadas.append(columna)
                        print(f"✅ Columna '{columna}' agregada a movimientos")
                        
                    except sqlite3.OperationalError as e:
                        print(f"⚠️ No se pudo agregar columna '{columna}': {e}")
                else:
                    print(f"✓ Columna '{columna}' ya existe")
            
            if columnas_agregadas:
                self.conn.commit()
                print(f"✅ Columnas agregadas exitosamente: {columnas_agregadas}")
            
            cur.close()
            
        except Exception as e:
            print(f"❌ Error en _agregar_columnas_movimientos: {e}")

    def _actualizar_estructura_usuarios(self):
        """Actualiza la estructura de la tabla usuarios si es necesario"""
        try:
            cur = self.conn.cursor()
            
            # Verificar columnas existentes
            cur.execute("PRAGMA table_info(usuarios)")
            columnas_existentes = [col[1] for col in cur.fetchall()]
            
            # Columnas nuevas que necesitamos
            columnas_necesarias = [
                'apellido', 'cargo', 'dni_cuit', 'email', 
                'fecha_creacion', 'ultimo_acceso', 'usuario_creacion'
            ]
            
            # Agregar columnas faltantes
            for columna in columnas_necesarias:
                if columna not in columnas_existentes:
                    try:
                        if columna in ['fecha_creacion', 'ultimo_acceso']:
                            cur.execute(f"ALTER TABLE usuarios ADD COLUMN {columna} TEXT")
                        else:
                            cur.execute(f"ALTER TABLE usuarios ADD COLUMN {columna} TEXT")
                        print(f"✅ Columna '{columna}' agregada a usuarios")
                    except sqlite3.OperationalError as e:
                        print(f"⚠️ No se pudo agregar columna '{columna}': {e}")
            
            self.conn.commit()
            
        except Exception as e:
            print(f"❌ Error actualizando estructura de usuarios: {e}")

    def _agregar_columnas_faltantes(self):
        """Agrega columnas faltantes a la tabla bienes de forma segura"""
        cur = self.conn.cursor()
        
        # Lista de columnas que deberían existir
        columnas_necesarias = [
            'prd', 'anio_prd', 'monto_original', 'linea', 'sim', 
            'empresa', 'imei', 'nombre', 'apellido', 'dni_cuit'
        ]
        
        # Verificar qué columnas existen
        cur.execute("PRAGMA table_info(bienes)")
        columnas_existentes = [col[1] for col in cur.fetchall()]
        
        # Agregar columnas faltantes
        for columna in columnas_necesarias:
            if columna not in columnas_existentes:
                try:
                    cur.execute(f"ALTER TABLE bienes ADD COLUMN {columna} TEXT")
                    print(f"✅ Columna '{columna}' agregada")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  No se pudo agregar columna '{columna}': {e}")
        
        cur.close()

    def _crear_indices_seguros(self):
        """Crea índices de forma segura, evitando errores por columnas faltantes"""
        cur = self.conn.cursor()
        
        # Verificar qué columnas existen antes de crear índices
        cur.execute("PRAGMA table_info(bienes)")
        columnas_existentes = [col[1] for col in cur.fetchall()]
        
        # Verificar columnas de movimientos también
        cur.execute("PRAGMA table_info(movimientos)")
        columnas_movimientos = [col[1] for col in cur.fetchall()]
        
        # Índices a crear (solo si la columna existe)
        indices = [
            ('idx_bienes_ficha', 'bienes', 'ficha'),
            ('idx_bienes_tipo', 'bienes', 'tipo'),
            ('idx_bienes_prd', 'bienes', 'prd'),
            ('idx_bienes_estado', 'bienes', 'estado'),
            ('idx_bienes_busqueda', 'bienes', 'ficha, tipo, estado'),
            ('idx_bienes_responsable', 'bienes', 'nombre, apellido'),
            ('idx_movimientos_fecha', 'movimientos', 'fecha DESC'),
            ('idx_bienes_movimientos_bien', 'bienes_movimientos', 'id_bien'),
        ]
        
        for nombre_idx, tabla, columnas in indices:
            # Verificar que la tabla existe
            cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
            if not cur.fetchone():
                print(f"⏭️  Saltando índice '{nombre_idx}' - tabla '{tabla}' no existe")
                continue
                
            # Verificar que todas las columnas del índice existen
            if tabla == 'bienes':
                columnas_target = columnas_existentes
            elif tabla == 'movimientos':
                columnas_target = columnas_movimientos
            else:
                columnas_target = []  # Para bienes_movimientos, asumimos que existe
                
            columnas_lista = [col.strip().split(' ')[0] for col in columnas.split(',')]  # Quitar DESC
            
            if not columnas_target or all(columna in columnas_target for columna in columnas_lista):
                try:
                    cur.execute(f"CREATE INDEX IF NOT EXISTS {nombre_idx} ON {tabla}({columnas})")
                    print(f"✅ Índice '{nombre_idx}' creado en {tabla}")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  No se pudo crear índice '{nombre_idx}': {e}")
            else:
                print(f"⏭️  Saltando índice '{nombre_idx}' - columnas no existen: {columnas_lista}")
        
        cur.close()

    def verificar_y_agregar_columnas_asignacion(self):
        """Verifica y agrega las columnas de asignación si no existen"""
        cur = self.conn.cursor()
        
        columnas_necesarias = ['nombre', 'apellido', 'dni_cuit', 'institucional']
        
        # Verificar qué columnas existen
        cur.execute("PRAGMA table_info(bienes)")
        columnas_existentes = [col[1] for col in cur.fetchall()]
        
        # Agregar columnas faltantes
        for columna in columnas_necesarias:
            if columna not in columnas_existentes:
                try:
                    cur.execute(f"ALTER TABLE bienes ADD COLUMN {columna} TEXT")
                    print(f"✅ Columna '{columna}' agregada a la tabla bienes")
                except sqlite3.OperationalError as e:
                    print(f"⚠️ No se pudo agregar columna '{columna}': {e}")
        
        self.conn.commit()
        cur.close()

    def add_bien(self, data):
        """Agrega un nuevo bien al inventario - VERSIÓN CORREGIDA CON ASIGNACIÓN"""
        cur = self.conn.cursor()
        
        try:
            # ✅ PRIMERO: Verificar y agregar columnas de asignación si no existen
            self.verificar_y_agregar_columnas_asignacion()
            
            # ✅ SEGUNDO: Verificar qué columnas existen AHORA
            cur.execute("PRAGMA table_info(bienes)")
            todas_columnas = [col[1] for col in cur.fetchall()]

            # ✅ NUEVO: LIMPIAR CAMPOS NUMÉRICOS ANTES DE GUARDAR
            campos_a_limpiar = ['imei', 'dni_cuit', 'linea', 'sim', 'serie']
            for campo in campos_a_limpiar:
                if campo in data and data[campo] is not None:
                    # Convertir a string y limpiar .0
                    valor = str(data[campo])
                    if valor.endswith('.0'):
                        data[campo] = valor[:-2]
                    # También limpiar si es número científico o decimal cero
                    elif '.' in valor and valor.split('.')[1] == '0':
                        data[campo] = valor.split('.')[0]            
            
            # ✅ TERCERO: Usar TODOS los campos de data que existen en la BD
            columnas_a_usar = []
            valores_a_usar = []
            
            for columna in todas_columnas:
                if columna in data:
                    columnas_a_usar.append(columna)
                    valor = data.get(columna, "")
                    valores_a_usar.append(str(valor).strip() if valor is not None else "")
            
                     
            # ✅ CUARTO: Validar que tenemos al menos las columnas básicas
            columnas_basicas = ["ficha", "tipo", "marca", "modelo", "serie", "estado", "fecha_registro"]
            columnas_faltantes = [col for col in columnas_basicas if col not in columnas_a_usar]
            
            if columnas_faltantes:
                print(f"⚠️ Columnas básicas faltantes: {columnas_faltantes}")
                # Agregar las columnas básicas faltantes con valores por defecto
                for columna in columnas_faltantes:
                    if columna == "fecha_registro":
                        columnas_a_usar.append(columna)
                        valores_a_usar.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    elif columna == "estado":
                        columnas_a_usar.append(columna)
                        valores_a_usar.append("En depósito")
                    else:
                        columnas_a_usar.append(columna)
                        valores_a_usar.append("")
            
            # ✅ QUINTO: Insertar en la base de datos
            keys = ",".join(columnas_a_usar)
            placeholders = ",".join("?" for _ in columnas_a_usar)
            
            cur.execute(f"INSERT INTO bienes ({keys}) VALUES ({placeholders})", tuple(valores_a_usar))
            self.conn.commit()
            
            print(f"✅ Bien guardado exitosamente - ID: {cur.lastrowid}")
            return True
            
        except sqlite3.IntegrityError as e:
            print(f"❌ Error de integridad (posible duplicado): {e}")
            return False
        except Exception as e:
            print(f"❌ Error al agregar bien: {e}")
            return False
        finally:
            cur.close()

    def list_bienes(self, limite=1000):
        """Obtiene bienes ordenados por fecha con límite para rendimiento"""
        try:
            cur = self.conn.cursor()
            query = """
                SELECT id, ficha, tipo, marca, modelo, serie, estado, prd, 
                    nombre, apellido, dni_cuit, institucional,
                    linea, sim, empresa, imei, descripcion, fecha_registro, 
                    monto_original, anio_prd
                FROM bienes 
                ORDER BY fecha_registro DESC 
                LIMIT ?
            """
            cur.execute(query, (limite,))
            resultado = cur.fetchall()
            cur.close()
            return resultado
        except Exception as e:
            print(f"Error al listar bienes: {e}")
            return []

    def list_bienes_completos(self):
        """Obtiene TODOS los bienes sin límite - PARA FILTROS"""
        try:
            cur = self.conn.cursor()
            query = """
                SELECT id, ficha, tipo, marca, modelo, serie, estado, prd, 
                    nombre, apellido, dni_cuit, institucional,
                    linea, sim, empresa, imei, descripcion, fecha_registro, 
                    monto_original, anio_prd
                FROM bienes 
                ORDER BY fecha_registro DESC
            """
            cur.execute(query)
            resultado = cur.fetchall()
            cur.close()
            print(f"✅ Obtenidos {len(resultado)} registros completos para filtros")
            return resultado
        except Exception as e:
            print(f"❌ Error al listar bienes completos: {e}")
            return []

    def buscar_bienes(self, texto, limite=1000):
        """Busca bienes por cualquier campo con límite para rendimiento"""
        cur = self.conn.cursor()
        try:
            query = """
                SELECT id, ficha, tipo, marca, modelo, serie, estado, prd, 
                    nombre, apellido, dni_cuit, institucional
                FROM bienes 
                WHERE ficha LIKE ? OR tipo LIKE ? OR marca LIKE ? OR modelo LIKE ? 
                OR serie LIKE ? OR imei LIKE ? OR linea LIKE ? OR nombre LIKE ? 
                OR apellido LIKE ? OR dni_cuit LIKE ? OR institucional LIKE ? 
                OR descripcion LIKE ? OR prd LIKE ?
                ORDER BY fecha_registro DESC
                LIMIT ?
            """
            parametro = f"%{texto}%"
            cur.execute(query, [parametro] * 13 + [limite])
            return cur.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Error en búsqueda: {e}")
            # Búsqueda básica como fallback
            try:
                query_basica = """
                    SELECT id, ficha, tipo, marca, modelo, serie, estado, prd
                    FROM bienes 
                    WHERE ficha LIKE ? OR tipo LIKE ? OR marca LIKE ? OR modelo LIKE ? OR serie LIKE ?
                    ORDER BY fecha_registro DESC
                    LIMIT ?
                """
                parametro = f"%{texto}%"
                cur.execute(query_basica, [parametro] * 5 + [limite])
                return cur.fetchall()
            except:
                return []
        finally:
            cur.close()

    def log_actividad(self, usuario, accion, detalles=""):
        """Registra actividad de usuarios en la BD"""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS logs_actividad (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT NOT NULL,
                    accion TEXT NOT NULL,
                    detalles TEXT,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute(
                "INSERT INTO logs_actividad (usuario, accion, detalles) VALUES (?, ?, ?)",
                (usuario, accion, detalles)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error en log: {e}")
            return False
        finally:
            cur.close()

    def crear_backup(self):
        """Crea un backup automático de la base de datos"""
        try:
            # Crear carpeta de backups si no existe
            backup_dir = os.path.join(os.path.dirname(self.path), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nombre del archivo con fecha/hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"inventario_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_name)
            
            # Crear backup
            shutil.copy2(self.path, backup_path)
            
            # Limitar a 10 backups máximo (eliminar los más viejos)
            self._limpiar_backups_antiguos(backup_dir)
            
            print(f"✅ Backup creado: {backup_name}")
            return backup_path
        except Exception as e:
            print(f"❌ Error en backup: {e}")
            return None

    def _limpiar_backups_antiguos(self, backup_dir, max_backups=15):
        """Mantiene solo los últimos backups, elimina los más viejos"""
        try:
            backups = []
            for file in os.listdir(backup_dir):
                if file.startswith("inventario_backup_") and file.endswith(".db"):
                    file_path = os.path.join(backup_dir, file)
                    creation_time = os.path.getctime(file_path)
                    backups.append((file_path, creation_time))
            
            # Ordenar por fecha (más reciente primero)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Eliminar backups excedentes
            for backup_path, _ in backups[max_backups:]:
                try:
                    os.remove(backup_path)
                    print(f"🗑️ Backup antiguo eliminado: {os.path.basename(backup_path)}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar backup: {e}")
                    
        except Exception as e:
            print(f"⚠️ Error limpiando backups antiguos: {e}")

    def add_movimiento(self, mov_data, bienes_ids):
        """Registra un movimiento y actualiza estados Y DATOS DEL RESPONSABLE - VERSIÓN CON TRANSACCIÓN"""
        try:
            # ✅ TRANSACCIÓN ATÓMICA - TODO O NADA
            with self.conn:
                cur = self.conn.cursor()
                
                # Debug: mostrar datos que llegan al movimiento
                print(f"🔄 DEBUG add_movimiento:")
                print(f"   Tipo: {mov_data['tipo']}")
                print(f"   Responsable nombre: '{mov_data.get('responsable_nombre', '')}'")
                print(f"   Responsable apellido: '{mov_data.get('responsable_apellido', '')}'")
                print(f"   Responsable dni_cuit: '{mov_data.get('responsable_dni_cuit', '')}'")
                print(f"   Bienes IDs: {bienes_ids}")
                
                # Insertar movimiento CON DATOS SEPARADOS
                keys = ",".join(mov_data.keys())
                placeholders = ",".join("?" for _ in mov_data)
                cur.execute(f"INSERT INTO movimientos ({keys}) VALUES ({placeholders})", 
                        tuple(mov_data.values()))
                mov_id = cur.lastrowid
                
                # Relacionar bienes con movimiento Y ACTUALIZAR DATOS
                for bien_id in bienes_ids:
                    cur.execute("INSERT INTO bienes_movimientos (id_bien, id_movimiento) VALUES (?, ?)", 
                            (bien_id, mov_id))
                    
                    # Actualizar estado Y DATOS DEL RESPONSABLE del bien
                    tipo_mov = mov_data["tipo"]
                    if tipo_mov == "Entrega":
                        nuevo_estado = "Asignado"
                        # ✅ ACTUALIZAR BIEN CON DATOS SEPARADOS DEL RESPONSABLE
                        cur.execute("""
                            UPDATE bienes SET estado=?, nombre=?, apellido=?, dni_cuit=?, institucional=?
                            WHERE id=?
                        """, (
                            nuevo_estado,
                            mov_data.get("responsable_nombre", ""),
                            mov_data.get("responsable_apellido", ""), 
                            mov_data.get("responsable_dni_cuit", ""),
                            mov_data.get("responsable_institucional", ""),
                            bien_id
                        ))
                        
                        # Debug: verificar la actualización
                        print(f"   ✅ Actualizado bien {bien_id}:")
                        print(f"      Estado: {nuevo_estado}")
                        print(f"      Nombre: '{mov_data.get('responsable_nombre', '')}'")
                        print(f"      Apellido: '{mov_data.get('responsable_apellido', '')}'")
                        print(f"      DNI/CUIT: '{mov_data.get('responsable_dni_cuit', '')}'")
                        
                    elif tipo_mov == "Devolución":
                        nuevo_estado = "En depósito"
                        # ✅ LIMPIAR DATOS DEL RESPONSABLE (devolver a stock)
                        cur.execute("""
                            UPDATE bienes SET estado=?, nombre='', apellido='', dni_cuit='', institucional=''
                            WHERE id=?
                        """, (nuevo_estado, bien_id))
                        print(f"   ✅ Devolución bien {bien_id} - datos limpiados")
                        
                    elif tipo_mov == "Baja":
                        nuevo_estado = "Baja definitiva"
                        cur.execute("UPDATE bienes SET estado=? WHERE id=?", (nuevo_estado, bien_id))
                    else:
                        nuevo_estado = "En depósito"
                        cur.execute("UPDATE bienes SET estado=? WHERE id=?", (nuevo_estado, bien_id))
                    
                print(f"✅ Movimiento {mov_id} guardado correctamente")
                return mov_id
                
        except Exception as e:
            print(f"❌ Error al agregar movimiento: {e}")
            raise e

    def marcar_como_eliminado(self, movimiento_id, motivo, usuario):
        """Marca un movimiento como eliminado (soft delete)"""
        try:
            from datetime import datetime
            
            cur = self.conn.cursor()
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cur.execute("""
                UPDATE movimientos 
                SET eliminado = 1, 
                    fecha_eliminacion = ?, 
                    motivo_eliminacion = ?
                WHERE id = ?
            """, (fecha_actual, motivo, movimiento_id))
            
            self.conn.commit()
            
            # Registrar en logs
            self.log_actividad(
                usuario,
                "ELIMINAR_MOVIMIENTO",
                f"Movimiento #{movimiento_id} marcado como eliminado. Motivo: {motivo}"
            )
            
            cur.close()
            print(f"✅ Movimiento #{movimiento_id} marcado como eliminado")
            return True
            
        except Exception as e:
            print(f"❌ Error marcando movimiento como eliminado: {e}")
            return False

    def list_movimientos(self):
        """Obtiene todos los movimientos"""
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT * FROM movimientos ORDER BY fecha DESC")
            return cur.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Error al listar movimientos: {e}")
            return []
        finally:
            cur.close()

    def get_movimientos_detallados(self, incluir_eliminados=False):
        """Obtiene movimientos con información detallada de bienes"""
        cur = self.conn.cursor()
        try:
            # Construir WHERE según parámetro
            if incluir_eliminados:
                where_clause = ""
            else:
                where_clause = "WHERE m.eliminado = 0"
            
            query = f"""
            SELECT m.*, 
                COUNT(bm.id_bien) as cantidad_bienes,
                GROUP_CONCAT(b.ficha) as fichas,
                GROUP_CONCAT(DISTINCT b.prd) as prds
            FROM movimientos m
            LEFT JOIN bienes_movimientos bm ON m.id = bm.id_movimiento
            LEFT JOIN bienes b ON bm.id_bien = b.id
            {where_clause}
            GROUP BY m.id
            ORDER BY m.fecha DESC
            """
            
            print(f"🔍 Query movimientos: incluir_eliminados={incluir_eliminados}")
            cur.execute(query)
            return cur.fetchall()
            
        except Exception as e:
            print(f"Error al obtener movimientos detallados: {e}")
            return self.list_movimientos()  # Fallback
        finally:
            cur.close()
            
    def obtener_movimientos_eliminados(self):
        """Obtiene solo los movimientos eliminados"""
        cur = self.conn.cursor()
        try:
            query = """
            SELECT m.*, 
                COUNT(bm.id_bien) as cantidad_bienes,
                GROUP_CONCAT(b.ficha) as fichas
            FROM movimientos m
            LEFT JOIN bienes_movimientos bm ON m.id = bm.id_movimiento
            LEFT JOIN bienes b ON bm.id_bien = b.id
            WHERE m.eliminado = 1
            GROUP BY m.id
            ORDER BY m.fecha_eliminacion DESC
            """
            
            cur.execute(query)
            return cur.fetchall()
        except Exception as e:
            print(f"❌ Error obteniendo movimientos eliminados: {e}")
            return []
        finally:
            cur.close()

    def bien_existe(self, ficha, tipo, marca, modelo, serie, imei=""):
        """Verifica si un bien ya existe - VERSIÓN QUE IGNORA 'SIN SERIE'"""
        try:
            cur = self.conn.cursor()
            
            # ✅ NORMALIZAR DATOS
            ficha_clean = str(ficha).strip() if ficha else ""
            tipo_clean = str(tipo).strip().lower() if tipo else ""
            marca_clean = str(marca).strip().lower() if marca else ""
            modelo_clean = str(modelo).strip().lower() if modelo else ""
            serie_clean = str(serie).strip() if serie else ""
            imei_clean = str(imei).strip() if imei else ""
            
            # ✅ VERIFICACIÓN POR PRIORIDAD
            
            # 1. PRIORIDAD MÁXIMA: Misma Ficha (identificador único del sistema)
            if ficha_clean:
                cur.execute("""
                    SELECT id, ficha, tipo, marca, modelo, serie, imei 
                    FROM bienes 
                    WHERE ficha = ? AND ficha != '' AND ficha IS NOT NULL
                """, (ficha_clean,))
                existente = cur.fetchone()
                if existente:
                    print(f"🚨 DUPLICADO POR FICHA: {ficha_clean}")
                    print(f"   Ya existe: {existente['tipo']} - {existente['marca']} {existente['modelo']}")
                    return True
            
            # 2. PRIORIDAD ALTA: Mismo IMEI (no vacío en ambos) - IGNORAR VALORES GENÉRICOS
            if imei_clean and imei_clean.upper() not in ['SIN IMEI', 'NO TIENE', 'N/A', '']:
                cur.execute("""
                    SELECT id, ficha, tipo, marca, modelo, serie, imei 
                    FROM bienes 
                    WHERE imei = ? AND imei != '' AND imei IS NOT NULL
                """, (imei_clean,))
                existente = cur.fetchone()
                if existente:
                    print(f"🚨 DUPLICADO POR IMEI: {imei_clean}")
                    print(f"   Ya existe: Ficha {existente['ficha']} - {existente['marca']} {existente['modelo']}")
                    return True
            
            # 3. PRIORIDAD MEDIA: Misma Serie (no vacía en ambos) - IGNORAR "SIN SERIE"
            if serie_clean and serie_clean.upper() not in ['SIN SERIE', 'SIN_SERIE', 'NO TIENE', 'N/A', '']:
                cur.execute("""
                    SELECT id, ficha, tipo, marca, modelo, serie, imei 
                    FROM bienes 
                    WHERE serie = ? AND serie != '' AND serie IS NOT NULL
                """, (serie_clean,))
                existente = cur.fetchone()
                if existente:
                    print(f"⚠️ DUPLICADO POR SERIE: {serie_clean}")
                    print(f"   Ya existe: Ficha {existente['ficha']} - {existente['marca']} {existente['modelo']}")
                    return True
            
            # 4. PRIORIDAD BAJA: Mismo tipo+marca+modelo SOLO SI NO HAY SERIE/IMEI VÁLIDOS
            # (Para evitar bloquear bienes similares pero con identificadores únicos diferentes)
            if all([tipo_clean, marca_clean, modelo_clean]):
                # Solo considerar duplicado si NO tienen serie/IMEI válidos
                cur.execute("""
                    SELECT id, ficha, tipo, marca, modelo, serie, imei 
                    FROM bienes 
                    WHERE LOWER(tipo) = ? AND LOWER(marca) = ? AND LOWER(modelo) = ?
                    AND (serie = '' OR serie IS NULL OR UPPER(serie) IN ('SIN SERIE', 'SIN_SERIE', 'NO TIENE', 'N/A'))
                    AND (imei = '' OR imei IS NULL OR UPPER(imei) IN ('SIN IMEI', 'NO TIENE', 'N/A'))
                """, (tipo_clean, marca_clean, modelo_clean))
                existente = cur.fetchone()
                if existente:
                    print(f"🔍 DUPLICADO POR TIPO+MARCA+MODELO (sin identificadores únicos):")
                    print(f"   Tipo: {tipo_clean}, Marca: {marca_clean}, Modelo: {modelo_clean}")
                    print(f"   Ya existe: Ficha {existente['ficha']}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error verificando existencia: {e}")
            return False
    
    def obtener_bien_por_id(self, bien_id):
        """Obtiene un bien por su ID - PARA EL GENERADOR DE ACTAS"""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM bienes WHERE id = ?", (bien_id,))
            resultado = cur.fetchone()
            
            if resultado:
                columnas = [desc[0] for desc in cur.description]
                return dict(zip(columnas, resultado))
            return None
        except Exception as e:
            print(f"❌ Error obteniendo bien por ID: {e}")
            return None

    def obtener_movimientos_por_bien(self, bien_id):
        """Obtiene todos los movimientos de un bien específico para el timeline - VERSIÓN CORREGIDA"""
        try:
            cur = self.conn.cursor()
            query = """
                SELECT 
                    m.id,
                    m.tipo,
                    m.fecha,
                    m.responsable,
                    m.responsable_nombre,
                    m.responsable_apellido, 
                    m.responsable_dni_cuit,
                    m.responsable_institucional,
                    m.observaciones,
                    m.archivo_path_pdf,        
                    m.numero_transferencia,
                    b.ficha,
                    b.tipo as tipo_bien,
                    b.marca,
                    b.modelo,
                    b.serie
                FROM movimientos m
                JOIN bienes_movimientos bm ON m.id = bm.id_movimiento
                JOIN bienes b ON bm.id_bien = b.id
                WHERE bm.id_bien = ?
                ORDER BY m.fecha DESC
            """
            cur.execute(query, (bien_id,))
            movimientos = cur.fetchall()
            
            # Convertir a lista de diccionarios
            resultado = []
            for mov in movimientos:
                resultado.append(dict(mov))
            
            cur.close()
            return resultado
            
        except Exception as e:
            print(f"❌ Error obteniendo movimientos del bien {bien_id}: {e}")
            return []
        
    def obtener_movimiento_por_id(self, movimiento_id):
        """Obtiene un movimiento por su ID - VERSIÓN ACTUALIZADA"""
        try:
            cur = self.conn.cursor()
            # ✅ CORREGIDO: Buscar archivo_path_pdf, no archivo_path
            cur.execute("""
                SELECT id, tipo, fecha, responsable, responsable_nombre, 
                    responsable_apellido, responsable_dni_cuit, 
                    responsable_institucional, observaciones, 
                    archivo_path_pdf, archivo_path_docx, 
                    numero_transferencia 
                FROM movimientos 
                WHERE id = ?
            """, (movimiento_id,))
            resultado = cur.fetchone()
            
            if resultado:
                columnas = [desc[0] for desc in cur.description]
                return dict(zip(columnas, resultado))
            return None
        except Exception as e:
            print(f"❌ Error obteniendo movimiento por ID: {e}")
            return None

    def get_estadisticas(self):
        """Obtiene estadísticas del inventario con manejo seguro de cursor"""
        try:
            # ✅ SIN CONTEXT MANAGER - MANUAL
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM bienes")
            total = cur.fetchone()[0]
            # ✅ CORREGIDO: Usar LOWER para agrupar sin importar mayúsculas
            cur.execute("SELECT LOWER(estado), COUNT(*) FROM bienes GROUP BY LOWER(estado)")
            # Convertir las claves a minúsculas para estandarizar
            por_estado_raw = dict(cur.fetchall())
            # ✅ ESTANDARIZAR: Convertir a título (ej: "asignado" → "Asignado")
            por_estado = {k.capitalize() if k else k: v for k, v in por_estado_raw.items()}
            cur.execute("SELECT tipo, COUNT(*) FROM bienes GROUP BY tipo")
            por_tipo = dict(cur.fetchall())
            cur.close()
            return {
                'total': total,
                'por_estado': por_estado,
                'por_tipo': por_tipo
            }
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {'total': 0, 'por_estado': {}, 'por_tipo': {}}
        
    def obtener_valores_unicos(self, campo):
        """
        Obtiene una lista de valores únicos para un campo (ej: institucional, tipo, marca)
        Útil para llenar combos de filtro.
        """
        try:
            cur = self.conn.cursor()
            cur.execute(f"SELECT DISTINCT {campo} FROM bienes WHERE {campo} IS NOT NULL AND {campo} != '' ORDER BY {campo}")
            resultados = cur.fetchall()
            cur.close()
            # Devolver solo los valores, sin None ni vacíos
            return [r[0] for r in resultados if r[0]]
        except Exception as e:
            print(f"Error obteniendo valores únicos de '{campo}': {e}")
            return []

    def get_estadisticas_filtradas(self, institucional=None, tipo=None, marca=None, estado=None):
        """
        Devuelve estadísticas filtradas por institucional, tipo, marca, estado
        """
        try:
            cur = self.conn.cursor()
            # Construir WHERE dinámicamente
            condiciones = []
            params = []

            if institucional:
                condiciones.append("institucional = ?")
                params.append(institucional)
            if tipo:
                condiciones.append("tipo = ?")
                params.append(tipo)
            if marca:
                condiciones.append("marca = ?")
                params.append(marca)
            if estado:
                condiciones.append("estado = ?")
                params.append(estado)

            where_clause = " WHERE " + " AND ".join(condiciones) if condiciones else ""

            # Consulta principal
            cur.execute(f"SELECT COUNT(*) FROM bienes {where_clause}", params)
            total = cur.fetchone()[0]

            cur.execute(f"SELECT estado, COUNT(*) FROM bienes {where_clause} GROUP BY estado", params)
            por_estado = dict(cur.fetchall())

            cur.execute(f"SELECT tipo, COUNT(*) FROM bienes {where_clause} GROUP BY tipo", params)
            por_tipo = dict(cur.fetchall())

            cur.execute(f"SELECT marca, COUNT(*) FROM bienes {where_clause} GROUP BY marca", params)
            por_marca = dict(cur.fetchall())

            cur.execute(f"SELECT institucional, COUNT(*) FROM bienes {where_clause} GROUP BY institucional", params)
            por_institucional = dict(cur.fetchall())

            cur.close()

            return {
                'total': total,
                'por_estado': por_estado,
                'por_tipo': por_tipo,
                'por_marca': por_marca,
                'por_institucional': por_institucional
            }
        except Exception as e:
            print(f"Error obteniendo estadísticas filtradas: {e}")
            return {'total': 0, 'por_estado': {}, 'por_tipo': {}, 'por_marca': {}, 'por_institucional': {}}
        
    def fetch_one(self, query, params=()):
        """Ejecuta query y retorna una sola fila - PARA LOGIN"""
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            result = cur.fetchone()
            cur.close()
            return result
        except Exception as e:
            print(f"Error en fetch_one: {e}")
            return None
        
    def obtener_bien_por_ficha(self, ficha):
        """Obtiene un bien por su número de ficha"""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM bienes WHERE ficha = ?", (ficha,))
            resultado = cur.fetchone()
            
            if resultado:
                columnas = [desc[0] for desc in cur.description]
                return dict(zip(columnas, resultado))
            return None
        except Exception as e:
            print(f"❌ Error obteniendo bien por ficha: {e}")
            return None
    
    def buscar_bienes_filtrados(self, filtros):
        """Query SQL optimizada con WHERE dinámico - REEMPLAZA filtro manual"""
        
        condiciones = []
        params = []
        
        # CONSTRUIR FILTROS DINÁMICAMENTE
        if filtros.get('tipo'):
            condiciones.append("tipo = ?")
            params.append(filtros['tipo'])
        
        if filtros.get('estado'):
            condiciones.append("estado = ?")
            params.append(filtros['estado'])
        
        if filtros.get('prd'):
            condiciones.append("prd LIKE ?")
            params.append(f"%{filtros['prd']}%")
        
        if filtros.get('marca'):
            condiciones.append("marca LIKE ?")
            params.append(f"%{filtros['marca']}%")
        
        if filtros.get('modelo'):
            condiciones.append("modelo LIKE ?")
            params.append(f"%{filtros['modelo']}%")
        
        if filtros.get('serie'):
            condiciones.append("serie LIKE ?")
            params.append(f"%{filtros['serie']}%")
        
        if filtros.get('imei'):
            condiciones.append("imei LIKE ?")
            params.append(f"%{filtros['imei']}%")
        
        if filtros.get('linea'):
            condiciones.append("linea LIKE ?")
            params.append(f"%{filtros['linea']}%")
        
        if filtros.get('sim'):
            condiciones.append("sim LIKE ?")
            params.append(f"%{filtros['sim']}%")
        
        if filtros.get('empresa'):
            condiciones.append("empresa = ?")
            params.append(filtros['empresa'])
        
        if filtros.get('nombre'):
            condiciones.append("nombre LIKE ?")
            params.append(f"%{filtros['nombre']}%")
        
        if filtros.get('apellido'):
            condiciones.append("apellido LIKE ?")
            params.append(f"%{filtros['apellido']}%")
        
        if filtros.get('dni_cuit'):
            condiciones.append("dni_cuit LIKE ?")
            params.append(f"%{filtros['dni_cuit']}%")
        
        if filtros.get('institucional'):
            condiciones.append("institucional LIKE ?")
            params.append(f"%{filtros['institucional']}%")
        
        if filtros.get('descripcion'):
            condiciones.append("descripcion LIKE ?")
            params.append(f"%{filtros['descripcion']}%")
        
        if filtros.get('anio_prd'):
            condiciones.append("anio_prd = ?")
            params.append(filtros['anio_prd'])
        
        # FILTROS DE RANGO (ficha)
        if filtros.get('ficha_desde'):
            try:
                condiciones.append("CAST(ficha AS INTEGER) >= ?")
                params.append(int(filtros['ficha_desde']))
            except (ValueError, TypeError):
                pass  # Ignorar si no es número
        
        if filtros.get('ficha_hasta'):
            try:
                condiciones.append("CAST(ficha AS INTEGER) <= ?")
                params.append(int(filtros['ficha_hasta']))
            except (ValueError, TypeError):
                pass  # Ignorar si no es número
        
        # FILTROS DE RANGO (monto)
        if filtros.get('monto_desde'):
            try:
                condiciones.append("CAST(monto_original AS REAL) >= ?")
                params.append(float(filtros['monto_desde']))
            except (ValueError, TypeError):
                pass
        
        if filtros.get('monto_hasta'):
            try:
                condiciones.append("CAST(monto_original AS REAL) <= ?")
                params.append(float(filtros['monto_hasta']))
            except (ValueError, TypeError):
                pass
        
        # CONSTRUIR QUERY FINAL
        where_clause = " AND ".join(condiciones) if condiciones else "1=1"
        
        query = f"""
            SELECT id, ficha, tipo, marca, modelo, serie, estado, prd,
                nombre, apellido, dni_cuit, institucional,
                linea, sim, empresa, imei, descripcion, fecha_registro,
                monto_original, anio_prd
            FROM bienes 
            WHERE {where_clause}
            ORDER BY fecha_registro DESC
            LIMIT 1000  -- ✅ LÍMITE POR SEGURIDAD
        """
        
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            resultado = cur.fetchall()
            cur.close()
            
            print(f"✅ Query optimizada: {len(resultado)} resultados en {len(condiciones)} filtros")
            return resultado
            
        except Exception as e:
            print(f"❌ Error en query optimizada: {e}")
            # Fallback a búsqueda básica
            return self.list_bienes()
        
    def actualizar_pdf_movimiento(self, movimiento_id, ruta_pdf):
        """Actualiza la ruta del PDF de un movimiento existente - VERSIÓN CORREGIDA"""
        try:
            import os
            from config.settings import get_config
            
            print(f"🔍 DEBUG actualizar_pdf_movimiento:")
            print(f"   Ruta PDF recibida: {ruta_pdf}")
            print(f"   ¿Es ruta absoluta?: {os.path.isabs(ruta_pdf) if ruta_pdf else 'No ruta'}")
            
            # ✅ SI la ruta es solo nombre de archivo, convertir a ruta completa
            if ruta_pdf and not os.path.isabs(ruta_pdf):
                config = get_config()
                ruta_completa = os.path.join(config["actas_folder_local"], ruta_pdf)
                print(f"   Convirtiendo a ruta completa: {ruta_completa}")
                ruta_pdf = ruta_completa
            
            print(f"   Guardando en BD: {ruta_pdf}")
            
            query = "UPDATE movimientos SET archivo_path_pdf = ? WHERE id = ?"
            self.conn.execute(query, (ruta_pdf, movimiento_id))
            self.conn.commit()
            
            print(f"✅ PDF actualizado en BD para movimiento {movimiento_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando PDF del movimiento: {e}")
            return False
        
    def get_bienes_de_movimiento(self, movimiento_id):
        """Obtiene los bienes asociados a un movimiento"""
        try:
            cur = self.conn.cursor()
            cur.execute("""
                SELECT b.* FROM bienes b
                JOIN bienes_movimientos bm ON b.id = bm.id_bien
                WHERE bm.id_movimiento = ?
            """, (movimiento_id,))
            rows = cur.fetchall()
            if rows:
                columns = [description[0] for description in cur.description]
                bienes = [dict(zip(columns, row)) for row in rows]
                cur.close()
                return bienes
            else:
                cur.close()
                return []
        except Exception as e:
            print(f"❌ Error obteniendo bienes del movimiento: {e}")
            return []