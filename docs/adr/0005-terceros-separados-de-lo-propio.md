---
estado: aceptada
creado: 2026-08-10
---

# ADR-0005 — Lo bajado de terceros vive separado de lo propio

## Contexto

Parte del harness va a incorporar material de repositorios públicos: listas de patrones,
skills, convenciones, checks. Hay trabajo hecho por otros que es bueno y que no tiene
sentido reescribir.

Pero el material de un harness no es una librería que se llama desde el código. **Una skill
o un agente es texto que el modelo lee y obedece.** Un `SKILL.md` bajado de GitHub entra al
contexto con la misma autoridad que uno escrito acá, y va a correr en máquinas de un
organismo público, sobre repositorios con datos de ciudadanos.

Sin separación aparecen cuatro problemas, todos silenciosos:

1. **No se sabe qué se auditó.** A los seis meses nadie distingue lo que escribimos de lo
   que heredamos, y por lo tanto nadie sabe qué se revisó línea por línea.
2. **Actualizar pisa trabajo propio.** Si alguien ajusta un archivo bajado y después se
   trae una versión nueva del upstream, el ajuste se pierde sin dejar rastro.
3. **No hay respuesta para la pregunta de licencia.** "¿De dónde salió esto y bajo qué
   licencia lo estamos usando?" es una pregunta que ASI puede hacer, y hay que poder
   contestarla con un commit exacto.
4. **El diff de una actualización se vuelve ilegible**, porque mezcla cambios del upstream
   con cambios nuestros.

## Decisión

**Todo lo que viene de afuera vive en `terceros/`, y esa carpeta es material de
referencia, no fuente de instalación.**

Tres reglas:

### 1. `terceros/` no se instala

`install.ps1` solo copia desde `comun/` y `harnesses/<id>/`. Lo que se toma de terceros se
copia a lo propio con una nota de procedencia en el encabezado.

Se evaluó permitir instalar directamente desde `terceros/` para no duplicar. Se descarta:
duplicar unos kilobytes es barato, y tener **una sola ruta de instalación** vale más que
ahorrarlos. Además obliga a que alguien mire el archivo al copiarlo, que es exactamente el
momento en que hay que mirarlo.

### 2. Lo de terceros no se edita en su lugar

Nunca. Si hay que adaptar algo, se copia a `comun/` o `harnesses/<id>/` y se adapta ahí.

Así, traer una versión nueva del upstream es siempre seguro: no puede pisar trabajo propio,
y el `git diff` muestra únicamente lo que cambió del otro lado.

### 3. Nada entra sin procedencia registrada

`terceros/terceros.lock.json` anota, por cada origen: repositorio, **commit exacto**,
licencia, fecha de incorporación, qué se tomó y qué se dejó, y quién lo revisó.

Y la condición previa: **se lee entero antes de incorporarlo.** No "se hojea el README" —
se lee lo que se va a incorporar. Para un `SKILL.md` de 200 líneas eso son diez minutos, y
es la única defensa real contra una instrucción hostil escondida en el medio.

## Consecuencias

**A favor:**
- Se puede contestar en cualquier momento qué es propio, qué es heredado, de qué commit y
  bajo qué licencia.
- Actualizar desde el upstream nunca pierde trabajo local.
- Queda un punto obligatorio de lectura antes de que material ajeno entre al contexto de un
  agente.
- El material de referencia queda versionado y disponible aunque el repo original desaparezca.

**En contra:**
- Duplicación entre `terceros/` y lo propio cuando algo se usa tal cual.
- Hay que mantener el lockfile a mano. Un origen sin registrar es peor que no tener el
  mecanismo, porque da falsa sensación de control.
- Más fricción para incorporar algo. Es deliberada.

## Revisión

Se revisa si el volumen de material de terceros crece hasta que la copia manual sea el
cuello de botella. En ese caso la salida es un script que copie desde `terceros/` dejando
la nota de procedencia automáticamente — **no** permitir instalar desde `terceros/`, que es
la parte que da la garantía.
