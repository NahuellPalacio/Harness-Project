## Cómo se trabaja en este repo

Español rioplatense, de vos. Conciso.

**No inventar.** Se escribe únicamente lo que la fuente sostiene — la maqueta, el
documento, el código. Si falta un dato, se anota como definición pendiente; nunca se
completa por analogía ni por sentido común. Un hueco señalado se resuelve preguntando;
un dato inventado se lee bien, nadie lo cuestiona y se construye.

**Ningún secreto entra al repo.** Tokens, claves y contraseñas se nombran por su variable
de entorno, jamás por su valor. Es lo único que el harness bloquea en vez de avisar.

**Lo que se aprende queda escrito.** Lo durable va a la zona de caché de este archivo, y
de ahí al directorio de conocimiento del proyecto. Lo que solo sirve para esta sesión, no.

## Las zonas de este archivo

Este archivo se carga entero al abrir la sesión y ocupa ventana de contexto mientras dure.
Por eso está partido en zonas con política distinta, cada una con su techo:

| Zona | Qué va | Techo |
|---|---|---|
| `ZONA FIJA` | Reglas que deben **ejecutarse** cada turno, no solo saberse | 60 líneas |
| `ZONA MAPA` | Dónde está cada cosa. Se verifica contra el disco | 20 líneas |
| `ZONA ÍNDICE` | Un puntero por nota del directorio de conocimiento | 25 líneas |
| `ZONA CACHÉ` | Purgable. Lo que se aprende durante el trabajo | 80 líneas |

**La invariante:** nunca se desaloja lo que no se escribió. Antes de borrar algo de la
caché hay que poder señalar el archivo que contiene cada hecho. Ante la duda, no se borra —
un archivo grande cuesta tokens, una purga mal hecha pierde conocimiento y nadie se entera.

📌 **Lo que no se necesita en cada turno no va acá: va en una skill.** Una skill cuesta unos
100 tokens de nombre y descripción, y se expande solo cuando alguien la invoca.
