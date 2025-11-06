"""
📱 PUNTO DE ENTRADA PRINCIPAL - Sistema de Inventario AGC
"""

import sys
import os
import traceback

# Agregar la carpeta del proyecto al path de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication

# Importar desde nuestros nuevos módulos
from config.settings import DB_PATH, ACTAS_FOLDER
from database.db_manager import DB
from ui.dialogs.login_dialog import LoginDialog
from ui.main_window import VentanaPrincipal


def main():
    """Función principal de la aplicación"""
    try:
        print("🚀 INICIANDO SISTEMA DE INVENTARIO AGC...")
        
        # Crear aplicación
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # 🗄️ CONECTAR A BASE DE DATOS
        print("🔗 Conectando a base de datos...")
        db = DB(DB_PATH, ACTAS_FOLDER)
        print("✅ Base de datos conectada")
        
        # 🔐 MOSTRAR LOGIN
        print("🔐 Mostrando login...")
        login_dialog = LoginDialog(db)  # ✅ ¡PASA LA BASE DE DATOS!
        if login_dialog.exec_() != LoginDialog.Accepted:
            print("❌ Login cancelado por el usuario")
            return 0  # Salida normal
            
        # ✅ VERIFICAR USUARIO ANTES DE CONTINUAR
        print("🏢 Iniciando ventana principal...")
        if not hasattr(login_dialog, 'usuario_actual') or not login_dialog.usuario_actual:
            print("❌ No se pudo obtener usuario del login")
            return 1
            
        ventana = VentanaPrincipal(db, login_dialog.usuario_actual)
        ventana.show()
        print("✅ Sistema iniciado correctamente")
        
        return app.exec_()
        
    except Exception as e:
        print(f"❌ Error crítico al iniciar: {e}")
        print(f"📋 Detalles: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())