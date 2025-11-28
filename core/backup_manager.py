"""
🏗️ GESTOR DE BACKUPS - Sistema de Inventario AGC
Maneja backups automáticos y manuales
"""

import shutil
import os
from datetime import datetime
from database.db_manager import DB


class BackupManager:
    """Maneja el sistema de backups"""
    
    def __init__(self, db: DB):
        self.db = db
    
    def crear_backup_automatico(self):
        """Crea backup automático (máximo 1 por día)"""
        return self.db.crear_backup()
    
    def crear_backup_manual(self, nombre_personalizado=None):
        """Crea backup manual con nombre personalizado"""
        # Lógica para backups manuales
        pass