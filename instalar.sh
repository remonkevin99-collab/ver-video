#!/usr/bin/env bash
# Instala «ver vídeos» (Mac y Linux). Se puede correr las veces que quieras: lo que ya está, no se toca.
#
#     bash instalar.sh
#
# Hace tres cosas:
#   1. crea el entorno de Python en .venv, dentro de esta carpeta (Python 3.10, 3.11 o 3.12; si tienes `uv`, lo usa y él
#      baja Python si falta),
#   2. instala lo necesario (requirements.txt),
#   3. baja el modelo de voz que escribe lo que se dice (se guarda en la caché de tu usuario, una sola vez).
# Y al final comprueba que todo funciona y dice LISTO.
set -euo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$AQUI"
VENV="$AQUI/.venv"
PY="$VENV/bin/python"

echo "== Ver vídeos: instalación =="

# ── ffmpeg ──────────────────────────────────────────────────────────────────────────────────────────────────────────
if command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg: lo tienes ($(command -v ffmpeg))"
else
  echo "ffmpeg: no está instalado en tu sistema. No pasa nada: se usará el que trae el paquete imageio-ffmpeg."
  echo "        (Si quieres el tuyo: en Mac, 'brew install ffmpeg'; en Ubuntu/Debian, 'sudo apt install ffmpeg'.)"
fi

# ── ¿el .venv que ya hay sirve? (Python 3.10 a 3.12) ──────────────────────────────────────────────────────────────
venv_sirve() {
  [ -x "$PY" ] && "$PY" -c 'import sys; sys.exit(0 if (3, 10) <= sys.version_info[:2] <= (3, 12) else 1)' 2>/dev/null
}

if venv_sirve; then
  echo "Python: ya hay un entorno en .venv ($("$PY" --version 2>&1)), se usa ese."
elif command -v uv >/dev/null 2>&1; then
  echo "Python: creando .venv con uv (Python 3.12; si no lo tienes, uv lo baja)..."
  rm -rf "$VENV"
  uv venv --seed --python 3.12 "$VENV"
else
  BASE=""
  for candidato in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidato" >/dev/null 2>&1 && \
       "$candidato" -c 'import sys; sys.exit(0 if (3, 10) <= sys.version_info[:2] <= (3, 12) else 1)' 2>/dev/null; then
      BASE="$candidato"
      break
    fi
  done
  if [ -z "$BASE" ]; then
    # no hay un Python que sirva: se instala uv (el instalador oficial, en tu carpeta de usuario), que baja Python solo
    echo "Python: no tienes Python 3.10, 3.11 o 3.12 (el transcriptor todavía no funciona con todos los más nuevos)."
    echo "        Instalo uv, que lo baja solo (es una vez, en tu carpeta de usuario)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || true
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  fi
  if [ -z "$BASE" ] && command -v uv >/dev/null 2>&1; then
    echo "Python: creando .venv con uv (Python 3.12)..."
    rm -rf "$VENV"
    uv venv --seed --python 3.12 "$VENV"
  elif [ -z "$BASE" ]; then
    echo ""
    echo "ERROR: falta Python 3.10, 3.11 o 3.12 (el transcriptor todavía no funciona con todas las más nuevas)."
    echo "  La forma más fácil: instala uv (https://docs.astral.sh/uv/) y vuelve a correr este archivo; uv baja Python solo."
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  O instala Python 3.12 a mano:"
    echo "    Mac:           brew install python@3.12   (o el instalador de https://www.python.org/downloads/)"
    echo "    Ubuntu/Debian: sudo apt install python3.12 python3.12-venv"
    exit 1
  fi
  if [ -n "$BASE" ]; then
    echo "Python: creando .venv con $BASE ($("$BASE" --version 2>&1))..."
    rm -rf "$VENV"
    "$BASE" -m venv "$VENV"
  fi
fi

# un .venv viejo hecho con uv puede no tener pip (y hace falta para actualizar yt-dlp): se le pone
if ! "$PY" -m pip --version >/dev/null 2>&1 && command -v uv >/dev/null 2>&1; then
  uv pip install --quiet --python "$PY" pip
fi

# ── los paquetes ────────────────────────────────────────────────────────────────────────────────────────────────────
echo "Paquetes: instalando lo de requirements.txt (la primera vez tarda un par de minutos)..."
if command -v uv >/dev/null 2>&1; then
  uv pip install --quiet --python "$PY" -r requirements.txt
else
  "$PY" -m pip install --quiet --upgrade pip
  "$PY" -m pip install --quiet -r requirements.txt
fi

# ── el modelo de voz (el que escribe lo que se dice) ───────────────────────────────────────────────────────────────
echo "Modelo de voz: preparándolo (la primera vez baja unos 460 MB; después ya no)..."
HF_HUB_VERBOSITY=error HF_HUB_DISABLE_PROGRESS_BARS=1 "$PY" -c 'import warnings; warnings.filterwarnings("ignore"); from faster_whisper import WhisperModel; WhisperModel("small", device="cpu", compute_type="int8")'
echo "Modelo de voz: listo."

# ── la prueba final ─────────────────────────────────────────────────────────────────────────────────────────────────
"$PY" ver.py --comprobar
echo ""
echo "Para usarlo:"
echo "  .venv/bin/python ver.py https://www.instagram.com/reel/..."
echo ""
echo "LISTO"
