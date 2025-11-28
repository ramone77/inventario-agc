"""
🎨 PANEL DE FILTROS AVANZADOS - Sistema de Inventario AGC
Panel de filtros visibles y organizados - VERSIÓN COMPLETA
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QGroupBox, QFormLayout,
                             QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from database.db_manager import DB  # ✅ NUEVO IMPORT

class PanelFiltrosAvanzados(QWidget):
    """Panel de filtros visibles - DISEÑO COMPACTO HORIZONTAL"""
    
    # Señal personalizada para cuando se aplican filtros
    filtros_aplicados = pyqtSignal(dict)
    
    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.db = db
        print(f"🔍 DEBUG PanelFiltros: BD recibida = {self.db is not None}")
        
        self._setup_ui()
        
        if self.db:
            print("🔍 DEBUG: Llamando a actualizar_tipos_dinamicos...")
            self.actualizar_tipos_dinamicos()
        else:
            print("❌ DEBUG: No hay BD para actualizar tipos")
    
    def _setup_ui(self):
        """Configura la interfaz del panel de filtros - DISEÑO HORIZONTAL COMPACTO"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # ===== TÍTULO PRINCIPAL =====
        titulo_layout = QHBoxLayout()
        titulo = QLabel("🔍 FILTROS AVANZADOS")
        titulo.setStyleSheet("""
            QLabel {
                font-weight: bold; 
                font-size: 14px; 
                color: #2c3e50;
                padding: 5px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        titulo_layout.addWidget(titulo)
        titulo_layout.addStretch()
        layout.addLayout(titulo_layout)

        # ===== FILA SUPERIOR: FILTROS RÁPIDOS + DATOS PERSONALES =====
        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(15)
        
        # Grupo: FILTROS RÁPIDOS
        grupo_rapidos = QGroupBox("░░░ FILTROS RÁPIDOS ░░░")
        grupo_rapidos.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; font-size: 11px; }")
        form_rapidos = QFormLayout(grupo_rapidos)
        form_rapidos.setHorizontalSpacing(8)
        form_rapidos.setVerticalSpacing(4)
        
        self.filtro_prd = QLineEdit()
        self.filtro_prd.setPlaceholderText("PRD...")
        self.filtro_prd.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_tipo = QComboBox()
        #self.filtro_tipo.addItems(["", "Oficina", "Cocina", "Laboratorio", "Celular", "Tablet", "Otro"])
        self.filtro_tipo.currentTextChanged.connect(self._aplicar_automaticamente)
        
        fila_ficha = QHBoxLayout()
        self.filtro_ficha_desde = QLineEdit()
        self.filtro_ficha_desde.setPlaceholderText("Desde")
        self.filtro_ficha_desde.setValidator(QIntValidator(0, 99999999))
        self.filtro_ficha_desde.setMaximumWidth(100)
        self.filtro_ficha_desde.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_ficha_hasta = QLineEdit()
        self.filtro_ficha_hasta.setPlaceholderText("Hasta")
        self.filtro_ficha_hasta.setValidator(QIntValidator(0, 99999999))
        self.filtro_ficha_hasta.setMaximumWidth(100)
        self.filtro_ficha_hasta.textChanged.connect(self._aplicar_automaticamente)
        
        fila_ficha.addWidget(self.filtro_ficha_desde)
        fila_ficha.addWidget(QLabel("     a     "))
        fila_ficha.addWidget(self.filtro_ficha_hasta)
        fila_ficha.addStretch()
        
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["", "En depósito", "Asignado", "En reparación", "Baja definitiva"])
        self.filtro_estado.currentTextChanged.connect(self._aplicar_automaticamente)
        
        form_rapidos.addRow("PRD:", self.filtro_prd)
        form_rapidos.addRow("Tipo:", self.filtro_tipo)
        form_rapidos.addRow("Ficha:", fila_ficha)
        form_rapidos.addRow("Estado:", self.filtro_estado)
        
        # Grupo: DATOS PERSONALES
        grupo_personales = QGroupBox("░░░ DATOS PERSONALES ░░░")
        grupo_personales.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; font-size: 11px; }")
        form_personales = QFormLayout(grupo_personales)
        form_personales.setHorizontalSpacing(8)
        form_personales.setVerticalSpacing(4)
        
        self.filtro_nombre = QLineEdit()
        self.filtro_nombre.setPlaceholderText("Nombre...")
        self.filtro_nombre.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_apellido = QLineEdit()
        self.filtro_apellido.setPlaceholderText("Apellido...")
        self.filtro_apellido.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_dni_cuit = QLineEdit()
        self.filtro_dni_cuit.setPlaceholderText("DNI/CUIT...")
        self.filtro_dni_cuit.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_institucional = QComboBox()
        self.filtro_institucional.addItems([
            "", "AGENCIA GUBERNAMENTAL DE CONTROL", "UNIDAD OPERATIVA PLANIFICACION Y COORDINACION DE GESTION",
            "DIRECCION EJECUTIVA", "GERENCIA OPERATIVA ESTRATEGIA COMUNICACIONAL", 
            "DIRECCION GENERAL HABILITACIONES Y PERMISOS", "DIRECCION GENERAL DE FISCALIZACION Y CONTROL",
            "DIRECCION GENERAL FISCALIZACION Y CONTROL DE OBRAS", "DIRECCION GENERAL HIGIENE Y SEGURIDAD ALIMENTARIA",
            "DIRECCION GENERAL LEGAL Y TECNICA", "UNIDAD DE AUDITORIA INTERNA",
            "UNION OPERATIVA DE FISCALIZACION INTEGRAL", "UNIDAD DE COORDINACION ADMINISTRATIVA"
        ])
        self.filtro_institucional.currentTextChanged.connect(self._aplicar_automaticamente)
        
        form_personales.addRow("Nombre:", self.filtro_nombre)
        form_personales.addRow("Apellido:", self.filtro_apellido)
        form_personales.addRow("DNI/CUIT:", self.filtro_dni_cuit)
        form_personales.addRow("Institucional:", self.filtro_institucional)
        
        fila_superior.addWidget(grupo_rapidos)
        fila_superior.addWidget(grupo_personales)
        
        # ===== FILA INFERIOR: DATOS TÉCNICOS + OTROS FILTROS =====
        fila_inferior = QHBoxLayout()
        fila_inferior.setSpacing(15)
        
        # Grupo: DATOS TÉCNICOS
        grupo_tecnicos = QGroupBox("░░░ DATOS TÉCNICOS ░░░")
        grupo_tecnicos.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; font-size: 11px; }")
        form_tecnicos = QFormLayout(grupo_tecnicos)
        form_tecnicos.setHorizontalSpacing(8)
        form_tecnicos.setVerticalSpacing(4)
        
        fila_tecnica1 = QHBoxLayout()
        self.filtro_marca = QLineEdit()
        self.filtro_marca.setPlaceholderText("Marca...")
        self.filtro_marca.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_modelo = QLineEdit()
        self.filtro_modelo.setPlaceholderText("Modelo...")
        self.filtro_modelo.textChanged.connect(self._aplicar_automaticamente)
        
        fila_tecnica1.addWidget(self.filtro_marca)
        fila_tecnica1.addWidget(QLabel("/"))
        fila_tecnica1.addWidget(self.filtro_modelo)
        
        fila_tecnica2 = QHBoxLayout()
        self.filtro_serie = QLineEdit()
        self.filtro_serie.setPlaceholderText("Serie...")
        self.filtro_serie.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_imei = QLineEdit()
        self.filtro_imei.setPlaceholderText("IMEI...")
        self.filtro_imei.textChanged.connect(self._aplicar_automaticamente)
        
        fila_tecnica2.addWidget(self.filtro_serie)
        fila_tecnica2.addWidget(QLabel("/"))
        fila_tecnica2.addWidget(self.filtro_imei)
        
        fila_tecnica3 = QHBoxLayout()
        self.filtro_linea = QLineEdit()
        self.filtro_linea.setPlaceholderText("Línea...")
        self.filtro_linea.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_sim = QLineEdit()
        self.filtro_sim.setPlaceholderText("SIM...")
        self.filtro_sim.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_empresa = QComboBox()
        self.filtro_empresa.addItems(["", "Personal", "Claro", "Movistar", "Tuenti", "Otro"])
        self.filtro_empresa.setMaximumWidth(100)
        self.filtro_empresa.currentTextChanged.connect(self._aplicar_automaticamente)
        
        fila_tecnica3.addWidget(self.filtro_linea)
        fila_tecnica3.addWidget(QLabel("/"))
        fila_tecnica3.addWidget(self.filtro_sim)
        fila_tecnica3.addWidget(QLabel("Emp:"))
        fila_tecnica3.addWidget(self.filtro_empresa)
        
        form_tecnicos.addRow("Marca/Modelo:", fila_tecnica1)
        form_tecnicos.addRow("Serie/IMEI:", fila_tecnica2)
        form_tecnicos.addRow("Línea/SIM:", fila_tecnica3)
        
        # Grupo: OTROS FILTROS
        grupo_otros = QGroupBox("░░░ OTROS FILTROS ░░░")
        grupo_otros.setStyleSheet("QGroupBox { font-weight: bold; color: #2c3e50; font-size: 11px; }")
        form_otros = QFormLayout(grupo_otros)
        form_otros.setHorizontalSpacing(8)
        form_otros.setVerticalSpacing(4)
        
        fila_monto = QHBoxLayout()
        self.filtro_monto_desde = QLineEdit()
        self.filtro_monto_desde.setPlaceholderText("Desde")
        self.filtro_monto_desde.setValidator(QDoubleValidator(0, 9999999, 2))
        self.filtro_monto_desde.setMaximumWidth(70)
        self.filtro_monto_desde.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_monto_hasta = QLineEdit()
        self.filtro_monto_hasta.setPlaceholderText("Hasta")
        self.filtro_monto_hasta.setValidator(QDoubleValidator(0, 9999999, 2))
        self.filtro_monto_hasta.setMaximumWidth(70)
        self.filtro_monto_hasta.textChanged.connect(self._aplicar_automaticamente)
        
        fila_monto.addWidget(self.filtro_monto_desde)
        fila_monto.addWidget(QLabel("a"))
        fila_monto.addWidget(self.filtro_monto_hasta)
        fila_monto.addStretch()
        
        self.filtro_anio_prd = QLineEdit()
        self.filtro_anio_prd.setPlaceholderText("Año PRD...")
        self.filtro_anio_prd.setValidator(QIntValidator(2000, 2030))
        self.filtro_anio_prd.setMaximumWidth(80)
        self.filtro_anio_prd.textChanged.connect(self._aplicar_automaticamente)
        
        self.filtro_descripcion = QLineEdit()
        self.filtro_descripcion.setPlaceholderText("Descripción...")
        self.filtro_descripcion.textChanged.connect(self._aplicar_automaticamente)
        
        form_otros.addRow("Monto:", fila_monto)
        form_otros.addRow("Año PRD:", self.filtro_anio_prd)
        form_otros.addRow("Descripción:", self.filtro_descripcion)
        
        fila_inferior.addWidget(grupo_tecnicos)
        fila_inferior.addWidget(grupo_otros)
        
        # ===== BOTONES =====
        botones_layout = QHBoxLayout()
        
        self.btn_limpiar = QPushButton("🧹 Limpiar Todo")
        self.btn_limpiar.clicked.connect(self.limpiar_filtros)
        self.btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        self.btn_aplicar = QPushButton("🔍 Aplicar Filtros")
        self.btn_aplicar.clicked.connect(self.aplicar_filtros)
        self.btn_aplicar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #219a52;
            }
        """)
        
        botones_layout.addWidget(self.btn_limpiar)
        botones_layout.addStretch()
        botones_layout.addWidget(self.btn_aplicar)
        
        # ===== ENSAMBLAR TODO =====
        layout.addLayout(fila_superior)
        layout.addLayout(fila_inferior)
        layout.addLayout(botones_layout)

    def _aplicar_automaticamente(self):
        """Aplica filtros automáticamente después de un pequeño delay"""
        # Por ahora aplicamos inmediatamente, luego podemos agregar debounce
        self.aplicar_filtros()

    def obtener_filtros(self):
        """Retorna un diccionario con todos los filtros aplicados"""
        filtros = {
            # Filtros rápidos
            'prd': self.filtro_prd.text().strip(),
            'tipo': self.filtro_tipo.currentText().strip(),
            'ficha_desde': self.filtro_ficha_desde.text().strip(),
            'ficha_hasta': self.filtro_ficha_hasta.text().strip(),
            'estado': self.filtro_estado.currentText().strip(),
            'institucional': self.filtro_institucional.currentText().strip(),
            
            # Datos personales
            'nombre': self.filtro_nombre.text().strip(),
            'apellido': self.filtro_apellido.text().strip(),
            'dni_cuit': self.filtro_dni_cuit.text().strip(),
            
            # Datos técnicos
            'marca': self.filtro_marca.text().strip(),
            'modelo': self.filtro_modelo.text().strip(),
            'serie': self.filtro_serie.text().strip(),
            'imei': self.filtro_imei.text().strip(),
            'linea': self.filtro_linea.text().strip(),
            'sim': self.filtro_sim.text().strip(),
            'empresa': self.filtro_empresa.currentText().strip(),
            
            # Otros filtros
            'monto_desde': self.filtro_monto_desde.text().strip(),
            'monto_hasta': self.filtro_monto_hasta.text().strip(),
            'anio_prd': self.filtro_anio_prd.text().strip(),
            'descripcion': self.filtro_descripcion.text().strip()
        }
        
        # Eliminar filtros vacíos
        return {k: v for k, v in filtros.items() if v}
        
    def limpiar_filtros(self):
        """Limpia todos los campos del panel"""
        # Limpiar campos de texto
        campos_texto = [
            self.filtro_prd, self.filtro_ficha_desde, self.filtro_ficha_hasta,
            self.filtro_nombre, self.filtro_apellido, self.filtro_dni_cuit,
            self.filtro_marca, self.filtro_modelo, self.filtro_serie, self.filtro_imei,
            self.filtro_linea, self.filtro_sim, self.filtro_monto_desde, 
            self.filtro_monto_hasta, self.filtro_anio_prd, self.filtro_descripcion
        ]
        
        for campo in campos_texto:
            campo.clear()
        
        # Resetear comboboxes
        self.filtro_tipo.setCurrentIndex(0)
        self.filtro_estado.setCurrentIndex(0)
        self.filtro_institucional.setCurrentIndex(0)
        self.filtro_empresa.setCurrentIndex(0)
        
        # Emitir señal de filtros limpios
        self.filtros_aplicados.emit({})

    # BORRA el método actualizar_tipos_dinamicos completo
    # Y PEGA este nuevo con debug:

    def actualizar_tipos_dinamicos(self):
        """Actualiza SOLO el combobox de tipos con datos reales de la BD - VERSIÓN DEBUG"""
        try:
            print("🔄 DEBUG: Ejecutando actualizar_tipos_dinamicos...")
            
            if not self.db:
                print("❌ DEBUG: No hay conexión a BD")
                return
                
            # Obtener bienes para extraer tipos
            bienes = self.db.list_bienes(limite=1000)
            print(f"📊 DEBUG: Bienes obtenidos: {len(bienes)}")
            
            # Extraer tipos únicos
            tipos_unicos = set()
            for i, bien in enumerate(bienes):
                if hasattr(bien, 'keys'):
                    bien_dict = dict(bien)
                else:
                    bien_dict = bien
                
                tipo = str(bien_dict.get('tipo', '')).strip()
                if i < 5:  # Mostrar solo primeros 5 para no saturar
                    print(f"🔍 DEBUG: Bien {i} - Tipo: '{tipo}'")
                if tipo and tipo != 'None' and tipo != '':  # Filtrar vacíos
                    tipos_unicos.add(tipo)
            
            # Ordenar alfabéticamente
            tipos_ordenados = sorted(list(tipos_unicos))
            print(f"🎯 DEBUG: Tipos únicos encontrados: {tipos_ordenados}")
            
            # Actualizar combobox
            current_text = self.filtro_tipo.currentText()
            print(f"🔧 DEBUG: Texto actual en combobox: '{current_text}'")
            
            self.filtro_tipo.clear()
            self.filtro_tipo.addItem("")  # Opción vacía
            self.filtro_tipo.addItems(tipos_ordenados)
            
            print(f"✅ DEBUG: Combobox actualizado con {len(tipos_ordenados)} tipos")
            print(f"✅ DEBUG: Items en combobox: {[self.filtro_tipo.itemText(i) for i in range(self.filtro_tipo.count())]}")
            
        except Exception as e:
            print(f"❌ DEBUG: Error en actualizar_tipos_dinamicos: {e}")
            import traceback
            traceback.print_exc()
        
    def aplicar_filtros(self):
        """Aplica los filtros y emite la señal"""
        filtros = self.obtener_filtros()
        self.filtros_aplicados.emit(filtros)
        print(f"🔍 Filtros aplicados: {len(filtros)} criterios")