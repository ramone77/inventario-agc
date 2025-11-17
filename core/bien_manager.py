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
        """Limpia .0 de valores que deberían ser strings numéricos - VERSIÓN MEJORADA"""
        if valor is None:
            return ""
        
        valor_str = str(valor)
        
        # Quitar .0 al final y también convertir números científicos
        if valor_str.endswith('.0'):
            return valor_str[:-2]
        elif '.' in valor_str and valor_str.split('.')[1] == '0':
            return valor_str.split('.')[0]
        else:
            return valor_str

    def _normalizar_texto(self, texto):
        """Normaliza texto quitando acentos y convirtiendo a minúsculas"""
        if texto is None:
            return ""
        
        # Convertir a string y minúsculas
        texto = str(texto).lower()
        
        # Reemplazar caracteres con acento
        reemplazos = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u',
            'à': 'a', 'è': 'e', 'ì': 'i', 'ò': 'o', 'ù': 'u',
            'ä': 'a', 'ë': 'e', 'ï': 'i', 'ö': 'o',
            'â': 'a', 'ê': 'e', 'î': 'i', 'ô': 'o', 'û': 'u',
            'ã': 'a', 'ñ': 'n', 'ç': 'c',
            'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u', 'Ü': 'u',
            'À': 'a', 'È': 'e', 'Ì': 'i', 'Ò': 'o', 'Ù': 'u',
            'Ä': 'a', 'Ë': 'e', 'Ï': 'i', 'Ö': 'o',
            'Â': 'a', 'Ê': 'e', 'Î': 'i', 'Ô': 'o', 'Û': 'u',
            'Ã': 'a', 'Ñ': 'n', 'Ç': 'c'
        }
        
        for acento, normal in reemplazos.items():
            texto = texto.replace(acento, normal)
        
        return texto
    
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
            
            # ✅ FILTRO POR MARCA - SIN ACENTOS
            if 'marca' in filtros and filtros['marca']:
                marca_bien = self._normalizar_texto(bien_dict.get('marca', ''))
                filtro_marca = self._normalizar_texto(filtros['marca'])
                
                if filtro_marca not in marca_bien:
                    cumple_filtros = False
                    continue

            
            # ✅ FILTRO POR MODELO - SIN ACENTOS
            if 'modelo' in filtros and filtros['modelo']:
                modelo_bien = self._normalizar_texto(bien_dict.get('modelo', ''))
                filtro_modelo = self._normalizar_texto(filtros['modelo'])
                
                if filtro_modelo not in modelo_bien:
                    cumple_filtros = False
                    continue
            
            # ✅ 7. FILTRO POR SERIE
            if 'serie' in filtros and filtros['serie']:
                serie_bien = self._limpiar_valor_numerico(bien_dict.get('serie', ''))  # ← LIMPIADO
                if filtros['serie'].lower() not in serie_bien.lower():
                    cumple_filtros = False
                    continue
            
            # ✅ FILTRO POR IMEI - DEBE USAR _limpiar_valor_numerico
            if 'imei' in filtros and filtros['imei']:
                imei_bien = self._limpiar_valor_numerico(bien_dict.get('imei', ''))  # ← DEBE ESTAR ESTO
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
            
            # ✅ FILTRO POR NOMBRE - SIN ACENTOS
            if 'nombre' in filtros and filtros['nombre']:
                nombre_bien = self._normalizar_texto(bien_dict.get('nombre', ''))
                filtro_nombre = self._normalizar_texto(filtros['nombre'])
                
                if filtro_nombre not in nombre_bien:
                    cumple_filtros = False
                    continue
                    
            # ✅ FILTRO POR APELLIDO - SIN ACENTOS  
            if 'apellido' in filtros and filtros['apellido']:
                apellido_bien = self._normalizar_texto(bien_dict.get('apellido', ''))
                filtro_apellido = self._normalizar_texto(filtros['apellido'])
                
                if filtro_apellido not in apellido_bien:
                    cumple_filtros = False
                    continue
            
            # ✅ 14. FILTRO POR DNI/CUIT
            if 'dni_cuit' in filtros and filtros['dni_cuit']:
                dni_bien = self._limpiar_valor_numerico(bien_dict.get('dni_cuit', ''))  # ← LIMPIADO
                if filtros['dni_cuit'].lower() not in dni_bien.lower():
                    cumple_filtros = False
                    continue
            
            # ✅ FILTRO POR INSTITUCIONAL - SIN ACENTOS + BÚSQUEDA INTELIGENTE
            if 'institucional' in filtros and filtros['institucional']:
                institucional_bien = self._normalizar_texto(bien_dict.get('institucional', ''))
                filtro_institucional = self._normalizar_texto(filtros['institucional'])
                
                # Normalizar: quitar "DE", comillas y espacios extra (EN TEXTO NORMALIZADO)
                institucional_clean = institucional_bien.replace('"', '').replace(' de ', ' ').replace('  ', ' ')
                filtro_clean = filtro_institucional.replace('"', '').replace(' de ', ' ').replace('  ', ' ')
                
                # Buscar si el filtro está contenido en el valor (sin "DE" y sin acentos)
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
            
            # ✅ 17. FILTRO POR AÑO PRD - COMPARACIÓN EXACTA MEJORADA
            if 'anio_prd' in filtros and filtros['anio_prd']:
                anio_bien = str(bien_dict.get('anio_prd', '')).strip().replace(' ', '')
                filtro_anio = filtros['anio_prd'].strip().replace(' ', '')
                
                if anio_bien != filtro_anio:
                    cumple_filtros = False
                    continue
            
            # ✅ FILTRO POR DESCRIPCIÓN - SIN ACENTOS
            if 'descripcion' in filtros and filtros['descripcion']:
                descripcion_bien = self._normalizar_texto(bien_dict.get('descripcion', ''))
                filtro_descripcion = self._normalizar_texto(filtros['descripcion'])
                
                if filtro_descripcion not in descripcion_bien:
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