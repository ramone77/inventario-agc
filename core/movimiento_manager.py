"""
"""
🏗️ GESTOR DE MOVIMIENTOS - Sistema de Inventario AGC  
Lógica de negocio para movimientos
"""

from database.db_manager import DB


class MovimientoManager:
    """Maneja la lógica de negocio para movimientos"""
    
    def __init__(self, db: DB):
        self.db = db
    
    def crear_movimiento(self, datos_movimiento, bienes_ids):
        """Crea un movimiento con validaciones"""
        return self.db.add_movimiento(datos_movimiento, bienes_ids)
    
    def obtener_movimientos_detallados(self):
        """Obtiene movimientos con información completa"""
        return self.db.get_movimientos_detallados()