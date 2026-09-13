"""
Lee las jornadas y la clasificación del grupo en bizkaiapadel.com
y genera data.json para la web estática.

Diseñado para no depender de clases CSS: trabaja sobre el texto
visible de la página, que sigue siempre el patrón:

    EQUIPO LOCAL
    X - Y
    EQUIPO VISITANTE
    dd/mm/aaaa hh:mm
    Club / sede

Si una jornada no se puede leer, se conserva la versión anterior
de esa jornada (si existe) en vez de romper el fichero.
"""
import json, re, sys, datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://www.bizkaiapadel.com/Home/JornadaLiga/{liga}?fase={fase}&grupoId={grupo}&jornada={j}"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
           "Accept-Language": "es-ES,es;q=0.9"}

RE_SCORE = re.compile(r"^(\d+)\s*-\s*(\d+)$")
RE_DATE = re.compile(r"^(\d{2})/(\d{2})/(\d{4})\s+(\d{2}):(\d{2})$")
RE_DATE_ONLY = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")
STOP_WORDS = {"partidos", "clasificación", "clasificacion", "jornada"}


def fetch(url):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def text_lines(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "nav", "footer", "header"]):
        t.decompose()
    lines = [l.strip() for l in soup.get_text("\n").splitlines()]
    return [l for l in lines if l], soup


def parse_matches(lines):
    """Busca el patrón local / marcador / visitante / fecha / sede."""
    matches = []
    i = 0
    n = len(lines)
    while i + 2 < n:
        m = RE_SCORE.match(lines[i + 1])
        if m and lines[i].lower() not in STOP_WORDS and lines[i + 2].lower() not in STOP_WORDS:
            match = {
                "local": lines[i],
                "visitante": lines[i + 2],
                "goles_local": int(m.group(1)),
                "goles_visitante": int(m.group(2)),
                "fecha": None,
                "hora": None,
                "sede": None,
            }
            j = i + 3
            # fecha (puede venir con o sin hora)
            if j < n:
                d = RE_DATE.match(lines[j]) or RE_DATE_ONLY.match(lines[j])
                if d:
                    g = d.groups()
                    match["fecha"] = f"{g[2]}-{g[1]}-{g[0]}"
                    if len(g) == 5:
                        match["hora"] = f"{g[3]}:{g[4]}"
                    j += 1
            # sede: siguiente línea que no sea una palabra de control ni otro marcador
            if j < n and lines[j].lower() not in STOP_WORDS and not RE_SCORE.match(lines[j]) \
                    and not (j + 1 < n and RE_SCORE.match(lines[j + 1])):
                match["sede"] = lines[j]
            match["jugado"] = not (match["goles_local"] == 0 and match["goles_visitante"] == 0)
            matches.append(match)
            i += 3
        else:
            i += 1
    return matches


def parse_standings(soup):
    for table in soup.find_all("table"):
        head = " ".join(th.get_text(" ", strip=True) for th in table.find_all("th")).lower()
        if "equipo" in head and ("pos" in head or "puntos" in head):
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(cells) >= 4 and cells[0].isdigit():
                    nums = [int(c) if c.lstrip("-").isdigit() else 0 for c in cells[2:]]
                    nums += [0] * (8 - len(nums))
                    rows.append({
                        "pos": int(cells[0]), "equipo": cells[1],
                        "puntos": nums[0], "pj": nums[1], "pg": nums[2], "pp": nums[3],
                        "sg": nums[4], "sp": nums[5], "jg": nums[6], "jp": nums[7],
                    })
            if rows:
                return rows
    return []


def main():
    cfg = json.loads(Path("config.json").read_text(encoding="utf-8"))
    out_path = Path("data.json")
    previous = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    prev_jornadas = {j["numero"]: j for j in previous.get("jornadas", [])}

    jornadas, standings, errors = [], [], []
    seen_signatures = set()

    for j in range(1, cfg.get("max_jornadas", 30) + 1):
        url = BASE.format(liga=cfg["liga_id"], fase=cfg["fase"], grupo=cfg["grupo_id"], j=j)
        try:
            lines, soup = text_lines(fetch(url))
            matches = parse_matches(lines)
        except Exception as e:  # red o parseo
            errors.append(f"J{j}: {e}")
            if j in prev_jornadas:
                jornadas.append(prev_jornadas[j])
                continue
            break

        if not matches:
            break
        sig = tuple((m["local"], m["visitante"]) for m in matches)
        if sig in seen_signatures:  # la web repite la última jornada si pides una que no existe
            break
        seen_signatures.add(sig)
        jornadas.append({"numero": j, "partidos": matches})
        if not standings:
            standings = parse_standings(soup)

    if not jornadas:
        print("No se ha podido leer ninguna jornada; se mantiene data.json anterior.", file=sys.stderr)
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(0 if previous else 1)

    if not standings:
        standings = previous.get("clasificacion", [])

    data = {
        "titulo": cfg["titulo"],
        "mi_equipo": cfg["mi_equipo"],
        "actualizado": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
        "fuente": BASE.format(liga=cfg["liga_id"], fase=cfg["fase"], grupo=cfg["grupo_id"], j=1),
        "jornadas": jornadas,
        "clasificacion": standings,
        "avisos": errors,
    }
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK: {len(jornadas)} jornadas, {len(standings)} equipos, {len(errors)} avisos")


if __name__ == "__main__":
    main()
