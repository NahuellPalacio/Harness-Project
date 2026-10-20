"""El contexto Knowledge Access: una frontera de solo lectura que responde una consulta sobre corpus declarados.

Es de Task 6 (docs/cambios/knowledge-api/spec.md; ADR-0017). Dos operaciones, `lookup` y `search`, en
una interfaz Python interna: sin REST, sin CLI y sin capability. Cada item que devuelve trae su cita, su
revision y su tramo literal, y lo que no se pudo mirar se declara.

    corpus.py            el catalogo cerrado de corpus, la contencion, el deny, el lector de una sola
                         lectura y los topes de la consulta
    recuperador_local.py el puerto del recuperador y `local-lexico/1`
    acceso.py            la fachada: `lookup`, `search` y el contrato `knowledge-result/1.0`

🔴 Sin estado y sin persistencia: no escribe, no imprime y no guarda nada entre dos consultas.
"""
