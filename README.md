🏢 Sistema de Inventario AGC - v2.0 Profesional
🚀 NUEVO EN VERSIÓN 2.0
Arquitectura Profesional con Sincronización Inteligente

✨ Características Principales
🔄 Sincronización Inteligente: Trabaja localmente (rápido) + Sincroniza con red (colaborativo)

🎨 Interfaz Profesional: Nueva paleta de colores y diseño moderno

🛡️ Sistema Resiliente: Funciona automáticamente con o sin conexión a red

📊 Dashboard Ejecutivo: KPI's en tiempo real con estadísticas avanzadas

⚙️ 3 Modos de Trabajo:

Sincronización (Recomendado): Rápido + Colaborativo

Red Directo: Producción en tiempo real

Local Solo: Pruebas y desarrollo

📋 Funcionalidades Completas
🔍 Gestión de Bienes
✅ CRUD completo de bienes patrimoniales

✅ Filtros avanzados dinámicos y auto-alimentados

✅ Búsqueda inteligente en todos los campos

✅ Validación de datos y prevención de duplicados

🔄 Sistema de Movimientos
✅ Entregas, devoluciones y bajas

✅ Gestión completa de responsables

✅ Tracking histórico de movimientos

✅ Generación automática de actas PDF

👥 Sistema Multi-Usuario
✅ Roles: Administrador, Supervisor, Operador

✅ Permisos granulares por funcionalidad

✅ Login seguro con autenticación

✅ Logs de actividad de usuarios

📤 Exportación Profesional
✅ Excel (📊 Verde): Listados completos y detallados

✅ PDF (📄 Rojo): Reportes resumidos horizontales

✅ Formatos optimizados para impresión y análisis

🛠️ Tecnología
Backend: Python 3.8+

Base de Datos: SQLite con arquitectura híbrida local/red

Interfaz: PyQt5 con diseño moderno

Exportación: Pandas + OpenPyXL + QtPrintSupport

🚀 Instalación Rápida
bash
# Clonar repositorio
git clone https://github.com/ramone77/inventario-agc.git

# Navegar al directorio
cd inventario-agc

# Ejecutar sistema
python main.py
⚙️ Configuración Inicial
Primer inicio: El sistema crea automáticamente la configuración

Modo de trabajo: Selecciona en ⚙️ Configuración → Modo Sincronización (Recomendado)

Usuario de prueba: mario / 1234 (admin)

📁 Estructura del Proyecto
text
inventario_agc/
├── 🏗️ core/                 # Lógica de negocio
│   ├── sync_manager.py     # 🆕 Sincronización inteligente
│   ├── bien_manager.py     # Gestión de bienes
│   └── movimiento_manager.py
├── 🗄️ database/            # Gestión de base de datos
│   └── db_manager.py
├── 🎨 ui/                  # Interfaz de usuario
│   ├── main_window.py      # Ventana principal
│   └── dialogs/            # Formularios y diálogos
├── ⚙️ config/              # Configuración del sistema
│   ├── config_manager.py
│   └── settings.py
└── 🔧 utils/               # Utilidades
    ├── excel_handler.py
    └── validators.py
🔄 Sistema de Sincronización
🎯 Arquitectura Híbrida
text
🏠 Local (Cache rápido) ←→ 🔄 Sincronización ←→ 🌐 Red (Base maestra)
     ↑                              ↑                      ↑
   Trabajo                      Control de              Colaboración
   diario                       conflictos               equipo
✅ Ventajas
⚡ Rendimiento máximo: Siempre trabajas localmente

💾 Resiliencia total: Si la red falla, sigues trabajando

👥 Colaboración sin conflictos: Sincronización controlada

📊 Tracking de cambios: Sabes quién hizo qué y cuándo

📞 Soporte
📧 Reportar issues: GitHub Issues

💡 Sugerencias: Siempre abiertas a mejoras

🔄 Actualizaciones: Sistema en constante evolución

🏆 Créditos
Sistema de Inventario AGC v2.0
Desarrollado con Python y PyQt5
Arquitectura profesional con sincronización inteligente