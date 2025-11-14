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
        """Cambia automáticamente a modo local"""
        print("🔄 Cambiando a MODO LOCAL...")
        
        # Importar aquí para evitar circular imports
        from ..config.config_manager import cargar_configuracion, guardar_configuracion
        
        # Cargar configuración actual
        config_actual = cargar_configuracion()
        
        # Cambiar a modo local
        config_actual["modo_local"] = True
        guardar_configuracion(config_actual)
        
        print("✅ Cambiado a MODO LOCAL. Reiniciando aplicación...")
        
        # Reiniciar aplicación
        QApplication.quit()
        os.execl(sys.executable, sys.executable, *sys.argv)

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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nombre TEXT,
                password TEXT,
                rol TEXT,
                activo INTEGER DEFAULT 1
            )
        """)
        print("✅ Tabla 'usuarios' verificada")
        
        # Insertar usuario de prueba si no existe
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE id = 'mario'")
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO usuarios (id, nombre, password, rol) VALUES (?, ?, ?, ?)",
                ("mario", "Mario Admin", "1234", "admin")
            )
            print("✅ Usuario de prueba 'mario' creado")
        
 # ✅ NUEVA LÍNEA: Verificar y agregar columnas de asignación
        self.verificar_y_agregar_columnas_asignacion()
        
        # SEGUNDO: Agregar columnas faltantes si es necesario
        self._agregar_columnas_faltantes()
        
        # TERCERO: Crear tabla movimientos MEJORADA
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
                archivo_path TEXT,
                numero_transferencia TEXT
            )
        """)
        print("✅ Tabla 'movimientos' mejorada")
        
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
        cur = self.conn.cursor()
        
        # Lista de columnas nuevas para movimientos
        columnas_nuevas = [
            'responsable_nombre', 'responsable_apellido', 
            'responsable_dni_cuit', 'responsable_institucional'
        ]
        
        # Verificar qué columnas existen
        cur.execute("PRAGMA table_info(movimientos)")
        columnas_existentes = [col[1] for col in cur.fetchall()]
        
        # Agregar columnas faltantes
        for columna in columnas_nuevas:
            if columna not in columnas_existentes:
                try:
                    cur.execute(f"ALTER TABLE movimientos ADD COLUMN {columna} TEXT")
                    print(f"✅ Columna '{columna}' agregada a movimientos")
                except sqlite3.OperationalError as e:
                    print(f"⚠️  No se pudo agregar columna '{columna}': {e}")
        
        cur.close()

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

    def get_movimientos_detallados(self):
        """Obtiene movimientos con información detallada de bienes"""
        cur = self.conn.cursor()
        try:
            query = """
            SELECT m.*, 
                   COUNT(bm.id_bien) as cantidad_bienes,
                   GROUP_CONCAT(b.ficha) as fichas,
                   GROUP_CONCAT(DISTINCT b.prd) as prds
            FROM movimientos m
            LEFT JOIN bienes_movimientos bm ON m.id = bm.id_movimiento
            LEFT JOIN bienes b ON bm.id_bien = b.id
            GROUP BY m.id
            ORDER BY m.fecha DESC
            """
            cur.execute(query)
            return cur.fetchall()
        except Exception as e:
            print(f"Error al obtener movimientos detallados: {e}")
            return self.list_movimientos()  # Fallback a la función básica
        finally:
            cur.close()

    def bien_existe(self, ficha, tipo, serie):
        """Verifica si un bien ya existe con manejo seguro de cursor"""
        try:
            # ✅ SIN CONTEXT MANAGER - MANUAL
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(*) FROM bienes WHERE ficha=? AND tipo=? AND serie=?", 
                    (ficha, tipo, serie))
            resultado = cur.fetchone()[0] > 0
            cur.close()
            return resultado
        except Exception as e:
            print(f"Error verificando existencia: {e}")
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
        """Obtiene todos los movimientos de un bien específico para el timeline"""
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
                    m.archivo_path,
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
        """Obtiene un movimiento por su ID"""
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT * FROM movimientos WHERE id = ?", (movimiento_id,))
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
            
            cur.execute("SELECT estado, COUNT(*) FROM bienes GROUP BY estado")
            por_estado = dict(cur.fetchall())
            
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