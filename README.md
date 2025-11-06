# 🏢 Sistema de Inventario AGC

**Sistema profesional de gestión de inventario** para la Agencia Gubernamental de Control - Desarrollado en Python/PyQt5

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![PyQt5](https://img.shields.io/badge/PyQt5-GUI-green?logo=qt)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightgrey?logo=sqlite)
![Status](https://img.shields.io/badge/Status-Operativo-success)

## 📋 Características Principales

### ✅ **Módulos Implementados**
- **🔐 Sistema de Autenticación** - Roles: Admin, Supervisor, Operador
- **📦 Gestión de Bienes** - Registro completo con datos patrimoniales
- **🔄 Sistema de Movimientos** - Entregas, devoluciones, bajas, transferencias
- **🔍 Búsqueda Avanzada** - Panel de filtros múltiples
- **📊 Dashboard Ejecutivo** - Estadísticas y KPIs
- **📥📤 Importación/Exportación** - Excel integration

### 🎨 **Interfaz Profesional**
- **Interfaz moderna** con PyQt5
- **Pestañas organizadas** para mejor flujo de trabajo
- **Paginación inteligente** para mejor rendimiento
- **Responsive design** adaptable a diferentes pantallas

### ⚙️ **Características Técnicas**
- **Base de datos SQLite** robusta y portable
- **Modo LOCAL/RED** configuración flexible
- **Sistema de backups** automático
- **Arquitectura modular** fácil de mantener

## 🚀 Instalación y Uso

### **Requisitos Previos**
```bash
Python 3.8+
PyQt5
pandas

Instalación de Dependencias: pip install PyQt5 pandas openpyxl
Ejecutar la Aplicación:python main.py

Credenciales de Prueba: Usuario: mario Contraseña: 1234

 Estructura del Proyecto: 
inventario_agc/
├── 📱 main.py                          # Punto de entrada
├── ⚙️ config/                          # Configuración del sistema
├── 🗄️ database/                       # Gestión de base de datos
├── 🏗️ core/                           # Lógica de negocio
├── 🎨 ui/                             # Interfaz de usuario
├── 🔧 utils/                          # Utilidades y helpers
└── 📊 widgets/                        # Componentes personalizados

🗃️ Esquema de Base de Datos

bienes - Inventario completo de bienes

movimientos - Historial de operaciones

usuarios - Control de acceso y roles

bienes_movimientos - Relación muchos a muchos

logs_actividad - Auditoría del sistema

✅ Funcionalidades Completadas
Sistema de login y autenticación

CRUD completo de bienes

Gestión de movimientos

Interfaz principal con pestañas

Base de datos con auto-inicialización

Sistema de configuración LOCAL/RED

Importación masiva desde Excel

Exportación a Excel

🔧 Próximas Mejoras
Implementación completa de filtros avanzados

Sistema de reportes PDF

Gráficos interactivos en dashboard

Búsqueda en tiempo real

Configuración de columnas visibles

Sistema de notificaciones
👥 Roles y Permisos
Rol	Permisos
Admin	Acceso completo, configuración, exportación
Supervisor	Gestión de bienes, movimientos, reportes
Operador	Consulta y registro básico
📞 Soporte y Contacto
Si encuentras algún problema o tienes sugerencias:

Revisa los issues

Crea un nuevo issue describiendo el problema

O contacta al equipo de desarrollo

📄 Licencia
Este proyecto es de uso interno para la Agencia Gubernamental de Control.
