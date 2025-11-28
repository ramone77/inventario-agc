"""
📊 DASHBOARD Y GRÁFICOS - Sistema de Inventario AGC v2.3
Dashboard INTERACTIVO con gráficos clickables y tooltips
"""

import matplotlib
matplotlib.use('Qt5Agg')  # Asegura compatibilidad con PyQt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QFrame, QComboBox, QScrollArea, QGridLayout, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon
import matplotlib.pyplot as plt


class TarjetaKPI(QWidget):
    """Widget de tarjeta KPI para el dashboard - VERSIÓN MEJORADA"""
    
    def __init__(self, titulo, valor, descripcion, icono=None, color_base="#3498db", parent=None):
        super().__init__(parent)
        self.titulo = titulo
        self.valor = str(valor)
        self.descripcion = descripcion
        self.icono = icono
        self.color_base = color_base
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Fila superior: icono + título
        header_layout = QHBoxLayout()
        
        if self.icono:
            self.label_icono = QLabel()
            # Si 'icono' es un QLabel (como en tu caso), copiamos su texto
            if isinstance(self.icono, QLabel):
                # Obtener el texto del QLabel original (ej: "📦")
                texto_icono = self.icono.text()
                self.label_icono.setText(texto_icono)
                self.label_icono.setStyleSheet("font-size: 18px;")
            else:
                # Si es un string o emoji, usar directamente
                self.label_icono.setText(str(self.icono))
                self.label_icono.setStyleSheet("font-size: 18px;")
            header_layout.addWidget(self.label_icono)
        
        self.label_titulo = QLabel(self.titulo)
        self.label_titulo.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.label_titulo)
        header_layout.addStretch()
        
        # Valor principal
        self.label_valor = QLabel(self.valor)
        self.label_valor.setStyleSheet("color: white; font-weight: bold; font-size: 28px;")
        self.label_valor.setAlignment(Qt.AlignCenter)
        
        # Descripción (abajo del valor)
        self.label_descripcion = QLabel(self.descripcion)
        self.label_descripcion.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 11px;")
        self.label_descripcion.setAlignment(Qt.AlignCenter)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.label_valor)
        layout.addWidget(self.label_descripcion)
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.color_base};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        self.setToolTip(self.descripcion)
    
    def actualizar_valor(self, nuevo_valor, descripcion_adicional=""):
        """Actualiza el valor y opcionalmente la descripción"""
        self.label_valor.setText(str(nuevo_valor))
        if descripcion_adicional:
            self.label_descripcion.setText(descripcion_adicional)
    
    def cambiar_color(self, nuevo_color):
        """Cambia el color de fondo dinámicamente"""
        self.color_base = nuevo_color
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {self.color_base};
                border-radius: 10px;
                padding: 10px;
            }}
        """)


class GraficoWidget(QWidget):
    """Widget para gráficos matplotlib integrados en PyQt - INTERACTIVO"""
    
    def __init__(self, titulo, parent=None):
        super().__init__(parent)
        self.titulo = titulo
        self.dashboard_parent = parent  # ✅ NUEVO: Referencia al dashboard padre
        
        # ✅ CONFIGURACIÓN MÁS PROFESIONAL
        plt.style.use('seaborn-v0_8')  # Estilo más limpio
        self.fig = Figure(figsize=(10, 6), dpi=100, facecolor='#f8f9fa')  # Fondo claro profesional
        self.canvas = FigureCanvas(self.fig)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(self.canvas)
    
    def actualizar_grafico_estado(self, datos_estado):
        """Gráfico circular con interactividad MEJORADA"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not datos_estado:
            ax.text(0.5, 0.5, 'No hay datos disponibles', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=14, style='italic',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
            ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
            self.canvas.draw()
            return

        estados = list(datos_estado.keys())
        valores = list(datos_estado.values())
        total = sum(valores)
        
        # Paleta de colores profesional
        colores = ['#27ae60', '#3498db', '#e67e22', '#e74c3c', '#9b59b6', '#f1c40f']
        
        # Crear gráfico con leyenda externa
        wedges, texts, autotexts = ax.pie(
            valores, 
            labels=None,  # No mostrar labels directamente
            autopct=lambda pct: f'{pct:.1f}%' if pct > 5 else '',  # Solo porcentajes >5%
            startangle=90,
            colors=colores[:len(estados)],
            explode=[0.03] * len(estados),  # Separación entre slices
            shadow=True,  # Sombra para efecto 3D
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        
        # Mejorar porcentajes
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        # LEYENDA EXTERNA MEJORADA
        leyenda_labels = [f'{estado}: {val} ({val/total*100:.1f}%)' for estado, val in zip(estados, valores)]
        ax.legend(wedges, leyenda_labels,
                 title="Estados",
                 loc="center left",
                 bbox_to_anchor=(1, 0, 0.5, 1),
                 fontsize=10,
                 frameon=True,
                 fancybox=True,
                 shadow=True)
        
        ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
        
        # ✅ NUEVO: INTERACTIVIDAD - Click en sectores
        def on_click(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_event(event)[0]:
                        estado_seleccionado = estados[i]
                        cantidad = valores[i]
                        print(f"🎯 Click en gráfico estado: {estado_seleccionado} ({cantidad} bienes)")
                        
                        # Aplicar filtro automático
                        if self.dashboard_parent:
                            self.dashboard_parent.aplicar_filtro_desde_grafico('estado', estado_seleccionado)
        
        # ✅ NUEVO: INTERACTIVIDAD - Tooltips al hover
        def on_hover(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    if wedge.contains_event(event)[0]:
                        estado = estados[i]
                        cantidad = valores[i]
                        porcentaje = (cantidad / total) * 100
                        
                        # Mostrar tooltip en título
                        wedge.set_alpha(0.8)  # Resaltar
                        ax.set_title(f"{self.titulo}\n🔍 {estado}: {cantidad} bienes ({porcentaje:.1f}%)", 
                                   fontsize=16, fontweight='bold', color='#2c3e50')
                    else:
                        wedge.set_alpha(1.0)  # Normal
                
                self.canvas.draw_idle()
        
        # Conectar eventos
        self.canvas.mpl_connect('button_press_event', on_click)
        self.canvas.mpl_connect('motion_notify_event', on_hover)
        
        # Ajustar layout para que quepa la leyenda
        self.fig.tight_layout()
        self.canvas.draw()

    def actualizar_grafico_tipo(self, datos_tipo):
        """Gráfico de barras horizontal con interactividad"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not datos_tipo:
            ax.text(0.5, 0.5, 'No hay datos disponibles', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=14, style='italic',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
            ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
            self.canvas.draw()
            return

        tipos = list(datos_tipo.keys())
        valores = list(datos_tipo.values())
        
        # Gráfico de barras HORIZONTAL (mejor para textos largos)
        bars = ax.barh(tipos, valores, color='#3498db', alpha=0.8, 
                      edgecolor='#2980b9', linewidth=1, height=0.6)
        
        # Agregar valores en las barras
        for bar, valor in zip(bars, valores):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{valor}', ha='left', va='center', fontweight='bold', fontsize=10)
        
        ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
        ax.set_xlabel("Cantidad", fontsize=12, fontweight='bold', color='#2c3e50')
        
        # Grid sutil
        ax.grid(True, axis='x', alpha=0.3, linestyle='--', color='gray')
        ax.set_axisbelow(True)
        
        # Fondo del gráfico
        ax.set_facecolor('#f8f9fa')
        
        # ✅ NUEVO: INTERACTIVIDAD - Click en barras
        def on_click(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains_event(event)[0]:
                        tipo_seleccionado = tipos[i]
                        cantidad = valores[i]
                        print(f"🎯 Click en gráfico tipo: {tipo_seleccionado} ({cantidad} bienes)")
                        
                        # Aplicar filtro automático
                        if self.dashboard_parent:
                            self.dashboard_parent.aplicar_filtro_desde_grafico('tipo', tipo_seleccionado)
        
        # ✅ NUEVO: INTERACTIVIDAD - Tooltips al hover
        def on_hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains_event(event)[0]:
                        tipo = tipos[i]
                        cantidad = valores[i]
                        
                        # Resaltar barra
                        bar.set_alpha(0.9)
                        bar.set_color('#e67e22')  # Color naranja al hover
                        
                        # Actualizar título con info
                        ax.set_title(f"{self.titulo}\n🔍 {tipo}: {cantidad} bienes", 
                                   fontsize=16, fontweight='bold', color='#2c3e50')
                    else:
                        bar.set_alpha(0.8)
                        bar.set_color('#3498db')  # Volver a azul
                
                self.canvas.draw_idle()
        
        # Conectar eventos
        self.canvas.mpl_connect('button_press_event', on_click)
        self.canvas.mpl_connect('motion_notify_event', on_hover)
        
        self.fig.tight_layout()
        self.canvas.draw()

    def actualizar_grafico_marca(self, datos_marca):
        """Actualiza gráfico de barras por marca con interactividad"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not datos_marca:
            ax.text(0.5, 0.5, 'No hay datos disponibles', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=14, style='italic',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
            ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
            self.canvas.draw()
            return

        marcas = list(datos_marca.keys())
        valores = list(datos_marca.values())
        
        # Gráfico de barras VERTICAL para marcas
        bars = ax.bar(marcas, valores, color='#9b59b6', alpha=0.8, 
                     edgecolor='#8e44ad', linewidth=1)
        
        # Agregar valores en las barras
        for bar, valor in zip(bars, valores):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{valor}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
        ax.set_ylabel("Cantidad", fontsize=12, fontweight='bold', color='#2c3e50')
        ax.tick_params(axis='x', rotation=45, labelsize=10)
        ax.tick_params(axis='y', labelsize=10)
        
        # Grid sutil
        ax.grid(True, axis='y', alpha=0.3, linestyle='--', color='gray')
        ax.set_axisbelow(True)
        
        # Fondo del gráfico
        ax.set_facecolor('#f8f9fa')
        
        # ✅ NUEVO: INTERACTIVIDAD - Click en barras
        def on_click(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains_event(event)[0]:
                        marca_seleccionada = marcas[i]
                        cantidad = valores[i]
                        print(f"🎯 Click en gráfico marca: {marca_seleccionada} ({cantidad} bienes)")
                        
                        # Aplicar filtro automático
                        if self.dashboard_parent:
                            self.dashboard_parent.aplicar_filtro_desde_grafico('marca', marca_seleccionada)
        
        # ✅ NUEVO: INTERACTIVIDAD - Tooltips al hover
        def on_hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains_event(event)[0]:
                        marca = marcas[i]
                        cantidad = valores[i]
                        
                        # Resaltar barra
                        bar.set_alpha(0.9)
                        bar.set_color('#e67e22')  # Color naranja al hover
                        
                        # Actualizar título con info
                        ax.set_title(f"{self.titulo}\n🔍 {marca}: {cantidad} bienes", 
                                   fontsize=16, fontweight='bold', color='#2c3e50')
                    else:
                        bar.set_alpha(0.8)
                        bar.set_color('#9b59b6')  # Volver a morado
                
                self.canvas.draw_idle()
        
        # Conectar eventos
        self.canvas.mpl_connect('button_press_event', on_click)
        self.canvas.mpl_connect('motion_notify_event', on_hover)
        
        self.fig.tight_layout()
        self.canvas.draw()

    def actualizar_grafico_institucional(self, datos_institucional):
        """Actualiza gráfico de barras por institucional con interactividad"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        
        if not datos_institucional:
            ax.text(0.5, 0.5, 'No hay datos disponibles', 
                   horizontalalignment='center', verticalalignment='center', 
                   transform=ax.transAxes, fontsize=14, style='italic',
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7))
            ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
            self.canvas.draw()
            return

        institucionales = list(datos_institucional.keys())
        valores = list(datos_institucional.values())
        
        # Gráfico de barras HORIZONTAL para áreas institucionales
        bars = ax.barh(institucionales, valores, color='#16a085', alpha=0.8, 
                      edgecolor='#1abc9c', linewidth=1, height=0.6)
        
        # Agregar valores en las barras
        for bar, valor in zip(bars, valores):
            width = bar.get_width()
            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2, 
                   f'{valor}', ha='left', va='center', fontweight='bold', fontsize=10)
        
        ax.set_title(self.titulo, fontsize=16, fontweight='bold', pad=20, color='#2c3e50')
        ax.set_xlabel("Cantidad", fontsize=12, fontweight='bold', color='#2c3e50')
        ax.tick_params(axis='x', labelsize=10)
        ax.tick_params(axis='y', labelsize=9)  # Texto más pequeño para áreas largas
        
        # Grid sutil
        ax.grid(True, axis='x', alpha=0.3, linestyle='--', color='gray')
        ax.set_axisbelow(True)
        
        # Fondo del gráfico
        ax.set_facecolor('#f8f9fa')
        
        # ✅ NUEVO: INTERACTIVIDAD - Click en barras
        def on_click(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains_event(event)[0]:
                        institucional_seleccionado = institucionales[i]
                        cantidad = valores[i]
                        print(f"🎯 Click en gráfico institucional: {institucional_seleccionado} ({cantidad} bienes)")
                        
                        # Aplicar filtro automático
                        if self.dashboard_parent:
                            self.dashboard_parent.aplicar_filtro_desde_grafico('institucional', institucional_seleccionado)
        
        # ✅ NUEVO: INTERACTIVIDAD - Tooltips al hover
        def on_hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    if bar.contains_event(event)[0]:
                        institucional = institucionales[i]
                        cantidad = valores[i]
                        
                        # Resaltar barra
                        bar.set_alpha(0.9)
                        bar.set_color('#e67e22')  # Color naranja al hover
                        
                        # Actualizar título con info
                        ax.set_title(f"{self.titulo}\n🔍 {institucional}: {cantidad} bienes", 
                                   fontsize=16, fontweight='bold', color='#2c3e50')
                    else:
                        bar.set_alpha(0.8)
                        bar.set_color('#16a085')  # Volver a verde
                
                self.canvas.draw_idle()
        
        # Conectar eventos
        self.canvas.mpl_connect('button_press_event', on_click)
        self.canvas.mpl_connect('motion_notify_event', on_hover)
        
        self.fig.tight_layout()
        self.canvas.draw()


class DashboardConfigurableWidget(QWidget):
    """Widget principal del dashboard ejecutivo INTERACTIVO"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.parent_window = parent  # ✅ NUEVO: Referencia a ventana principal
        self.filtros_actuales = {}
        self.cache_estadisticas = {}
        self._setup_ui()
        self.cargar_opciones_filtros()
        self.cargar_datos_iniciales()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("📊 DASHBOARD EJECUTIVO INTERACTIVO - INVENTARIO AGC v2.3")
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QLabel {
                font-size: 18px; 
                font-weight: bold; 
                color: #2c3e50; 
                padding: 15px;
                background-color: #3498db;
                color: white;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(header)

        # Filtros
        filtros_layout = QHBoxLayout()

        self.combo_institucional = QComboBox()
        self.combo_institucional.addItems(["Todas las áreas", ""])
        self.combo_institucional.currentTextChanged.connect(self.aplicar_filtros)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Todos los tipos", ""])
        self.combo_tipo.currentTextChanged.connect(self.aplicar_filtros)

        self.combo_estado = QComboBox()
        self.combo_estado.addItems(["Todos los estados", ""])
        self.combo_estado.currentTextChanged.connect(self.aplicar_filtros)

        self.combo_marca = QComboBox()
        self.combo_marca.addItems(["Todas las marcas", ""])
        self.combo_marca.currentTextChanged.connect(self.aplicar_filtros)

        btn_limpiar = QPushButton("🧹 Limpiar Filtros")
        btn_limpiar.clicked.connect(self.limpiar_filtros)

        filtros_layout.addWidget(QLabel("Área:"))
        filtros_layout.addWidget(self.combo_institucional)
        filtros_layout.addWidget(QLabel("Tipo:"))
        filtros_layout.addWidget(self.combo_tipo)
        filtros_layout.addWidget(QLabel("Estado:"))
        filtros_layout.addWidget(self.combo_estado)
        filtros_layout.addWidget(QLabel("Marca:"))
        filtros_layout.addWidget(self.combo_marca)
        filtros_layout.addWidget(btn_limpiar)
        filtros_layout.addStretch()

        layout.addLayout(filtros_layout)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(sep)

        # Tarjetas KPI
        kpi_layout = QHBoxLayout()

        # Iconos como emojis (ahora como QLabel)
        icon_total = QLabel("📦")
        icon_deposito = QLabel("🟢")
        icon_asignados = QLabel("👤")
        icon_bajas = QLabel("📉")

        self.kpi_total = TarjetaKPI("TOTAL BIENES", "0", "Cantidad total de bienes filtrados", icon_total, "#3498db")
        self.kpi_deposito = TarjetaKPI("EN DEPÓSITO", "0", "Bienes disponibles en depósito", icon_deposito, "#27ae60")
        self.kpi_asignados = TarjetaKPI("ASIGNADOS", "0", "Bienes actualmente asignados", icon_asignados, "#e67e22")
        self.kpi_bajas = TarjetaKPI("BAJAS", "0", "Bienes dados de baja", icon_bajas, "#e74c3c")

        kpi_layout.addWidget(self.kpi_total)
        kpi_layout.addWidget(self.kpi_deposito)
        kpi_layout.addWidget(self.kpi_asignados)
        kpi_layout.addWidget(self.kpi_bajas)
        layout.addLayout(kpi_layout)

        # Contenedor de gráficos (2 grandes, lado a lado)
        graficos_layout = QHBoxLayout()

        # Definir los 2 contenedores de gráficos grandes
        self.contenedores_graficos = []
        tipos_graficos = [
            "Distribución por Estado",
            "Bienes por Tipo"
        ]
        titulos_iniciales = [
            "📊 Distribución por Estado",
            "📈 Bienes por Tipo"
        ]

        for i in range(2):
            contenedor = QWidget()
            contenedor_layout = QVBoxLayout(contenedor)

            combo_tipo = QComboBox()
            combo_tipo.addItems([
                "Distribución por Estado",
                "Bienes por Tipo",
                "Bienes por Área",
                "Bienes por Marca"
            ])
            combo_tipo.setCurrentText(tipos_graficos[i])
            combo_tipo.currentTextChanged.connect(lambda text, index=i: self.cambiar_tipo_grafico(index, text))

            # ✅ MODIFICADO: Pasar self como parent para interactividad
            grafico_widget = GraficoWidget(titulos_iniciales[i], self)

            contenedor_layout.addWidget(QLabel(f"Gráfico {i+1}:"))
            contenedor_layout.addWidget(combo_tipo)
            contenedor_layout.addWidget(grafico_widget)

            graficos_layout.addWidget(contenedor)

            self.contenedores_graficos.append({
                'combo': combo_tipo,
                'widget': grafico_widget
            })

        layout.addLayout(graficos_layout)

        # Botón de actualización
        btn_actualizar = QPushButton("🔄 Actualizar Dashboard")
        btn_actualizar.clicked.connect(self.cargar_datos_iniciales)
        layout.addWidget(btn_actualizar)

    # ✅ NUEVO MÉTODO: Aplicar filtro desde gráfico
    def aplicar_filtro_desde_grafico(self, tipo_filtro, valor):
        """Aplica filtro automáticamente en la tabla principal"""
        try:
            if not self.parent_window:
                print("⚠️ No hay referencia a ventana principal")
                QMessageBox.information(self, "Dashboard Interactivo", 
                                      f"Click en: {tipo_filtro} = {valor}\n\n"
                                      "Esta función aplicaría el filtro automáticamente en la tabla principal.")
                return
                
            print(f"🎯 Aplicando filtro desde dashboard: {tipo_filtro} = {valor}")
            
            # Mostrar confirmación al usuario
            respuesta = QMessageBox.question(self, "Dashboard Interactivo",
                                           f"¿Aplicar filtro automático?\n\n"
                                           f"{tipo_filtro.upper()}: {valor}\n\n"
                                           f"Se cambiará a la pestaña de búsqueda con este filtro aplicado.",
                                           QMessageBox.Yes | QMessageBox.No)
            
            if respuesta == QMessageBox.Yes:
                # Aplicar en panel de filtros de la ventana principal
                if hasattr(self.parent_window, 'panel_filtros'):
                    # Limpiar filtros previos
                    self.parent_window.panel_filtros.limpiar_filtros()
                    
                    # Aplicar nuevo filtro según el tipo
                    if tipo_filtro == 'estado':
                        self.parent_window.panel_filtros.filtro_estado.setCurrentText(valor)
                    elif tipo_filtro == 'tipo':
                        self.parent_window.panel_filtros.filtro_tipo.setCurrentText(valor)
                    elif tipo_filtro == 'institucional':
                        self.parent_window.panel_filtros.filtro_institucional.setCurrentText(valor)
                    elif tipo_filtro == 'marca':
                        self.parent_window.panel_filtros.filtro_marca.setText(valor)
                    
                    # Forzar aplicación del filtro
                    self.parent_window.panel_filtros.aplicar_filtros()
                    
                    # Cambiar a pestaña de búsqueda
                    self.parent_window.tabs.setCurrentIndex(0)
                    
                    print(f"✅ Filtro aplicado: {valor}")
                else:
                    print("❌ No se encontró panel de filtros")
            else:
                print("⏹️ Usuario canceló la aplicación del filtro")
                
        except Exception as e:
            print(f"❌ Error aplicando filtro: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo aplicar el filtro:\n{str(e)}")

    def cargar_opciones_filtros(self):
        """Carga las opciones dinámicas para los combos de filtro"""
        try:
            # Obtener institucionales
            institucionales = self.db.obtener_valores_unicos('institucional')
            self.combo_institucional.clear()
            self.combo_institucional.addItem("Todas las áreas")
            self.combo_institucional.addItems(institucionales)

            # Obtener tipos
            tipos = self.db.obtener_valores_unicos('tipo')
            self.combo_tipo.clear()
            self.combo_tipo.addItem("Todos los tipos")
            self.combo_tipo.addItems(tipos)

            # Obtener estados
            estados = self.db.obtener_valores_unicos('estado')
            self.combo_estado.clear()
            self.combo_estado.addItem("Todos los estados")
            self.combo_estado.addItems(estados)

            # Obtener marcas
            marcas = self.db.obtener_valores_unicos('marca')
            self.combo_marca.clear()
            self.combo_marca.addItem("Todas las marcas")
            self.combo_marca.addItems(marcas)

        except Exception as e:
            print(f"❌ Error cargando opciones de filtros: {e}")

    def aplicar_filtros(self):
        """Aplica los filtros seleccionados y actualiza el dashboard"""
        # Obtener valores seleccionados
        institucional = self.combo_institucional.currentText()
        tipo = self.combo_tipo.currentText()
        estado = self.combo_estado.currentText()
        marca = self.combo_marca.currentText()

        # Construir filtros (excluyendo "Todas las..." o "")
        filtros = {}
        if institucional not in ["Todas las áreas", ""]:
            filtros['institucional'] = institucional
        if tipo not in ["Todos los tipos", ""]:
            filtros['tipo'] = tipo
        if estado not in ["Todos los estados", ""]:
            filtros['estado'] = estado
        if marca not in ["Todas las marcas", ""]:
            filtros['marca'] = marca

        self.filtros_actuales = filtros
        self._cargar_datos_con_filtros(filtros)

    def limpiar_filtros(self):
        """Limpia todos los filtros y vuelve a mostrar todos los datos"""
        self.combo_institucional.setCurrentIndex(0)
        self.combo_tipo.setCurrentIndex(0)
        self.combo_estado.setCurrentIndex(0)
        self.combo_marca.setCurrentIndex(0)
        self.filtros_actuales = {}
        self.cargar_datos_iniciales()

    def cargar_datos_iniciales(self):
        """Carga y actualiza todos los datos del dashboard sin filtros"""
        self._cargar_datos_con_filtros({})

    def _cargar_datos_con_filtros(self, filtros):
        """Carga datos usando filtros específicos - CON CACHÉ"""
        # ✅ CACHÉ: Si los filtros son los mismos, usar cache
        clave_cache = tuple(sorted(filtros.items()))
        if clave_cache in self.cache_estadisticas:
            stats = self.cache_estadisticas[clave_cache]
        else:
            # ✅ Consultar BD y guardar en caché
            stats = self.db.get_estadisticas_filtradas(
                institucional=filtros.get('institucional'),
                tipo=filtros.get('tipo'),
                marca=filtros.get('marca'),
                estado=filtros.get('estado')
            )
            self.cache_estadisticas[clave_cache] = stats

        self._actualizar_tarjetas_kpi(stats)
        self._actualizar_graficos(stats)

    def _actualizar_tarjetas_kpi(self, stats):
        """Actualiza los valores de las tarjetas KPI"""
        try:
            total = stats.get('total', 0)
            por_estado = stats.get('por_estado', {})

            # Actualizar cada tarjeta
            self.kpi_total.actualizar_valor(total, f"Total filtrado: {total}")
            self.kpi_deposito.actualizar_valor(por_estado.get('En depósito', 0), f"Disponibles: {por_estado.get('En depósito', 0)}")
            self.kpi_asignados.actualizar_valor(por_estado.get('Asignado', 0), f"Asignados: {por_estado.get('Asignado', 0)}")
            self.kpi_bajas.actualizar_valor(por_estado.get('Baja definitiva', 0), f"Bajas: {por_estado.get('Baja definitiva', 0)}")

            # Cambiar color si hay muchas bajas
            if por_estado.get('Baja definitiva', 0) > total * 0.1:  # Más del 10% de bajas
                self.kpi_bajas.cambiar_color("#c0392b")  # Rojo más oscuro
            else:
                self.kpi_bajas.cambiar_color("#e74c3c")

        except Exception as e:
            print(f"❌ Error actualizando tarjetas KPI: {e}")

    def _actualizar_graficos(self, stats):
        """Actualiza los 2 gráficos reales con matplotlib según su tipo seleccionado"""
        try:
            por_estado = stats.get('por_estado', {})
            por_tipo = stats.get('por_tipo', {})
            por_marca = stats.get('por_marca', {})
            por_institucional = stats.get('por_institucional', {})

            for contenedor in self.contenedores_graficos:
                tipo = contenedor['combo'].currentText()
                grafico = contenedor['widget']

                if tipo == "Distribución por Estado":
                    grafico.actualizar_grafico_estado(por_estado)
                elif tipo == "Bienes por Tipo":
                    grafico.actualizar_grafico_tipo(por_tipo)
                elif tipo == "Bienes por Área":
                    grafico.actualizar_grafico_institucional(por_institucional)
                elif tipo == "Bienes por Marca":
                    grafico.actualizar_grafico_marca(por_marca)

        except Exception as e:
            print(f"❌ Error actualizando gráficos: {e}")

    def cambiar_tipo_grafico(self, index, nuevo_tipo):
        """Cambia el tipo de gráfico en el contenedor 'index'"""
        # Actualizar el título del widget de gráfico
        titulos_mapa = {
            "Distribución por Estado": "📊 Distribución por Estado",
            "Bienes por Tipo": "📈 Bienes por Tipo", 
            "Bienes por Área": "🏢 Bienes por Área",
            "Bienes por Marca": "🏷️ Bienes por Marca"
        }
        nuevo_titulo = titulos_mapa.get(nuevo_tipo, nuevo_tipo)
        self.contenedores_graficos[index]['widget'].titulo = nuevo_titulo
        
        # Volver a pintar con el nuevo tipo
        stats = self.cache_estadisticas.get(tuple(sorted(self.filtros_actuales.items())), {})
        self._actualizar_graficos(stats)