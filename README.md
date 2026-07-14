# Job Search Bot (semi-automático)

Busca vacantes en Indeed, LinkedIn y ZonaJobs/Bumeran según tus criterios, evita
mostrarte duplicados ya vistos, y genera un reporte en Markdown con un borrador
de carta de presentación por vacante (usando la API de Claude). **No postula
por vos**: la decisión y el envío final siempre los hacés vos, manualmente.

## ⚠️ Antes de usarlo — Términos de Servicio

LinkedIn e Indeed prohíben explícitamente el scraping y la automatización en
sus Términos de Servicio. Usar este bot conlleva riesgo:

- **LinkedIn**: este bot usa el endpoint público de búsqueda (sin login), así
  que no hay riesgo de que te *baneen la cuenta*, pero LinkedIn puede
  bloquear tu IP si hacés muchas requests. No lo corras más de 1-2 veces por
  día.
- **Indeed / ZonaJobs**: scraping directo del HTML. Mismo riesgo de bloqueo de
  IP si abusás de la frecuencia.
- **Nunca** uses tus credenciales de estas plataformas dentro del bot, y
  **nunca** automatices el click de "postular"/"Easy Apply" con tu sesión
  logueada — eso es lo que más fácil detectan y lo que más rápido te puede
  banear una cuenta profesional que probablemente te importa mantener sana.

Este diseño (semi-automático, sin login, con delays) minimiza el riesgo, pero
no lo elimina. Es responsabilidad tuya el uso que le des.

## Instalación (en tu máquina local — este bot no corre en la nube)

```bash
git clone <tu-repo>
cd Pruebas
python3 -m venv .venv
source .venv/bin/activate  # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium   # necesario para el scraper de ZonaJobs
```

## Configuración

1. **Criterios de búsqueda:**
   ```bash
   cp config.example.yaml config.yaml
   ```
   Editá `config.yaml`: palabras clave, ubicaciones, modalidad remota,
   palabras a excluir, qué sitios habilitar.

2. **Tu CV** (para las cartas de presentación):
   ```bash
   # Pegá el contenido de tu CV como texto plano en:
   cv/cv.txt
   ```

3. **API key de Anthropic** (para generar las cartas):
   ```bash
   cp .env.example .env
   ```
   Editá `.env` y poné tu `ANTHROPIC_API_KEY` (la sacás de
   https://console.anthropic.com/settings/keys). Este archivo está en
   `.gitignore`, nunca se sube al repo.

   Si no querés usar esta función, poné `cover_letter.enabled: false` en
   `config.yaml`.

## Uso

Correr una búsqueda:

```bash
python -m job_search_bot.main
```

Esto genera un archivo `data/reports/YYYY-MM-DD_HHMM.md` con las vacantes
nuevas que matchean tus criterios (no te repite las que ya viste en
corridas anteriores — se trackean en `data/jobs.sqlite3`).

Para correr sin generar cartas de presentación (más rápido):

```bash
python -m job_search_bot.main --no-cover-letters
```

## Automatizar con cron (Linux/Mac)

Para que corra solo, por ejemplo todas las mañanas a las 9:

```bash
crontab -e
```

Agregá esta línea (ajustá las rutas a tu instalación):

```
0 9 * * * cd /ruta/a/Pruebas && /ruta/a/Pruebas/.venv/bin/python -m job_search_bot.main >> data/cron.log 2>&1
```

En macOS puede que necesites dar permisos de "Full Disk Access" a `cron`/
`Terminal` en Preferencias del Sistema > Privacidad para que pueda ejecutar
sin problemas.

En Windows, usá el Programador de Tareas (Task Scheduler) en vez de cron,
apuntando a `python.exe` con el mismo comando.

## Si un scraper deja de funcionar

Los sitios cambian su HTML seguido, y cuando eso pasa un scraper puede dejar
de devolver resultados de un día para el otro. Si ves en los logs
`"no se encontraron resultados"`:

1. Abrí la URL de búsqueda manualmente en tu navegador.
2. Click derecho sobre una tarjeta de vacante → "Inspeccionar".
3. Fijate qué clase/atributo identifica cada tarjeta, el título, la empresa,
   el link.
4. Actualizá los selectores correspondientes en
   `job_search_bot/scrapers/indeed.py`, `linkedin.py` o `zonajobs.py`.

## Estructura del proyecto

```
job_search_bot/
  models.py           # JobPosting (dataclass)
  config.py           # carga de config.yaml
  db.py                # SQLite para no repetir vacantes ya vistas
  matcher.py           # filtrado según tus criterios
  cover_letter.py       # generación de cartas con Claude
  report.py            # genera el .md con el resumen
  main.py              # orquesta todo
  scrapers/
    indeed.py
    linkedin.py
    zonajobs.py
config.example.yaml    # template — copiar a config.yaml
.env.example            # template — copiar a .env
cv/cv.txt                # tu CV en texto plano (no se sube al repo)
data/                    # DB y reportes generados (no se sube al repo)
```
