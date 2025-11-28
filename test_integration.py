"""
🧪 TEST DE INTEGRACIÓN - Movimientos con Actas Automáticas
"""

import os
import sys
from database.db_manager import DB
from core.movimiento_manager import MovimientoManager

def test_movimiento_con_acta():
    print("🧪 PROBANDO INTEGRACIÓN MOVIMIENTO + ACTA AUTOMÁTICA...")
    
    # Conectar a la BD
    db = DB("inventario_local.db", "actas_generadas")
    movimiento_mgr = MovimientoManager(db)
    
    # 🔍 ENCONTRAR UN BIEN VÁLIDO AUTOMÁTICAMENTE
    print("🔍 Buscando bienes en la base de datos...")
    bienes = db.list_bienes(limite=1)
    
    if not bienes:
        print("❌ No hay bienes en la base de datos. Agrega al menos uno primero.")
        return
    
    bien_id = bienes[0]['id']
    bienes_ids = [bien_id]
    
    print(f"✅ Bien encontrado - ID: {bien_id} | Ficha: {bienes[0]['ficha']} | Tipo: {bienes[0]['tipo']}")
    
    # Datos de prueba para un movimiento de ENTREGA
    datos_movimiento = {
        'tipo': 'Entrega',
        'fecha': '2024-01-15 10:00:00',
        'responsable': 'PEPE GOMEZ',
        'responsable_nombre': 'Pepe',
        'responsable_apellido': 'Gomez', 
        'responsable_dni_cuit': '30.123.456',
        'responsable_institucional': 'AREA DE SISTEMAS',
        'observaciones': 'Prueba de integración con acta automática',
        'numero_transferencia': 'TEST-001'
    }
    
    usuario_actual = "MARIO"  # Tu usuario
    
    print(f"📦 Creando movimiento de ENTREGA...")
    print(f"   Responsable: {datos_movimiento['responsable_nombre']} {datos_movimiento['responsable_apellido']}")
    print(f"   DNI: {datos_movimiento['responsable_dni_cuit']}")
    print(f"   Área: {datos_movimiento['responsable_institucional']}")
    
    # Crear movimiento (debería generar acta automáticamente)
    movimiento_id, mensaje = movimiento_mgr.crear_movimiento(
        datos_movimiento, 
        bienes_ids, 
        usuario_actual
    )
    
    print(f"📝 Resultado: {mensaje}")
    
    if movimiento_id:
        print(f"✅ Movimiento creado exitosamente: ID {movimiento_id}")
        
        # Verificar el historial del bien
        print(f"📊 Consultando historial del bien {bien_id}...")
        historial = movimiento_mgr.obtener_movimientos_por_bien(bien_id)
        
        if historial:
            print(f"✅ Historial encontrado: {len(historial)} movimiento(s)")
            
            for i, mov in enumerate(historial, 1):
                archivo = mov['archivo_path'] if mov['archivo_path'] else "SIN ARCHIVO"
                print(f"   {i}. {mov['fecha']}: {mov['tipo']}")
                print(f"      📎 Archivo: {archivo}")
                print(f"      👤 Responsable: {mov['responsable_nombre']} {mov['responsable_apellido']}")
        else:
            print("❌ No se encontró historial para el bien")
            
        # Verificar si se generó el archivo PDF
        if hasattr(db, 'obtener_movimiento_por_id'):
            movimiento_detalle = db.obtener_movimiento_por_id(movimiento_id)
            if movimiento_detalle and movimiento_detalle.get('archivo_path'):
                archivo_path = movimiento_detalle['archivo_path']
                if os.path.exists(archivo_path):
                    print(f"✅ ARCHIVO PDF GENERADO: {archivo_path}")
                else:
                    print(f"⚠️  Ruta de archivo existe en BD pero no en disco: {archivo_path}")
            else:
                print("⚠️  No se encontró ruta de archivo en el movimiento")
        else:
            print("ℹ️  Método obtener_movimiento_por_id no disponible en DB")
    
    else:
        print(f"❌ Error al crear movimiento: {mensaje}")
    
    print("🎯 TEST COMPLETADO")

def mostrar_metodo_auxiliar():
    """Muestra el método auxiliar para agregar a db_manager.py si es necesario"""
    metodo_auxiliar = '''
def obtener_movimiento_por_id(self, movimiento_id):
    """Obtiene un movimiento por su ID"""
    try:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM movimientos WHERE id = ?", (movimiento_id,))
        resultado = cur.fetchone()
        
        if resultado:
            columnas = [desc[0] for desc in cur.description]
            return dict(zip(columnas, resultado))
        return None
    except Exception as e:
        print(f"❌ Error obteniendo movimiento por ID: {e}")
        return None
'''
    print("\\n" + "="*50)
    print("📝 SI NECESITAS ESTE MÉTODO, AGREGALO A db_manager.py:")
    print(metodo_auxiliar)

if __name__ == "__main__":
    test_movimiento_con_acta()
    mostrar_metodo_auxiliar()