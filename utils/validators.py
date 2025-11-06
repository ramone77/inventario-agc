"""
🔧 VALIDADORES - Sistema de Inventario AGC
Funciones de validación de datos
"""

import re
from datetime import datetime


def validar_email(email):
    """Valida formato de email"""
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(patron, email) is not None


def validar_cuit(cuit):
    """Valida formato de CUIT (XX-XXXXXXXX-X)"""
    patron = r'^\d{2}-\d{8}-\d{1}$'
    return re.match(patron, cuit) is not None


def validar_fecha_argentina(fecha_str):
    """Valida fecha en formato argentino DD/MM/AAAA"""
    try:
        datetime.strptime(fecha_str, "%d/%m/%Y")
        return True
    except ValueError:
        return False


def validar_numero_positivo(valor):
    """Valida que sea un número positivo"""
    try:
        numero = float(valor)
        return numero >= 0
    except (ValueError, TypeError):
        return False


def validar_texto_no_vacio(texto):
    """Valida que el texto no esté vacío"""
    return texto is not None and str(texto).strip() != ""