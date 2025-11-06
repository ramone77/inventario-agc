"""
🎨 HEADER PERSONALIZADO - Sistema de Inventario AGC
Header de tabla con ordenamiento (sin filtros Excel)
"""

from PyQt5.QtWidgets import QHeaderView, QMenu, QAction
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QCursor


class HeaderFiltros(QHeaderView):
    """Header personalizado SIMPLIFICADO - Solo ordenamiento"""
    
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.mostrar_menu_simplificado)
        
    def mostrar_menu_simplificado(self, pos):
        """Muestra menú simplificado - Solo ordenamiento"""
        index = self.logicalIndexAt(pos)
        if index < 0:
            return
            
        # Obtener nombre de columna
        tabla = self.parent()
        if not tabla or tabla.rowCount() == 0:
            return
        
        nombre_columna = tabla.horizontalHeaderItem(index).text() if tabla.horizontalHeaderItem(index) else f"Columna {index + 1}"
        
        # Crear menú
        menu = QMenu(self)
        
        # Información para el usuario
        info_action = QAction(f"💡 Usa el panel de filtros avanzados", self)
        info_action.setEnabled(False)
        menu.addAction(info_action)
        
        menu.addSeparator()
        
        # Opciones de ordenamiento
        accion_ordenar_asc = QAction(f"🔺 Ordenar {nombre_columna} A-Z", self)
        accion_ordenar_asc.triggered.connect(lambda: self.ordenar_columna(index, Qt.AscendingOrder))
        menu.addAction(accion_ordenar_asc)
        
        accion_ordenar_desc = QAction(f"🔻 Ordenar {nombre_columna} Z-A", self)
        accion_ordenar_desc.triggered.connect(lambda: self.ordenar_columna(index, Qt.DescendingOrder))
        menu.addAction(accion_ordenar_desc)
        
        menu.addSeparator()
        
        # Ir al panel de filtros
        accion_ir_filtros = QAction("🚀 Ir al panel de filtros avanzados", self)
        accion_ir_filtros.triggered.connect(self._ir_a_panel_filtros)
        menu.addAction(accion_ir_filtros)
        
        # Mostrar menú
        menu.exec_(QCursor.pos())
    
    def _ir_a_panel_filtros(self):
        """Lleva al usuario al panel de filtros avanzados"""
        parent = self.parent()
        while parent and not hasattr(parent, 'tabs'):
            parent = parent.parent()
        
        if parent and hasattr(parent, 'tabs'):
            parent.tabs.setCurrentIndex(0)  # Pestaña "Buscar Bienes"

    def ordenar_columna(self, col_index, orden):
        """Ordenar la columna especificada"""
        tabla = self.parent()
        if tabla:
            tabla.sortItems(col_index, orden)

    def limpiar_filtros(self):
        """Método por compatibilidad"""
        print("💡 Los filtros se gestionan desde el panel avanzado")