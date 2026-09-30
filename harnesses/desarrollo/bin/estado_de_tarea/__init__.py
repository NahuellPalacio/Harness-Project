"""Donde se guarda el estado del flujo de cada tarea, y el puntero a la tarea activa.

Vive afuera de `flujo/` a proposito: `flujo/` no escribe nada (E-18 de
docs/cambios/flujo-precondiciones). Lo que se guarda aca lo deriva `flujo/estado.py`; este
paquete solo lo reconcilia contra lo guardado y lo escribe sin dejar medio archivo.
"""
