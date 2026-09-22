"""El borde de traduccion entre un proveedor y la contabilidad.

Todo lo que sabe de un formato concreto vive de este lado. El nucleo recibe eventos
normalizados y no sabe de donde salieron: es lo que permite que el proveedor numero tres se
agregue sin tocar una sola linea de la agregacion, del motor de costos ni del reporte.

🔴 Lo desconocido sale `USAGE_UNRESOLVED`, nunca cero. Un adaptador que rellena con ceros
lo que no pudo leer produce una tarea que salio barata.
"""
