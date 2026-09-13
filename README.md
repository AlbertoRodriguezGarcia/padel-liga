# Liga de pádel · seguimiento del equipo

Web estática que lee automáticamente jornadas, resultados y clasificación
de bizkaiapadel.com y las muestra en formato móvil. Gratis, sin servidor.

## Puesta en marcha (una vez, ~10 min)

1. Crea un repositorio **público** en GitHub (por ejemplo `padel-liga`) y sube
   todos estos archivos (puedes arrastrarlos en "Add file → Upload files").
2. Edita `config.json` y pon el nombre exacto de vuestro equipo en `mi_equipo`
   (tal como aparece en la clasificación de la federación).
3. En el repositorio: **Settings → Pages → Source: Deploy from a branch → main / (root)** → Save.
4. **Settings → Actions → General → Workflow permissions → "Read and write permissions"** → Save.
5. Pestaña **Actions → "Actualizar datos de la liga" → Run workflow** para la primera carga.
6. En un par de minutos la web estará en `https://TU_USUARIO.github.io/padel-liga/`.
   Pinéala en el grupo de WhatsApp.

## Cómo se actualiza

GitHub Actions ejecuta `scrape.py` cada 3 horas los fines de semana y dos
veces al día entre semana. Si quieres forzar una actualización, pulsa
"Run workflow" en la pestaña Actions.

## Nueva temporada o cambio de grupo

Abre en la web de la federación la jornada de vuestro grupo y copia de la URL
los tres números a `config.json`:

    https://www.bizkaiapadel.com/Home/JornadaLiga/34?fase=60&grupoId=54&jornada=1
                                                     ^liga_id   ^fase   ^grupo_id

Al guardar `config.json` el workflow se lanza solo.

## Si algo deja de funcionar

Si la federación cambia el diseño de su web, la pestaña Actions mostrará el
fallo y la app seguirá enseñando los últimos datos correctos. El parser está
en `scrape.py` y solo depende del texto visible (equipo / marcador / equipo /
fecha / sede), así que normalmente bastará con un ajuste pequeño.

## Instalarla como app en el móvil

- **Android (Chrome):** al abrir el enlace aparece el botón "Instalar"; también vale
  menú ⋮ → "Añadir a pantalla de inicio".
- **iPhone (Safari):** botón Compartir → "Añadir a pantalla de inicio".

Se abre a pantalla completa con su icono y, si no hay cobertura, muestra los
últimos datos que cargó.
