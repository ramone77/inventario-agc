"""
🏗️ GESTOR DE BIENES - Sistema de Inventario AGC
Lógica de negocio para gestión de bienes
"""

from database.db_manager import DB

class BienManager:
    """Maneja la lógica de negocio para bienes"""
    
    def __init__(self, db: DB):
        self.db = db

    # ✅ AGREGAR AQUÍ LA NUEVA FUNCIÓN
    def _limpiar_valor_numerico(self, valor):
        """Limpia .0 de valores que deberían ser strings numéricos"""
        if valor is None:
            return ""
        valor_str = str(valor)
        # Solo quitar .0 si es exactamente un decimal cero
        if valor_str.endswith('.0'):
            return valor_str[:-2]
        return valor_str
    
    def crear_bien(self, datos_bien):
        """Crea un nuevo bien con validaciones"""
        return self.db.add_bien(datos_bien)
    
    def buscar_bienes(self, filtros=None):
        """Busca bienes con filtros avanzados - VERSIÓN CORREGIDA"""
        try:
            if not filtros:
                return self.db.list_bienes()  # Con límite para rendimiento normal
                
            print(f"🔍 Aplicando filtros en BienManager: {filtros}")
            
            # ✅ CORRECCIÓN: Usar list_bienes_completos para filtros
            bienes = self.db.list_bienes_completos()  # ¡SIN LÍMITE!
            bienes_filtrados = self._aplicar_filtros_manual(bienes, filtros)
            
            print(f"✅ Filtros aplicados: {len(bienes_filtrados)} de {len(bienes)} registros")
            return bienes_filtrados
            
        except Exception as e:
            print(f"❌ Error en buscar_bienes: {e}")
            return self.db.list_bienes()

    def list_bienes_completos(self):
    #Obtiene TODOS los bienes sin límite - PARA FILTROS"""
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

    def _aplicar_filtros_manual(self, bienes, filtros):
        """Aplica TODOS los filtros manualmente - VERSIÓN CON LIMPIEZA"""
        if not filtros or not bienes:
            return bienes
            
        resultados = []
        
        print(f"🔍 Aplicando {len(filtros)} filtros sobre {len(bienes)} bienes")
        
        for bien in bienes:
            cumple_filtros = True
            
            # Convertir a dict de manera segura
            try:
                if hasattr(bien, 'keys'):
                    bien_dict = dict(bien)
                else:
                    bien_dict = bien
            except:
                bien_dict = {}
            
            # ✅ FILTROS DE TEXTO - MÁS FLEXIBLES
            if 'prd' in filtros and filtros['prd']:
                prd_bien = str(bien_dict.get('prd', '')).lower()
                if filtros['prd'].lower() not in prd_bien:
                    cumple_filtros = False
                    continue
                    
            # ✅ 2. FILTRO POR TIPO
            if 'tipo' in filtros and filtros['tipo']:
                tipo_bien = str(bien_dict.get('tipo', '')).strip().lower()  # ← a minúsculas
                filtro_tipo = filtros['tipo'].strip().lower()  # ← a minúsculas
                
                if tipo_bien != filtro_tipo:
                    cumple_filtros = False
                    continue
                    
            # ✅ 3. FILTRO POR FICHA (RANGO)
            if 'ficha_desde' in filtros and filtros['ficha_desde']:
                try:
                    ficha_bien = int(bien_dict.get('ficha', 0))
                    ficha_desde = int(filtros['ficha_desde'])
                    if ficha_bien < ficha_desde:
                        cumple_filtros = False
                        continue
                except (ValueError, TypeError):
                    pass  # Si no es número, ignorar filtro
                    
            if 'ficha_hasta' in filtros and filtros['ficha_hasta']:
                try:
                    ficha_bien = int(bien_dict.get('ficha', 0))
                    ficha_hasta = int(filtros['ficha_hasta'])
                    if ficha_bien > ficha_hasta:
                        cumple_filtros = False
                        continue
                except (ValueError, TypeError):
                    pass  # Si no es número, ignorar filtro

            # ✅ 4. FILTRO POR ESTADO - CASE INSENSITIVE
            if 'estado' in filtros and filtros['estado']:
                estado_bien = str(bien_dict.get('estado', '')).strip().lower()
                filtro_estado = filtros['estado'].strip().lower()
                
                if estado_bien != filtro_estado:
                    cumple_filtros = False
                    continue
            
            # ✅ 5. FILTRO POR MARCA
            if 'marca' in filtros and filtros['marca']:
                marca_bien = str(bien_dict.get('marca', '')).lower()
                if filtros['marca'].lower() not in marca_bien:
                    cumple_filtros = False
                    continue
            
            # ✅ 6. FILTRO POR MODELO
            if 'modelo' in filtros and filtros['modelo']:
                modelo_bien = str(bien_dict.get('modelo', '')).lower()
                if filtros['modelo'].lower() not in modelo_bien:
                    cumple_filtros = False
                    continue
            
            # ✅ 7. FILTRO POR SERIE
            if 'serie' in filtros and filtros['serie']:
                serie_bien = self._limpiar_valor_numerico(bien_dict.get('serie', ''))  # ← LIMPIADO
                if filtros['serie'].lower() not in serie_bien.lower():
                    cumple_filtros = False
                    continue
            
            # ✅ 8. FILTRO POR IMEI
            if 'imei' in filtros and filtros['imei']:
                imei_bien = self._limpiar_valor_numerico(bien_dict.get('imei', ''))  # ← LIMPIADO
                if filtros['imei'].lower() not in imei_bien.lower():
                    cumple_filtros = False
                    continue
            
            # ✅ 9. FILTRO POR LÍNEA
            if 'linea' in filtros and filtros['linea']:
                linea_bien = self._limpiar_valor_numerico(bien_dict.get('linea', ''))  # ← LIMPIADO
                if filtros['linea'].lower() not in linea_bien.lower():
                    cumple_filtros = False
                    continue
            
            # ✅ 10. FILTRO POR SIM
            if 'sim' in filtros and filtros['sim']:
                sim_bien = self._limpiar_valor_numerico(bien_dict.get('sim', ''))  # ← LIMPIADO
                if filtros['sim'].lower() not in sim_bien.lower():
                    cumple_filtros = False
                    continue
            
            # ✅ 11. FILTRO POR EMPRESA - CASE INSENSITIVE
            if 'empresa' in filtros and filtros['empresa']:
                empresa_bien = str(bien_dict.get('empresa', '')).strip().lower()
                filtro_empresa = filtros['empresa'].strip().lower()
                
                if empresa_bien != filtro_empresa:
                    cumple_filtros = False
                    continue
            
            if 'nombre' in filtros and filtros['nombre']:
                nombre_bien = str(bien_dict.get('nombre', '')).lower()
                if filtros['nombre'].lower() not in nombre_bien:
                    cumple_filtros = False
                    continue
                    
            # ✅ 13. FILTRO POR APELLIDO
            if 'apellido' in filtros and filtros['apellido']:
                apellido_bien = str(bien_dict.get('apellido', '')).lower()
                if filtros['apellido'].lower() not in apellido_bien:
                    cumple_filtros = False
                    continue
            
            # ✅ 14. FILTRO POR DNI/CUIT
            if 'dni_cuit' in filtros and filtros['dni_cuit']:
                dni_bien = self._limpiar_valor_numerico(bien_dict.get('dni_cuit', ''))  # ← LIMPIADO
                if filtros['dni_cuit'].lower() not in dni_bien.lower():
                    cumple_filtros = False
                    continue
            
            # ✅ FILTRO POR INSTITUCIONAL - BÚSQUEDA PARCIAL MEJORADA
            if 'institucional' in filtros and filtros['institucional']:
                institucional_bien = str(bien_dict.get('institucional', '')).lower()
                filtro_institucional = filtros['institucional'].lower()
                
                # Normalizar: quitar "DE", comillas y espacios extra
                institucional_clean = institucional_bien.replace('"', '').replace(' de ', ' ').replace('  ', ' ')
                filtro_clean = filtro_institucional.replace('"', '').replace(' de ', ' ').replace('  ', ' ')
                
                # Buscar si el filtro está contenido en el valor (sin "DE")
                if filtro_clean not in institucional_clean:
                    cumple_filtros = False
                    continue
            
            # ✅ 16. FILTRO POR MONTO (RANGO)
            if 'monto_desde' in filtros and filtros['monto_desde']:
                try:
                    monto_bien = float(bien_dict.get('monto_original', 0))
                    monto_desde = float(filtros['monto_desde'])
                    if monto_bien < monto_desde:
                        cumple_filtros = False
                        continue
                except (ValueError, TypeError):
                    pass  # Si no es número, ignorar filtro
                    
            if 'monto_hasta' in filtros and filtros['monto_hasta']:
                try:
                    monto_bien = float(bien_dict.get('monto_original', 0))
                    monto_hasta = float(filtros['monto_hasta'])
                    if monto_bien > monto_hasta:
                        cumple_filtros = False
                        continue
                except (ValueError, TypeError):
                    pass  # Si no es número, ignorar filtro
            
            # ✅ 17. FILTRO POR AÑO PRD
            if 'anio_prd' in filtros and filtros['anio_prd']:
                anio_bien = str(bien_dict.get('anio_prd', ''))
                if filtros['anio_prd'] not in anio_bien:
                    cumple_filtros = False
                    continue
            
            # ✅ 18. FILTRO POR DESCRIPCIÓN
            if 'descripcion' in filtros and filtros['descripcion']:
                descripcion_bien = str(bien_dict.get('descripcion', '')).lower()
                if filtros['descripcion'].lower() not in descripcion_bien:
                    cumple_filtros = False
                    continue
            
            # Si pasa TODOS los filtros, agregar a resultados
            if cumple_filtros:
                resultados.append(bien)
        
        print(f"✅ Filtrado completado: {len(resultados)} de {len(bienes)} bienes coinciden")
        return resultados
    
    def obtener_estadisticas(self):
        """Obtiene estadísticas de bienes"""
        return self.db.get_estadisticas()