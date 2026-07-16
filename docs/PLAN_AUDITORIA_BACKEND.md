# Plan: Auditoría integral del backend — corrección de bugs y mejoras

> **Objetivo:** Revisar sistemáticamente todo el backend (controllers, repositorios,
> modelos, seeds, tests e infraestructura de arranque), corregir los bugs confirmados
> con tests de regresión, y aplicar mejoras estructurales que eliminen las clases de
> bug de raíz — no solo sus síntomas.

- **Fecha:** 2026-07-16
- **Estado:** Pendiente de implementación
- **Rama sugerida:** `feature/backend-audit-hardening`
- **Antecedente:** Plan de congresos (`PLAN_CONGRESO_CREACION_COMPLETA.md`), cuya
  Fase 0 y verificación en vivo revelaron **clases de bug** que se repiten en el
  resto de los módulos. Este plan generaliza esas correcciones.

---

## 1. Contexto y lecciones del plan anterior

La auditoría y verificación en vivo del módulo de congresos (rama
`feature/congress-create-with-relations`) demostró tres cosas que motivan este plan:

1. **El patrón `Row` vs modelo está en todo el código.** El bug B4 de congresos
   (repositorios que mezclan `select` de SQLAlchemy con `db.exec(...).all()` sin
   `.scalars()`, devolviendo `Row` en vez de instancias de modelo) fue corregido
   **solo** en `congress_repository.py`. Los demás repositorios tienen el mismo
   defecto y sus controllers lo enmascaran con `hasattr(x, 'id') else x[0]`.
2. **Los deletes sin política de FKs producen 500 en SQL Server real.** El caso
   `delete_congress` con speakers asociados devolvía 500 por `IntegrityError` — y
   los tests con SQLite **no lo detectaron** porque SQLite no aplica FKs por defecto.
   `delete_speaker`, `delete_sponsor` y `delete_session` usan el `self.delete`
   genérico sin ninguna verificación de dependientes: misma clase de bug.
3. **Un seed defectuoso impide arrancar la API.** Durante la verificación en vivo,
   `enrollment_seed.py` crasheó el contenedor en el arranque (exit 3) con
   `ValueError: empty range` en `random.randint`. Los seeds corren en el `lifespan`
   de FastAPI: cualquier excepción no controlada tumba el servicio completo.

---

## 2. Fase 0 — Línea base y preparación

1. **Resolver el estado sucio del working tree** (previo a todo): hay cambios sin
   commitear que parecen ser el trabajo de migraciones Alembic en curso
   (`requirements.txt`, `scripts/wait-for-sql.sh`, `src/main.py` modificados;
   `alembic.ini` y `alembic/` sin trackear; `debug_sponsor_get_by_id.py` borrado).
   **Decidir con el usuario:** commitear ese trabajo en su propia rama/commit, o
   stashearlo. No mezclarlo con esta auditoría.
2. Correr `pytest` completo y registrar la línea base (última conocida: **520 passed,
   1 skipped** tras el plan de congresos).
3. Crear la rama `feature/backend-audit-hardening` desde `main` actualizado (una vez
   mergeado el PR de congresos, para heredar sus fixes).

---

## 3. Fase 1 — Bugs confirmados/sospechados (P0–P1)

> Cada bug corregido lleva su test de regresión. **Un bug = un commit.**
> Verificar cada sospecha antes de corregir y registrar el resultado en la tabla 6.

### 3.1 Catálogo de sospechas

| # | Prioridad | Sospecha | Ubicación | Evidencia / Impacto |
|---|---|---|---|---|
| A1 | **P0** | Repositorios devuelven `Row` en vez de instancias de modelo: importan `select` de `sqlalchemy` (no de `sqlmodel`) y varios métodos hacen `db.exec(query...).all()` sin `.scalars()`. Es el mismo bug B4 de congresos, ya confirmado y corregido allí. | `speaker_repository.py` (líneas ~123, 225, 241, 318), `sponsor_repository.py` (~103, 121, 158, 198, 283), `sesion_cronograma_repository.py` (~128, 153, 176, 248, 281), `congreso_sponsor_repository.py` (~182, 302, 339, 380) | Confirmado por inspección: mismos imports y mismo patrón que el bug ya reproducido en congress. Los controllers lo enmascaran (ver A2). Riesgo de 500 intermitente si se quita el enmascaramiento o cambia una query. |
| A2 | **P0** | Patrón defensivo muerto `x if hasattr(x, 'id_*') else x[0]` repetido en los controllers, enmascarando A1. Eliminarlo **después** de corregir A1. | `speaker_controller.py` (8 sitios), `sponsor_controller.py` (6 sitios), `sesion_cronograma_controller.py` (7 sitios) | Código frágil que oculta la inconsistencia real del repositorio; idéntico al B4 ya corregido en congress. |
| A3 | **P0** | `delete_speaker` sin política de FKs: un speaker con sesiones (`sesiones_cronograma.id_speaker` NOT NULL) produce `IntegrityError` → 500 en SQL Server real. | `speaker_controller.py:324` | Misma clase del bug encontrado **en vivo** al borrar congresos con speakers. Política propuesta: **409** si tiene sesiones. |
| A4 | **P0** | `delete_sponsor` sin política de FKs: un sponsor con registros en `congreso_sponsors` viola la FK al borrarse. | `sponsor_controller.py:223` | Política propuesta: **cascada** sobre `congreso_sponsors` (tabla pivote, consistente con la política de `delete_congress`). |
| A5 | **P0** | Seeds corren dentro del `lifespan` de FastAPI sin aislamiento: una excepción en cualquier seed impide el arranque de la API (contenedor sale con exit code ≠ 0). | `src/main.py` (lifespan, líneas ~58–70) | **Observado en vivo**: crash de `enrollment_seed` → contenedor muerto. Envolver cada seed en try/except con log del error, o mover los seeds a un comando explícito (`python -m src.utils.seeds.main_seed`) fuera del arranque. |
| A6 | **P1** | `enrollment_seed.py`: `random.randint(10, min(150, len(users) // 2))` lanza `ValueError: empty range` cuando hay pocos usuarios de plataforma (`len(users)//2 < 10`) y existe un congreso futuro. Además, las estadísticas impresas superan el 100% (ej. "Interesado: 172.2%") — el denominador está mal. | `src/utils/seeds/enrollment_seed.py:101` (randint) y bloque de estadísticas | **Observado en vivo** (crash real durante la verificación de congresos). Usar `random.randint(min(10, n), n)` con `n = max(1, ...)` y corregir el denominador de porcentajes. |
| A7 | **P1** | Doble manejo de transacciones: `BaseRepository.create/update/delete/bulk_create` hacen `db.commit()` propio **y** `BaseController.create/update/delete` vuelven a hacer `commit`. Contradice la convención de capas del proyecto (los repositorios no deben commitear) y rompe cualquier intento de componer operaciones atómicas sobre esos métodos. | `base_repository.py:117, 135, 144, 210` + `base_controller.py:57, 170, 214` | Riesgo real: un flujo "todo o nada" que reutilice `repository.create` persiste a mitad de camino (es exactamente el bug B7 documentado en el controller de cursos). Quitar los commits del repositorio y dejar la transacción solo en el controller. Revisar todos los call sites al hacerlo. |
| A8 | **P1** | `handle_repository_errors` envuelve **cualquier** excepción en `RepositoryError(f"...")`, destruyendo el tipo original: un `IntegrityError`, un `ValueError` de validación o incluso un futuro `HTTPException` llegan al controller como error genérico → siempre 500, nunca 400/409, y el traceback original se pierde. | `base_repository.py:232–240` | Códigos de estado incorrectos y debugging a ciegas. Propuesta: re-lanzar tal cual (el decorador hoy no aporta nada) o al menos encadenar con `raise ... from e` y dejar pasar excepciones tipadas. |
| A9 | **P1** | `create_course_with_requirements` hace commit intermedio (no atómico): si fallan los requirements/contents queda un curso huérfano. Es el B7 documentado y **aún no corregido** — el patrón correcto (flush + commit único) ya existe en `create_congress_with_relations` como referencia. | `course_controller.py:62–83` | Curso huérfano en BD ante fallo parcial. Replicar el patrón atómico de congress. |
| A10 | **P1** | `SesionCronogramaUpdate.validate_fecha` rechaza fechas pasadas, pero en `SesionCronogramaCreate` esa misma validación está **comentada**. Inconsistencia: se puede crear una sesión histórica pero no editarla (cualquier PATCH que toque `fecha` de una sesión pasada falla con 422). | `sesion_cronograma_model.py:88–94` (comentado) vs `:133–140` (activo) | Decidir una sola política (propuesta: quitar la restricción también del Update — los datos históricos deben ser editables) y testear ambas direcciones. |
| A11 | **P2** | Tests con SQLite **sin** `PRAGMA foreign_keys=ON`: toda la clase de bugs de FKs (A3, A4, el caso speakers de congresos) es invisible para la suite. | `tests/conftest.py:27–34` | Activar FKs en el fixture `session` (event listener `connect` → `PRAGMA foreign_keys=ON`). ⚠️ Esto puede hacer fallar tests existentes que creaban datos violando FKs — corregirlos es parte del valor de este ítem. |
| A12 | **P2** | `speaker_controller.py:492–496` maneja `speaker_with_sessions[0] if isinstance(..., tuple)` — otra variante del enmascaramiento A2, con lógica distinta al resto. | `speaker_controller.py:492` | Unificar con la corrección A1/A2. |

### 3.2 Procedimiento por bug

1. Escribir primero el test que reproduce el fallo (rojo).
2. Corregir en la capa correcta (causa raíz, no parche en el consumidor).
3. Test en verde + `pytest` completo sin regresiones.
4. Commit individual con formato `fix(<módulo>): <qué> — <por qué>`.
5. Actualizar la tabla de registro (sección 6).

---

## 4. Fase 2 — Endurecimiento estructural (previene clases de bug)

| # | Mejora | Detalle |
|---|---|---|
| E1 | **FKs activas en tests** (A11) | Es la mejora que más bugs futuros previene: la clase entera de errores de borrado/huérfanos se vuelve detectable en CI. Hacerla temprano en la fase 2, después de corregir A3/A4 (para que la suite pase). |
| E2 | **Política de borrado documentada y uniforme** | Documentar en un solo lugar (docstring de `BaseController.delete` + `docs/`) la política por entidad: qué bloquea con 409, qué cascadea. Hoy la política solo existe en `delete_congress`. |
| E3 | **Convención única de queries en repositorios** | Regla: `select` siempre de `sqlmodel`, o `db.execute(...).scalars()` siempre que se use `select` de SQLAlchemy. Elegir una (propuesta: `db.execute(...).scalars()`, ya mayoritaria) y aplicarla al corregir A1. Añadir la regla a la skill `ctt-backend`. |
| E4 | **Transacción solo en el controller** (A7) | Tras quitar los commits del `BaseRepository`, verificar con grep que ningún repositorio hace `commit()` y añadir la regla a la skill. |
| E5 | **Seeds fuera del camino crítico de arranque** (A5) | Opción mínima: try/except por seed con log. Opción completa: variable de entorno `RUN_SEEDS` (default off en producción) y ejecución explícita vía `main_seed.py`. Decidir con el usuario — afecta el flujo de despliegue con Docker. |

---

## 5. Fase 3 — Mejoras de calidad (P2–P3, no bloqueantes)

| # | Mejora | Detalle |
|---|---|---|
| M1 | Cobertura de tests medida | `pytest --cov=src --cov-report=term-missing` como referencia; identificar módulos <60% (candidatos: serializers, `image_utils`, `pdf_utils`, `svg_utils`, middleware). |
| M2 | Deduplicar paginación | Cada repositorio re-implementa el mismo bloque count + order + offset/limit. Extraer un helper en `BaseRepository` que reciba la query base y devuelva `(items, total)`. |
| M3 | Módulos legacy de course/user | Siguen con SQLAlchemy clásico + métodos estáticos (documentado en la skill como "no copiar"). Decidir: migrar al patrón moderno o congelar explícitamente. No migrar sin necesidad — solo si A9 exige tocar course de todas formas. |
| M4 | Rutas legacy de congress | `POST /congresses-new/legacy` y `GET /{id}/legacy` generan datos sintéticos (fechas de hoy, edición derivada del título). Confirmar si el frontend aún las consume; si no, deprecarlas con warning en la respuesta y fecha de eliminación. |
| M5 | Doble `db.rollback()` router+controller | Verificado inocuo en la auditoría de congresos (B5 descartado), pero es ruido: cuando A7 esté hecho, evaluar quitar los rollbacks redundantes de los routers para dejar un solo dueño de la transacción. |
| M6 | Montaje triple en docker-compose | `./static/images` se monta también en `/app/static/pdf` y `/app/static/svg` (bug heredado ya anotado en la skill ctt-containers). Confirmar con el usuario y corregir el compose. |
| M7 | Validadores duplicados en modelos `*Nested` | `CongresoSponsorNested`/`SesionCronogramaNested` copian los validators de sus `*Create`. Extraer mixins o clases base de validación para no mantenerlos por duplicado. |
| M8 | Chequeos batch en validaciones N+1 | `create_congress_with_relations` valida sponsors/speakers con un SELECT por ítem (hallazgo del code-review previo). Cambiar a una query `WHERE id IN (...)` por tipo de entidad. |
| M9 | Enum `Jornada` con valor no-ASCII (`"mañana"`) | Funciona, pero ya produjo fricción de encoding al enviar payloads desde shells Windows (observado en la verificación en vivo). No cambiar el valor (rompería el contrato con el frontend) — documentar en el endpoint que el body debe ser UTF-8 y cubrir con un test de charset. |

---

## 6. Registro de resultados de auditoría

| # | Estado | Corrección aplicada / commit |
|---|---|---|
| A1 | ⬜ Pendiente | — |
| A2 | ⬜ Pendiente | — |
| A3 | ⬜ Pendiente | — |
| A4 | ⬜ Pendiente | — |
| A5 | ⬜ Pendiente | — |
| A6 | ⬜ Pendiente | — |
| A7 | ⬜ Pendiente | — |
| A8 | ⬜ Pendiente | — |
| A9 | ⬜ Pendiente | — |
| A10 | ⬜ Pendiente | — |
| A11 | ⬜ Pendiente | — |
| A12 | ⬜ Pendiente | — |

---

## 7. Plan de pruebas

### 7.1 Regresión por bug (Fase 1)

- **A1/A2:** por cada método de repositorio corregido, un test que verifique que
  devuelve instancias del modelo (`isinstance(result[0], Model)`), más los tests de
  controller existentes en verde tras quitar los fallbacks.
- **A3:** borrar speaker con sesiones → 409; sin sesiones → 200. Espejo del test
  `test_delete_congress_with_speakers_returns_409` ya existente.
- **A4:** borrar sponsor con `congreso_sponsors` → 200 y los registros pivote
  desaparecen; el congreso asociado queda intacto.
- **A5/A6:** test unitario de `seed_enrollments` con 2–4 usuarios y un congreso
  futuro (hoy crashea); test de que un seed que lanza excepción no impide que los
  demás corran.
- **A7:** test de que `BaseRepository.create` **no** persiste sin commit del
  controller (usar una sesión sin autocommit y verificar rollback).
- **A9:** crear curso con `contents` inválidos → 4xx y **ningún** curso en BD.
- **A10:** PATCH de una sesión con fecha pasada → según la política decidida.
- **A11:** suite completa en verde con `PRAGMA foreign_keys=ON`.

### 7.2 Verificación en vivo (obligatoria — las lecciones vienen de aquí)

Igual que en el plan de congresos: los bugs de FKs **no aparecen en SQLite**.
Al terminar cada grupo de fixes de borrado (A3, A4):

```bash
# Contenedor temporal contra el SQL Server real, sin tocar el servicio del usuario
docker compose build ctt-api
docker run -d --name ctt-verify --network ctt-back_ctt-network \
  --env-file .env -e SQL_SERVER=sqlserver -p 8003:8000 ctt-back-ctt-api:latest
# Login → crear entidades relacionadas → intentar borrados en cada combinación
# → verificar 409/200/cascada según la política → limpiar datos → docker rm -f ctt-verify
```

### 7.3 Skills al cierre

- `/code-review high` sobre el diff completo de la rama.
- `/verify` end-to-end de los flujos tocados (borrados, creación de curso atómica,
  arranque con seeds).

---

## 8. Criterios de aceptación

- [ ] Working tree limpio al iniciar: trabajo de Alembic commiteado o stasheado por separado.
- [ ] Cada sospecha A1–A12 marcada como confirmada/descartada en la tabla 6; todas
      las confirmadas corregidas con test de regresión y commit individual.
- [ ] Ningún repositorio devuelve `Row` donde el controller espera modelo; ningún
      controller conserva el patrón `hasattr(...) else x[0]`.
- [ ] Todos los DELETE de la API responden 404/409/200 según política documentada —
      ninguno responde 500 por FK, **verificado en vivo contra SQL Server real**.
- [ ] Los repositorios no hacen `commit()`; la transacción vive solo en el controller.
- [ ] Un seed que falla no impide el arranque de la API (o los seeds ya no corren en
      el arranque, según lo decidido en E5).
- [ ] La suite de tests corre con FKs activas en SQLite y pasa completa.
- [ ] `pytest` completo en verde (≥ línea base de 520 passed) + cobertura medida y
      registrada como referencia.
- [ ] Skill `ctt-backend` actualizada con las reglas nuevas (queries, transacciones,
      política de borrado).
- [ ] `/code-review` y `/verify` ejecutados antes del PR.

---

## 9. Riesgos y decisiones abiertas

| Riesgo / Decisión | Mitigación / Propuesta |
|---|---|
| Quitar los commits del `BaseRepository` (A7) afecta a **todos** los módulos, incluidos los legacy (course, user) que pueden depender del commit implícito | Grep exhaustivo de call sites antes de tocar; correr la suite tras cada módulo migrado; si un legacy depende fuerte, envolver solo ese caso y anotarlo |
| Activar FKs en SQLite (A11) puede romper decenas de tests con fixtures que violan FKs | Hacerlo en commit propio; corregir fixtures es parte del valor (destapan datos imposibles) |
| Cambiar el comportamiento de los seeds (A5/E5) afecta el flujo de despliegue Docker actual | Decidir con el usuario antes de implementar; opción mínima (try/except) no cambia el flujo |
| La política de borrado de sponsor (cascada vs 409) es una decisión de producto | Propuesta: cascada de la tabla pivote (consistente con congress); confirmar con el usuario |
| Deprecar rutas legacy (M4) puede romper el frontend | Solo deprecar con confirmación explícita; mientras tanto, warning en la respuesta |
| El working tree tiene trabajo de Alembic sin commitear | Resolverlo en Fase 0 **antes** de crear la rama de auditoría |

---

## 10. Orden de ejecución sugerido

1. **Fase 0:** resolver working tree (Alembic) → `pytest` base → crear rama.
2. **A6 + A5** (seeds): son los únicos que rompen el *arranque* — primero lo que
   impide levantar el entorno.
3. **A1 + A2 + A12** (Row/hasattr): un commit por repositorio corregido, quitando
   los fallbacks de su controller en el mismo commit.
4. **A3 + A4** (políticas de borrado) → verificación en vivo de todos los DELETE.
5. **A11/E1** (FKs en tests) → corregir los tests que destape.
6. **A7 + A8** (transacciones y errores del repositorio base) — los más invasivos,
   con la suite ya endurecida por el paso anterior.
7. **A9** (curso atómico) y **A10** (validación de fecha en update).
8. **Fase 3** (M1–M9) según prioridad y tiempo, cada una como commit independiente.
9. `/code-review high` + `/verify` + actualizar tabla 6 y criterios → PR.
