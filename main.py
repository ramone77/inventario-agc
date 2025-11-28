"""
🏢 SISTEMA DE INVENTARIO AGC - PUNTO DE ENTRADA
Sistema completo de gestión de bienes patrimoniales
"""

import sys
import os
import traceback

# ✅ AGREGAR ESTO PARA IMPORTS ABSOLUTOS
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# ✅ NUEVAS IMPORTACIONES - ARQUITECTURA PROFESIONAL
from config.settings import get_db_path, get_actas_folder, get_info_sistema
from database.db_manager import DB
from ui.dialogs.login_dialog import LoginDialog
from ui.main_window import VentanaPrincipal


def excepcion_global(tipo, valor, tb):
    """Manejador global de excepciones"""
    traceback.print_exception(tipo, valor, tb)
    QMessageBox.critical(
        None, 
        "Error Crítico", 
        f"Error inesperado:\n\n{str(valor)}\n\nRevisa la consola para más detalles."
    )
    sys.exit(1)


def main():
    """Función principal de la aplicación"""
    try:
        # Configurar manejo de excepciones
        sys.excepthook = excepcion_global
        
        # Crear aplicación Qt
        app = QApplication(sys.argv)
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        app.setFont(QFont("Segoe UI", 10))
        
        print("🚀 INICIANDO SISTEMA DE INVENTARIO AGC - ARQUITECTURA PROFESIONAL")
        print("=" * 70)
        
        # ✅ NUEVO: Mostrar información del sistema
        info_sistema = get_info_sistema()
        print(f"📍 Modo: {info_sistema['modo_trabajo']}")
        print(f"🗃️ BD Activa: {info_sistema['db_activa']}")
        print(f"🌐 BD Maestra: {info_sistema['db_maestra']}")
        print(f"📁 Carpeta Actas: {info_sistema['carpeta_actas']}")
        print(f"👤 Usuario: {info_sistema['usuario']}")
        print("=" * 70)
        
        # ✅ NUEVO: Obtener rutas dinámicamente
        db_path = get_db_path()
        actas_folder = get_actas_folder()
        
        print(f"🔗 Conectando a base de datos: {db_path}")
        
        # Inicializar base de datos
        db = DB(db_path, actas_folder)
        
        # Mostrar diálogo de login
        login_dialog = LoginDialog(db)
        if login_dialog.exec_() == LoginDialog.Accepted:
            usuario = login_dialog.obtener_usuario_actual()
            print(f"✅ Usuario autenticado: {usuario['id']} ({usuario['rol']})")
            
            # Crear y mostrar ventana principal
            ventana = VentanaPrincipal(db, usuario)
            ventana.show()
            
            print("🎉 Sistema cargado correctamente")
            print("💡 Usa el botón 🔄 Sincronizar para mantener tus datos actualizados")
            
            # Ejecutar aplicación
            sys.exit(app.exec_())
        else:
            print("❌ Login cancelado")
            sys.exit(0)
            
    except Exception as e:
        print(f"💥 ERROR CRÍTICO: {e}")
        traceback.print_exc()
        QMessageBox.critical(
            None, 
            "Error de Inicio", 
            f"No se pudo iniciar la aplicación:\n\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()