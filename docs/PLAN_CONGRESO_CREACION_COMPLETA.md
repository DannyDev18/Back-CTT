# Plan: Creación de Congresos con Relaciones (patrón "Curso Completo")

> **Objetivo:** Que la creación de un congreso funcione igual que la creación de un curso:
> una sola request que crea el congreso **junto con** sus sponsors y sesiones de cronograma,
> en una transacción atómica (todo o nada).

- **Fecha:** 2026-07-15
- **Estado:** Implementado (ver sección 6 — todos los criterios de aceptación cumplidos)
- **Rama sugerida:** `feature/congress-create-with-relations`

---

## 1. Contexto

### 1.1 Cómo funciona hoy la creación de un CURSO (patrón de referencia)

`POST /api/v1/courses` recibe un solo body con tres bloques y crea todo junto:

```json
{
  "course": { "title": "...", "category_id": 1, ... },
  "requirements": { "start_date_course": "...", ... },
  "contents": [ { "unit": "...", "title": "...", "topics": [] } ]
}
```

Flujo interno (ver `src/controllers/course_controller.py` → `create_course_with_requirements`):

1. Valida que la categoría exista (`CategoryRepository.get_by_id`).
2. Crea el `Course` principal.
3. Crea los `CourseRequirement` asociados vía repositorio.
4. Crea los `CourseContent` asociados vía repositorio.
5. Un solo `db.commit()` final + rollback en el router si algo falla.
6. Retorna el curso serializado **con todas sus relaciones**.

### 1.2 Cómo funciona hoy la creación de un CONGRESO (estado actual)

`POST /api/v1/congresses-new` solo crea la entidad `Congress` con sus campos básicos
(nombre, edición, año, fechas, descripción, poster). Las relaciones se crean por separado:

| Relación | Endpoint actual separado | Modelo |
|---|---|---|
| Sponsors | `/api/v1/congreso-sponsors` | `CongresoSponsor` (tabla pivote con `categoria` y `aporte`) |
| Sesiones | rutas de `sesion_cronograma_router.py` | `SesionCronograma` (requiere `id_congreso` + `id_speaker`) |
| Speakers | rutas de speakers | `Speaker` (se referencia por id, no se crea aquí) |

**Problema:** el frontend debe hacer N requests encadenadas y puede quedar un congreso
"huérfano" (sin sponsors/sesiones) si una request intermedia falla.

---

## 2. Fase 0 — Auditoría de la estructura actual y corrección de bugs

> **Antes de implementar lo nuevo**, revisar y corregir la base sobre la que se construye.
> Cada bug corregido debe llevar su test de regresión. Si un hallazgo es grande, abrir
> issue aparte para no bloquear esta feature.

### 2.0.1 Sospechas concretas ya identificadas (verificar y corregir)

| # | Sospecha | Ubicación | Impacto |
|---|---|---|---|
| B1 | `create_legacy_congress` genera `edicion = f"{title[:10]}-01"` → hasta 13 caracteres, pero la columna `edicion` es `max_length=10`. Puede fallar el INSERT o truncar según el motor de BD. | `congress_controller.py` (~línea 355) | Error 500 al crear congresos legacy con títulos largos |
| B2 | `delete_congress` no maneja relaciones: si el congreso tiene sponsors o sesiones, el DELETE viola las FKs (`congreso_sponsors.id_congreso`, `sesiones_cronograma.id_congreso`). No hay cascade configurado. | `congress_controller.py` / modelos | Error 500 al eliminar congresos con datos asociados |
| B3 | `serialize_to_dict` accede a `cs.sponsor` sin garantizar eager loading → posible N+1 o `DetachedInstanceError` según cómo cargue `get_congress_with_relations`. | `congress_controller.py` líneas 76–84 | Rendimiento / errores intermitentes en GET por id |
| B4 | El manejo del caso "Row vs objeto" (`congress[0]`) repetido en 7 métodos del controller sugiere que el repositorio devuelve tipos inconsistentes. Normalizar en el repositorio y eliminar los `hasattr(congress, 'id_congreso')`. | `congress_controller.py` | Código frágil; bugs silenciosos si cambia la query |
| B5 | Doble manejo de transacción: `BaseController.create` hace commit/rollback y el router vuelve a hacer `db.rollback()` en su except. Verificar que no oculte errores ni haga rollback sobre sesión ya cerrada. | `base_controller.py` + `congress_router.py` | Errores enmascarados |
| B6 | Decorador `@handle_controller_errors` envolviendo métodos que ya lanzan `HTTPException` → confirmar que no re-envuelve un 404 en un 500. | `base_controller.py` | Códigos de estado incorrectos |
| B7 | En el patrón de referencia (cursos): commit intermedio no atómico y `db.exec(...)` sobre `Session` de SQLAlchemy (método de SQLModel). Verificar que `SessionDep` sea del tipo correcto. **No copiar estos patrones al implementar congresos.** | `course_controller.py` líneas 62–83 | Referencia defectuosa |
| B8 | Enum `Jornada` y `SponsorCategory`: confirmar que los valores que valida el backend coinciden con los que la BD y el seed usan (`congreso_sponsor_seed.py` vs validator de `categoria`). | `models/base.py` + seeds | Seeds o requests válidas rechazadas |

### 2.0.2 Procedimiento de auditoría

1. Correr `pytest` completo y anotar el estado base (qué pasa y qué no, antes de tocar nada).
2. Verificar cada sospecha B1–B8 con un test o reproducción manual; marcar como
   **confirmada / descartada** en este documento.
3. Corregir las confirmadas **en commits separados** (un bug = un commit con su test),
   antes de empezar la sección 3.
4. Ejecutar la skill `/code-review` sobre los archivos de congress existentes
   (`congress_controller.py`, `congress_router.py`, `congress_repository.py`,
   `congreso_sponsor_*`, `sesion_cronograma_*`) para detectar bugs no listados aquí.
5. Al eliminar un congreso (B2): decidir política — borrado en cascada de sponsors/sesiones
   o bloquear con 409 si tiene datos asociados. **Propuesta: cascada para `congreso_sponsors`
   (tabla pivote) y 409 si hay sesiones.**

### 2.0.3 Registro de resultados de auditoría

Baseline `pytest` antes de tocar nada: **505 passed, 1 skipped** (sin fallos).

| # | Estado | Corrección aplicada / commit |
|---|---|---|
| B1 | ✅ Confirmada | `create_legacy_congress` genera hasta 13 caracteres (`title[:10]` + `-01`) para una columna `max_length=10`. Corregido: se recorta el prefijo del título a 7 caracteres antes de agregar `-01` (10 chars exacto). |
| B2 | ✅ Confirmada | No había política de borrado con relaciones. Corregido: `delete_congress` borra en cascada `congreso_sponsors` y bloquea con 409 si existen `sesiones_cronograma` **o `speakers`** asociados. El caso de `speakers` no estaba en la sospecha original ni en los tests de SQLite (que no fuerzan FKs) — se descubrió al verificar en vivo contra SQL Server real: `speakers.id_congreso` es `NOT NULL`, y sin el chequeo, `db.delete(congress)` hacía que SQLAlchemy intentara poner `NULL` en esa columna al desasociar la relación, produciendo un `IntegrityError` → 500. |
| B3 | ✅ Confirmada | `get_upcoming_congresses(include_details=True)` no cargaba `CongresoSponsor.sponsor` (a diferencia de `get_congress_with_relations`), y `serialize_to_dict` accede a `cs.sponsor.nombre`. Corregido: se agrega `.selectinload(CongresoSponsor.sponsor)` también ahí. |
| B4 | ✅ Confirmada | Causa raíz real (no la sospechada): `congress_repository.py` importa `select` de **`sqlalchemy`** (no de `sqlmodel`), y dos métodos (`get_congresses_paginated`, `get_upcoming_congresses`) hacían `db.exec(query...).all()` sin `.scalars()` — con `select` de SQLAlchemy eso sí devuelve `Row`, a diferencia del resto de métodos que usan `db.execute(...).scalars()`. El `hasattr(...) else congress[0]` del controller enmascaraba el síntoma. Corregido: ambos métodos ahora usan `db.execute(query...).scalars().all()` (consistente con el resto del archivo), y se elimina el patrón defensivo del controller en las 7 ubicaciones. |
| B5 | ⬜ Descartada | `db.rollback()` es idempotente cuando no hay transacción activa; `BaseController.create/update/delete` ya hacen su propio rollback antes de propagar la excepción, por lo que el rollback adicional del router es un no-op seguro, no enmascara errores. |
| B6 | ⬜ Descartada | `handle_controller_errors` tiene `except HTTPException: raise` explícito antes de capturar `Exception`, por lo que un 404 no se re-envuelve en 500. |
| B7 | ⬜ Descartada | Es una nota de referencia sobre `course_controller.py`, no un bug de `congress`. Se tiene en cuenta en el diseño de la sección 3.3 (flush + commit único). |
| B8 | ⬜ Descartada | Los valores de `SponsorCategory` (`oro`, `plata`, `bronce`, `colaborador`) y `Jornada` (`mañana`, `tarde`, `noche`) usados en los seeds coinciden exactamente con los enums de `models/base.py`. |

---

## 3. Diseño propuesto

### 3.1 Nuevo contrato del endpoint

`POST /api/v1/congresses-new` (se extiende el body actual, retrocompatible: `sponsors` y `sessions` son opcionales con default `[]`):

```json
{
  "congress": {
    "nombre": "Congreso Internacional de Teología 2026",
    "edicion": "CIT-2026",
    "anio": 2026,
    "fecha_inicio": "2026-03-15",
    "fecha_fin": "2026-03-17",
    "descripcion_general": "…",
    "poster_cover_url": "https://…"
  },
  "sponsors": [
    { "id_sponsor": 1, "categoria": "oro", "aporte": 5000.00 },
    { "id_sponsor": 2, "categoria": "plata", "aporte": 2500.00 }
  ],
  "sessions": [
    {
      "id_speaker": 3,
      "fecha": "2026-03-15",
      "hora_inicio": "09:00",
      "hora_fin": "10:30",
      "titulo_sesion": "Conferencia inaugural",
      "jornada": "matutina",
      "lugar": "Auditorio principal"
    }
  ]
}
```

**Decisión clave:** los sponsors y speakers se **referencian por id** (ya deben existir),
igual que los cursos referencian `category_id`. No se crean sponsors/speakers inline.

### 3.2 Modelos Pydantic nuevos

En `src/models/congreso_sponsor_model.py`:

- `CongresoSponsorNested(BaseModel)` — igual a `CongresoSponsorCreate` pero **sin** `id_congreso`
  (el id lo pone el controller después de crear el congreso). Reutilizar los validators de
  `categoria` (enum `SponsorCategory`) y `aporte` (rango 0–999999.99).

En `src/models/sesion_cronograma_model.py`:

- `SesionCronogramaNested(BaseModel)` — igual a `SesionCronogramaCreate` pero **sin** `id_congreso`.
  Reutilizar validators de horas, título, jornada (enum `Jornada`) y lugar.

En `src/routes/congress_router.py`:

```python
class CongressCreateRequest(BaseModel):
    congress: CongressCreate
    sponsors: List[CongresoSponsorNested] = Field(default_factory=list)
    sessions: List[SesionCronogramaNested] = Field(default_factory=list)
```

(Se modifica el request existente que hoy solo tiene `congress`.)

### 3.3 Controller

Nuevo método en `src/controllers/congress_controller.py`, espejo de
`create_course_with_requirements`:

```python
@handle_controller_errors
def create_congress_with_relations(
    self,
    db: Session,
    congress_data: CongressCreate,
    sponsors_data: List[CongresoSponsorNested],
    sessions_data: List[SesionCronogramaNested],
    current_user_id: Optional[int] = None,
) -> Dict[str, Any]:
```

Pasos internos (en orden, **un solo commit al final**):

1. **Validaciones previas** (antes de escribir nada):
   - `check_edition_exists(edicion, anio)` → error 400 si ya existe (ya implementado en `_validate_before_create`).
   - `fecha_fin > fecha_inicio` (ya cubierto por el validator Pydantic + `_validate_before_create`).
   - Cada `id_sponsor` existe (`sponsor_repository.get`), sin ids duplicados en la lista → 404/400.
   - Cada `id_speaker` existe (`speaker_repository.get`) → 404.
   - Cada sesión: `fecha` dentro del rango `[fecha_inicio, fecha_fin]` del congreso → 400.
2. Crear `Congress` con `db.add()` + `db.flush()` (flush, **no** commit, para obtener `id_congreso`).
3. Crear cada `CongresoSponsor(id_congreso=nuevo_id, ...)` con `db.add()`.
4. Crear cada `SesionCronograma(id_congreso=nuevo_id, ...)` con `db.add()`.
5. `db.commit()` único + `db.refresh(congress)`.
6. Recargar con `congress_repository.get_congress_with_relations(db, id)` y retornar
   `self.serialize_to_dict(congress, include_relations=True)` — el serializer **ya soporta**
   speakers, sesiones y sponsors (líneas 48–84 del controller actual).

> ⚠️ **Atomicidad:** a diferencia del controller de cursos (que hace `commit` intermedio tras
> crear el curso), aquí se usa `flush()` intermedio y **un solo commit**, para que un fallo en
> sponsors/sesiones no deje un congreso huérfano. El router ya hace `db.rollback()` en `except`.

### 3.4 Router

En `src/routes/congress_router.py`:

- Modificar `CongressCreateRequest` (agregar `sponsors` y `sessions` opcionales).
- Modificar el handler `create_congress` para pasar las listas al nuevo método del controller.
- Actualizar `summary`/`description`/docstring del endpoint: "Crea un congreso completo con
  sponsors y sesiones de cronograma".
- La respuesta `CongressResponse.data` ahora incluye `sponsors` y `sesiones` serializados.

### 3.5 Seed

**Decisión de implementación:** se mantiene `congreso_sponsor_seed.py` y
`sesion_cronograma_seed.py` tal como están, sin moverlos a `congress_seed.py`.

Motivo: ambos ya son idempotentes (verifican existencia antes de crear —
`existing_count`/`created_count` con mensajes "already exists") y el orden en
`main_seed.py` ya es correcto: `seed_congresses()` → `seed_sponsors()` →
`seed_speakers()` → `seed_sesion_cronograma()` → `seed_congreso_sponsor()`
(`src/utils/seeds/main_seed.py` líneas 80–100). Reescribirlos para pasar por
`create_congress_with_relations` duplicaría lógica de generación de datos de
prueba ya validada, sin ganancia funcional: el objetivo de esta fase era el
endpoint, no el reemplazo de los seeds existentes. Si en el futuro se agrega un
seed nuevo con datos, debe usarse el mismo patrón idempotente ya presente en
estos dos archivos.

---

## 4. Archivos a modificar

| # | Archivo | Cambio |
|---|---|---|
| 1 | `src/models/congreso_sponsor_model.py` | Agregar `CongresoSponsorNested` |
| 2 | `src/models/sesion_cronograma_model.py` | Agregar `SesionCronogramaNested` |
| 3 | `src/controllers/congress_controller.py` | Agregar `create_congress_with_relations` |
| 4 | `src/routes/congress_router.py` | Extender `CongressCreateRequest` y handler POST |
| 5 | `src/utils/seeds/congress_seed.py` | Seed con relaciones, idempotente |
| 6 | `src/utils/seeds/main_seed.py` | Revisar orden de seeds (sponsors/speakers → congresos) |
| 7 | `tests/test_controllers/test_congress_controller.py` | Tests nuevos del controller |
| 8 | `tests/test_routes/test_congress_router.py` | Tests nuevos del endpoint |
| 9 | `docs/QUICK_REFERENCE.md` / `docs/ROUTES_TESTING_GUIDE.md` | Documentar nuevo body |

**No se modifican:** modelos SQLModel de tablas (el esquema de BD ya soporta todo),
repositorios (se usan los existentes), endpoints separados de sponsors/sesiones
(siguen funcionando para agregar/editar después de crear).

---

## 5. Plan de pruebas

### 5.1 Tests unitarios del controller (`test_congress_controller.py`)

1. ✅ Crear congreso **sin** sponsors ni sesiones (retrocompatibilidad) → igual que hoy.
2. ✅ Crear congreso con 2 sponsors y 2 sesiones → respuesta incluye ambos, BD contiene los registros.
3. ❌ `id_sponsor` inexistente → 404 y **no** se crea el congreso (verificar rollback).
4. ❌ `id_speaker` inexistente → 404 y no se crea el congreso.
5. ❌ Sesión con fecha fuera del rango del congreso → 400.
6. ❌ Sponsor duplicado en la lista (mismo `id_sponsor` dos veces) → 400 (violaría PK compuesta).
7. ❌ `categoria` de sponsor inválida / `aporte` negativo → 422 (validator Pydantic).
8. ❌ Edición+año duplicados → 400 (validación existente sigue funcionando).

### 5.2 Tests de ruta (`test_congress_router.py`)

1. POST con body completo → 201, `data` contiene `sponsors` y `sesiones`.
2. POST con body legacy (solo `congress`) → 201 (retrocompatible).
3. POST sin token → 401.
4. GET `/{id}` después de crear → relaciones visibles.

### 5.3 Verificación manual (skill `/verify` al terminar)

```bash
# 1. Levantar el server y sembrar
python -m src.utils.seeds.main_seed
# 2. Login para obtener token, luego:
curl -X POST http://localhost:8000/api/v1/congresses-new \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d @docs/ejemplos/congreso_completo.json
# 3. GET /api/v1/congresses-new/{id} → confirmar sponsors y sesiones
```

---

## 6. Criterios de aceptación

- [x] Auditoría Fase 0 completada: cada sospecha B1–B8 marcada como confirmada/descartada
      en la tabla 2.0.3, y todas las confirmadas corregidas con test de regresión.
- [x] `POST /api/v1/congresses-new` acepta `congress` + `sponsors` + `sessions` en un solo body.
- [x] La operación es **atómica**: si falla cualquier parte, no queda ningún registro en BD.
- [x] El body antiguo (solo `congress`) sigue funcionando sin cambios (retrocompatible).
- [x] La respuesta del POST y del GET por id incluyen sponsors y sesiones serializados.
- [x] Sponsors y speakers inexistentes producen 404 con mensaje claro; datos inválidos producen 400/422.
- [x] El seed crea congresos con relaciones y es idempotente (correr dos veces no duplica) —
      ver decisión en sección 3.5: se mantienen los seeds existentes, ya idempotentes.
- [x] Todos los tests existentes siguen pasando (`pytest`) + los nuevos tests pasan (519 passed, 1 skipped).
- [x] Documentación de rutas actualizada (`ROUTES_TESTING_GUIDE.md`).

---

## 7. Riesgos y decisiones abiertas

| Riesgo / Decisión | Mitigación / Propuesta |
|---|---|
| El controller de cursos hace commit intermedio (no atómico); copiarlo tal cual replicaría el bug (B7) | Usar `flush()` + commit único (sección 3.3) |
| `congreso_sponsor_seed.py` quedaría redundante si el seed de congresos asocia sponsors | Decidir en implementación: deprecarlo o dejarlo solo para asociaciones extra |
| PK compuesta de `congreso_sponsors` truena con sponsors duplicados en la lista | Validar duplicados antes del insert → error 400 legible |
| `SesionCronogramaCreate` exige `id_congreso` que aún no existe al validar el body | Por eso se crean los modelos `*Nested` sin ese campo |
| Enums `SponsorCategory` y `Jornada` deben coincidir con lo que envía el frontend | Reutilizar los validators existentes; documentar valores válidos en el endpoint |

---

## 8. Orden de ejecución sugerido

1. Crear rama `feature/congress-create-with-relations`.
2. **Fase 0 (sección 2)**: correr `pytest` base, auditar B1–B8, correr `/code-review`
   sobre los archivos existentes de congress, y corregir los bugs confirmados
   (un bug = un commit con su test de regresión). Actualizar la tabla 2.0.3.
3. Paso 1–2: modelos `*Nested` (archivos 1 y 2). Correr `pytest` — nada debe romperse.
4. Paso 3: método del controller con validaciones + transacción única.
5. Paso 4: router (request model + handler). Probar manualmente con Swagger (`/docs`).
6. Paso 5–6: seeds y orden en `main_seed.py`. Correr seed dos veces → verificar idempotencia.
7. Paso 7–8: tests unitarios y de ruta. `pytest` completo en verde.
8. Paso 9: actualizar documentación.
9. `/code-review` del diff + `/verify` end-to-end antes del PR.
