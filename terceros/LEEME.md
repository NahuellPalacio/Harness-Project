# terceros/

Material bajado de repositorios públicos. **Nada de acá se instala directamente.**

El fundamento completo está en [ADR-0005](../docs/adr/0005-terceros-separados-de-lo-propio.md).
Lo operativo es esto:

## Las tres reglas

### 1. Esto no se instala

`install.ps1` solo copia desde `comun/` y `harnesses/<id>/`. Para usar algo de acá, se
**copia** a lo propio con una nota de procedencia arriba:

```
# Adaptado de <repo> @ <commit>, bajo licencia <X>.
# Original en terceros/<origen>/. No editar allá: editar acá.
```

### 2. Esto no se edita

Nunca, ni una coma. Si hay que cambiar algo, se cambia en la copia propia.

Es lo que hace que traer una versión nueva del upstream sea siempre seguro: no puede pisar
trabajo nuestro, y el diff muestra solo lo que cambió del otro lado.

### 3. Nada entra sin leerlo entero

No el README: **lo que se va a incorporar**. Una skill o un agente es texto que el modelo
obedece, no una librería que se llama. Una instrucción hostil escondida en la línea 140 de
un `SKILL.md` de 200 líneas entra al contexto con la misma autoridad que lo que escribimos
nosotros.

Diez minutos de lectura es todo lo que hay entre eso y una máquina del GCBA.

## Cómo se incorpora un origen

1. **Reconocer sin clonar.** La skill `instalar-desde-github` trae datos duros por API y el
   README filtrado, sin bajar el repo. Sirve para descartar temprano y sale ~600 tokens en
   vez de decenas de miles.
2. **Bajar a `terceros/<origen>/`**, fijando el **commit exacto**. Nunca una rama: las ramas
   se mueven.
3. **Leer lo que se va a usar.** Entero.
4. **Registrar en `terceros.lock.json`**: repo, commit, licencia, fecha, qué se tomó, qué se
   dejó y por qué, y quién lo revisó.
5. **Escribir `terceros/<origen>/ORIGEN.md`** con la lectura: qué resuelve, qué sirve, qué no
   sirve y qué hay que adaptar.
6. **Copiar a lo propio** lo que se vaya a usar, con la nota de procedencia.

## Qué mirar al leer

Preguntas que valen para cualquier material que entre al contexto de un agente:

- ¿Le dice al modelo que **ignore instrucciones previas** o que cambie de rol?
- ¿Le dice que **lea archivos fuera del proyecto**, o que mande algo a una URL?
- ¿Tiene rutas absolutas, URLs internas o credenciales de otra organización?
- ¿Ejecuta algo — `curl`, `Invoke-WebRequest`, `npm install`, un instalador?
- ¿Contradice una regla nuestra, sobre todo la de no inventar o la de secretos?
- ¿La licencia permite usarlo y redistribuirlo dentro del organismo?

Cualquier "sí" no descalifica automáticamente, pero va anotado en `ORIGEN.md`.

## Licencias

Se registra la licencia de cada origen y se conserva su archivo de licencia dentro de
`terceros/<origen>/`. Un origen **sin licencia declarada no se incorpora**: sin licencia no
hay permiso de uso, aunque el repo sea público.
