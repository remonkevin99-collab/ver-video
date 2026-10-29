"""Claude no ve vídeos: ve fotos y lee texto. Este programa le prepara un vídeo así, para que lo «vea» entero.

    python ver.py <enlace o archivo>        # un Reel, un TikTok, un vídeo de YouTube o uno tuyo
    python ver.py <enlace> --cada 1         # un cuadro cada segundo (si no, lo decide según lo que dure)
    python ver.py <vídeo> --desde 10 --hasta 12      # la lupa: ese tramo, 10 cuadros por segundo (--cada 0.04: casi todos)
    python ver.py --comprobar               # dice si todo está instalado

Lo deja en `videos-vistos/<nombre>/`, dentro de la carpeta desde la que lo corres:
- `RESUMEN.md`: lo primero que se lee. Los datos (cuenta, fecha, vistas, Me gusta…), lo que se dice con su segundo, los
  cambios de plano y qué imagen tiene cada tramo.
- `gancho.jpg`: los 3 primeros segundos, 8 cuadros por segundo (ahí se decide si la gente se queda).
- `hoja-01.jpg`, `hoja-02.jpg`…: el vídeo entero en cuadros, cada uno con su segundo.
- `voz.json`: cada frase y cada palabra con su segundo.
- `video.mp4` (o el formato en que venga) y `datos.json`.

Todo corre en tu computadora. Es para estudiar vídeos públicos, no para volver a subir el de otro.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')   # la consola de Windows no siempre escribe «✓»
except AttributeError:
    pass

VERTICAL = {'mini': 216, 'columnas': 5, 'filas': 4}      # 20 cuadros por hoja
HORIZONTAL = {'mini': 320, 'columnas': 4, 'filas': 5}
GANCHO_SEGUNDOS, GANCHO_FPS = 3, 8


def ffmpeg():
    """El ffmpeg del sistema si lo hay; si no, el que trae el paquete imageio-ffmpeg."""
    propio = shutil.which('ffmpeg')
    if propio:
        return propio
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def reloj(t, decimas=False):
    """0:07 · con `decimas`, 0:07.5 · con decimas=2, 0:07.52 (para la lupa)."""
    m, s = divmod(t, 60)
    if decimas == 2:
        return f'{int(m)}:{s:05.2f}'
    return f'{int(m)}:{s:04.1f}' if decimas else f'{int(m)}:{int(s):02d}'


def nombre_limpio(texto):
    texto = re.sub(r'[^\w\-]+', '-', texto, flags=re.UNICODE).strip('-')
    return texto[:60] or 'video'


# ── 1 · el vídeo ──────────────────────────────────────────────────────────────────────────────────────────────────

def bajar(enlace, destino):
    """Lo baja con yt-dlp, sin entrar en ninguna cuenta. Devuelve (archivo, datos)."""
    from yt_dlp import YoutubeDL
    tmp = destino / '_bajando'
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    opciones = {
        'outtmpl': str(tmp / 'video.%(ext)s'),
        # lo mejor hasta 1920 de alto (de sobra para mirar cuadros); si viene en dos trozos, ffmpeg los junta
        'format': 'bv*[height<=1920]+ba/b[height<=1920]/bv*+ba/b',
        'merge_output_format': 'mp4',
        'ffmpeg_location': ffmpeg(),
        'noplaylist': True, 'quiet': True, 'no_warnings': True, 'noprogress': True,
    }
    try:
        with YoutubeDL(opciones) as y:
            info = y.extract_info(enlace, download=True)
    except Exception as e:  # noqa: BLE001  (yt-dlp lanza de todo; a la persona le sirve el mensaje, no el tipo)
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit('No pude bajar el vídeo.\n'
                 '- ¿Es público? Los privados, los de cuentas privadas y las historias no se pueden bajar.\n'
                 '- Si es público, las plataformas cambian a menudo: actualiza el programa que los baja con\n'
                 f'    "{sys.executable}" -m pip install -U yt-dlp\n'
                 '  y vuelve a probar.\n'
                 f'(El error: {str(e).strip()[:300]})')
    # la cuenta con su @ (en Instagram, «uploader_id» es un número y el @ viene en «channel»)
    cuentas = [info.get(k) for k in ('channel', 'uploader_id', 'uploader') if info.get(k)]
    cuenta = next((c for c in cuentas if not str(c).isdigit()), cuentas[0] if cuentas else None)
    titulo = info.get('title') or ''
    if titulo.startswith('Video by') and info.get('description'):     # Instagram no tiene título: la 1.ª línea del pie
        titulo = info['description'].strip().splitlines()[0]
    datos = {
        'enlace': info.get('webpage_url') or enlace,
        'plataforma': info.get('extractor_key'),
        'cuenta': str(cuenta).lstrip('@') if cuenta else None,
        'nombre': info.get('uploader') or info.get('channel'),
        'fecha': info.get('upload_date'),
        'titulo': titulo,
        'pie': info.get('description'),
        'dura': info.get('duration'),
        'vistas': info.get('view_count'),
        'me_gusta': info.get('like_count'),
        'comentarios': info.get('comment_count'),
        'compartidos': info.get('repost_count'),
    }
    nombre = nombre_limpio(f"{datos['cuenta'] or 'video'}-{info.get('id') or ''}")
    final = destino / nombre
    shutil.rmtree(final, ignore_errors=True)
    tmp.rename(final)
    archivos = sorted((f for f in final.glob('video.*') if f.suffix not in ('.part', '.json', '.ytdl')),
                      key=lambda f: f.suffix not in ('.mp4', '.webm', '.mkv', '.mov'))   # el vídeo antes que el audio
    if not archivos:
        sys.exit('El vídeo no se bajó entero. Vuelve a probar en un momento.')
    return archivos[0], datos


def medir(video, ff):
    """Cuánto dura y el tamaño con que se VE (el primer cuadro ya girado: los del móvil traen la rotación aparte)."""
    r = subprocess.run([ff, '-hide_banner', '-i', str(video)], capture_output=True, text=True, errors='replace')
    m = re.search(r'Duration: (\d+):(\d+):(\d+(?:\.\d+)?)', r.stderr)
    dura = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0
    tiene_audio = bool(re.search(r'Stream #\S+.*Audio:', r.stderr))
    tiene_imagen = any('Video:' in x and 'attached pic' not in x for x in r.stderr.splitlines() if 'Stream #' in x)
    if not tiene_imagen:
        sys.exit('Esto no tiene imagen: es solo sonido. Si es una publicación de fotos (un carrusel de TikTok o de '
                 'Instagram), no hay vídeo que mirar.')
    with tempfile.TemporaryDirectory() as t:
        uno = Path(t) / 'uno.png'
        subprocess.run([ff, '-v', 'error', '-y', '-i', str(video), '-frames:v', '1', str(uno)], check=False)
        from PIL import Image
        ancho, alto = Image.open(uno).size if uno.exists() else (1080, 1920)
    return dura, ancho, alto, tiene_audio


# ── 2 · los cuadros ───────────────────────────────────────────────────────────────────────────────────────────────

def sacar_cuadros(video, ff, fps, ancho_mini, dura=None, desde=0):
    """Los cuadros a `fps` por segundo, ya pequeños, desde el segundo `desde` y durante `dura`. Devuelve
    [(segundo, imagen)]."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as t:
        args = [ff, '-v', 'error'] + (['-ss', str(desde)] if desde else []) + ['-i', str(video)]
        if dura:
            args += ['-t', str(dura)]
        args += ['-vf', f'fps={fps},scale={ancho_mini}:-2', '-q:v', '3', str(Path(t) / '%05d.jpg')]
        subprocess.run(args, check=True)
        cuadros = []
        for k, f in enumerate(sorted(Path(t).glob('*.jpg'))):
            with Image.open(f) as im:
                cuadros.append((desde + k / fps, im.convert('RGB')))
    return cuadros


def hoja(cuadros, columnas, ruta, decimas):
    """Los cuadros en una cuadrícula, con su segundo debajo en amarillo sobre negro."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = cuadros[0][1].size
    banda = 30
    filas = -(-len(cuadros) // columnas)
    lienzo = Image.new('RGB', (columnas * w + (columnas + 1) * 6, filas * (h + banda) + (filas + 1) * 6), (20, 20, 24))
    d = ImageDraw.Draw(lienzo)
    try:
        f = ImageFont.load_default(size=22)
    except TypeError:                     # Pillow viejo
        f = ImageFont.load_default()
    for k, (t, im) in enumerate(cuadros):
        x = 6 + (k % columnas) * (w + 6)
        y = 6 + (k // columnas) * (h + banda + 6)
        lienzo.paste(im.resize((w, h)), (x, y))
        d.text((x + w / 2, y + h + banda / 2), reloj(t, decimas), font=f, fill=(255, 200, 40), anchor='mm')
    lienzo.save(ruta, quality=85)


def cortes(video, ff):
    """Los cambios de plano que ve ffmpeg (cuando cambia mucho la imagen de un cuadro al siguiente)."""
    r = subprocess.run([ff, '-hide_banner', '-i', str(video), '-vf', "scale=320:-2,select='gt(scene,0.3)',showinfo",
                        '-an', '-f', 'null', '-'], capture_output=True, text=True, errors='replace')
    return [round(float(x), 2) for x in re.findall(r'pts_time:([\d.]+)', r.stderr)]


# ── 3 · lo que se dice ────────────────────────────────────────────────────────────────────────────────────────────

def audio(video, ff):
    """El audio a 16 kHz y mono, con el volumen igualado (si está muy bajo, el transcriptor no oye nada)."""
    import numpy as np
    r = subprocess.run([ff, '-v', 'error', '-i', str(video), '-vn', '-ac', '1', '-ar', '16000',
                        '-af', 'loudnorm=I=-18:TP=-2:LRA=11', '-f', 'f32le', '-'], capture_output=True)
    return np.frombuffer(r.stdout, np.float32).copy()


def transcribir(a, modelo):
    """Las frases y las palabras con su segundo. En un Mac con mlx-whisper instalado usa ese (va más rápido); si no,
    faster-whisper, en tu computadora."""
    try:
        import mlx_whisper
        r = mlx_whisper.transcribe(a, path_or_hf_repo='mlx-community/whisper-large-v3-turbo', word_timestamps=True)
        frases = [(s['start'], s['end'], s['text'].strip()) for s in r['segments']]
        palabras = [(w['word'].strip(), w['start'], w['end']) for s in r['segments'] for w in s.get('words', [])]
        return frases, palabras, r.get('language')
    except ImportError:
        pass
    os.environ.setdefault('HF_HUB_VERBOSITY', 'error')       # sin los avisos en inglés de la descarga del modelo
    os.environ.setdefault('HF_HUB_DISABLE_PROGRESS_BARS', '1')
    import warnings
    warnings.filterwarnings('ignore')
    from faster_whisper import WhisperModel
    m = WhisperModel(modelo, device='cpu', compute_type='int8')
    for vad in (True, False):             # primero quitando los silencios; si así no saca nada, sin quitarlos
        trozos, info = m.transcribe(a, word_timestamps=True, vad_filter=vad)
        trozos = list(trozos)
        if trozos:
            frases = [(s.start, s.end, s.text.strip()) for s in trozos]
            palabras = [(w.word.strip(), w.start, w.end) for s in trozos for w in (s.words or [])]
            return frases, palabras, info.language
    return [], [], None


# ── 4 · el resumen ────────────────────────────────────────────────────────────────────────────────────────────────

def cifra(n):
    return 'no la da' if n is None else f'{n:,}'.replace(',', '.')


def resumen(carpeta, datos, dura, ancho, alto, frases, palabras, idioma, planos, imagenes, cada):
    forma = 'vertical' if alto > ancho else 'horizontal' if ancho > alto else 'cuadrado'
    l = [f"# {(datos.get('titulo') or carpeta.name)[:90]}", '']
    if datos.get('enlace'):
        l.append(f"- **Enlace:** {datos['enlace']}")
    if datos.get('cuenta') or datos.get('nombre'):
        nombre = f" ({datos['nombre']})" if datos.get('nombre') and datos['nombre'] != datos.get('cuenta') else ''
        l.append(f"- **Cuenta:** @{datos.get('cuenta') or ''}{nombre}")
    if datos.get('fecha'):
        f = datos['fecha']
        l.append(f'- **Publicado:** {f[:4]}-{f[4:6]}-{f[6:]}')
    l.append(f'- **Dura:** {reloj(dura)} · {ancho} × {alto} ({forma})')
    if datos.get('enlace'):
        l.append(f"- **Vistas:** {cifra(datos.get('vistas'))} · **Me gusta:** {cifra(datos.get('me_gusta'))} · "
                 f"**Comentarios:** {cifra(datos.get('comentarios'))} · **Compartidos:** {cifra(datos.get('compartidos'))}")
    if palabras and dura:
        l.append(f'- **Ritmo de la voz:** {len(palabras)} palabras, unas {round(len(palabras) / dura * 60)} por minuto')
    if datos.get('pie'):
        pie = ' '.join(datos['pie'].split())
        l.append(f"- **Texto de la publicación:** {pie[:400]}{'…' if len(pie) > 400 else ''}")
    l += ['', f'## Lo que se dice, con su segundo{f" (idioma: {idioma})" if idioma else ""}', '']
    if frases:
        l += [f'[{reloj(a, True)}–{reloj(b, True)}] {t}' for a, b, t in frases]
    else:
        l.append('No se oye voz (o no tiene sonido). Lo que se dice, si hay, estará escrito en pantalla: míralo en las hojas.')
    l += ['', '## Cambios de plano', '']
    if planos:
        media = dura / (len(planos) + 1)
        l.append(f'{len(planos)} cambios: un plano nuevo cada {media:.1f} s de media.')
        l.append(' · '.join(reloj(t, True) for t in planos))
    else:
        l.append('Ninguno brusco: o es un solo plano, o pasa de una imagen a otra con movimientos y transiciones suaves (lo '
                 'normal en un vídeo animado). Míralo en las hojas.')
    l.append('Ojo: ffmpeg no ve los cortes con el mismo encuadre (los «jump cuts» de alguien hablando): esos se cuentan en '
             'las hojas, cuando la persona salta de postura de un cuadro al siguiente.')
    l += ['', '## Las imágenes (míralas en este orden)', '',
          f'- `gancho.jpg`: de 0:00 a 0:0{GANCHO_SEGUNDOS}, {GANCHO_FPS} cuadros por segundo.']
    for ruta, a, b in imagenes:
        l.append(f'- `{ruta}`: de {reloj(a)} a {reloj(b)} (un cuadro cada {str(cada).replace(".", ",")} s).')
    l += ['', '## Lo que no tienes', '',
          '- **La música y los efectos de sonido:** solo está la voz, escrita. No digas qué canción suena ni dónde hay un '
          'golpe de sonido: no lo sabes.',
          '- **Lo que pasa entre dos cuadros:** si algo dura menos que el hueco entre cuadros, no sale. Para un tramo '
          'concreto, vuelve a sacarlo con más cuadros (`--cada 0.25`).',
          '- **La transcripción puede traer alguna palabra mal oída** (un «balato» por «barato», un nombre propio mal '
          'escrito): corrígela por el contexto y por lo que se lee en pantalla.']
    (carpeta / 'RESUMEN.md').write_text('\n'.join(l) + '\n', encoding='utf-8')


# ── la lupa: un tramo corto, casi cuadro a cuadro ──────────────────────────────────────────────────────────────

def lupa(video, ff, carpeta, desde, hasta, cada, forma):
    """Un tramo corto con muchos cuadros (10 por segundo, o los que diga `cada`), para ver una transición o un efecto
    rápido. Deja `lupa-<desde>-<hasta>-NN.jpg`, dice lo que se habla en ese tramo y lo apunta en RESUMEN.md."""
    if hasta <= desde:
        sys.exit('En la lupa, --hasta tiene que ser mayor que --desde.')
    if hasta - desde > 15:
        print('Ojo: la lupa es para tramos cortos (unos segundos). Con tantos, salen muchas hojas.', flush=True)
    cuadros = sacar_cuadros(video, ff, 1 / cada, forma['mini'], dura=hasta - desde, desde=desde)
    if not cuadros:
        sys.exit('Ese tramo está fuera del vídeo.')
    nombre = f'lupa-{desde:g}-{hasta:g}'.replace('.', ',')
    for viejo in carpeta.glob(f'{nombre}-*.jpg'):
        viejo.unlink()
    por_hoja = forma['columnas'] * forma['filas']
    rutas = []
    for n, k in enumerate(range(0, len(cuadros), por_hoja), 1):
        ruta = f'{nombre}-{n:02d}.jpg'
        hoja(cuadros[k:k + por_hoja], forma['columnas'], carpeta / ruta, 2)
        rutas.append(ruta)
    print(f'✓ Lupa de {reloj(desde, True)} a {reloj(hasta, True)}: {len(cuadros)} cuadros, uno cada '
          f'{str(round(cada, 3)).replace(".", ",")} s, en {len(rutas)} hojas: {", ".join(rutas)}', flush=True)
    dicho = []
    voz = carpeta / 'voz.json'
    if voz.exists():
        frases = json.loads(voz.read_text(encoding='utf-8')).get('frases', [])
        dicho = [f"[{reloj(f['ini'], True)}–{reloj(f['fin'], True)}] {f['texto']}" for f in frases
                 if f['fin'] > desde and f['ini'] < hasta]
    print('Lo que se dice en ese tramo:\n' + '\n'.join(dicho) if dicho else 'En ese tramo no se dice nada (o no se pasó '
          'antes el vídeo entero).', flush=True)
    resumen_md = carpeta / 'RESUMEN.md'
    if resumen_md.exists():
        texto = resumen_md.read_text(encoding='utf-8')
        if '## Con lupa' not in texto:
            texto += '\n## Con lupa\n\n'
        texto += f"- {', '.join(f'`{r}`' for r in rutas)}: de {reloj(desde, True)} a {reloj(hasta, True)}, un cuadro cada " \
                 f"{str(round(cada, 3)).replace('.', ',')} s.\n"
        resumen_md.write_text(texto, encoding='utf-8')


# ── todo junto ────────────────────────────────────────────────────────────────────────────────────────────────────

def comprobar():
    bien = True
    for modulo, para in (('yt_dlp', 'bajar vídeos'), ('PIL', 'las hojas de cuadros'), ('numpy', 'el audio'),
                         ('imageio_ffmpeg', 'el ffmpeg de respaldo'), ('faster_whisper', 'escribir lo que se dice')):
        try:
            __import__(modulo)
        except ImportError:
            print(f'MAL: falta {modulo} ({para}).')
            bien = False
    try:
        ff = ffmpeg()
        subprocess.run([ff, '-version'], capture_output=True, check=True)
    except Exception:  # noqa: BLE001
        print('MAL: no encuentro ffmpeg.')
        bien = False
    print('Todo bien.' if bien else 'Corre otra vez la instalación (instalar.sh o instalar.ps1).')
    return bien


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        sys.exit(__doc__)
    if args[0] == '--comprobar':
        sys.exit(0 if comprobar() else 1)
    fuente = args[0]
    cada = float(args[args.index('--cada') + 1]) if '--cada' in args else None
    desde = float(args[args.index('--desde') + 1]) if '--desde' in args else None
    hasta = float(args[args.index('--hasta') + 1]) if '--hasta' in args else None
    modelo = args[args.index('--modelo') + 1] if '--modelo' in args else os.environ.get('MODELO_WHISPER', 'small')
    destino = Path(args[args.index('--carpeta') + 1]) if '--carpeta' in args else Path.cwd() / 'videos-vistos'
    destino.mkdir(parents=True, exist_ok=True)
    ff = ffmpeg()

    if re.match(r'https?://', fuente) or fuente.startswith('www.'):
        print('Bajando el vídeo…', flush=True)
        video, datos = bajar(fuente if fuente.startswith('http') else 'https://' + fuente, destino)
        carpeta = video.parent
    else:
        video = Path(fuente).expanduser().resolve()
        if not video.exists():
            sys.exit(f'No encuentro el archivo {video}.')
        if video.parent.parent == destino.resolve():
            # uno que ya se bajó (para mirar un tramo con más cuadros): se queda en su carpeta y con sus datos
            carpeta = video.parent
            viejos = carpeta / 'datos.json'
            datos = json.loads(viejos.read_text(encoding='utf-8')) if viejos.exists() else {'titulo': video.name}
        else:
            carpeta = destino / nombre_limpio(video.stem)
            carpeta.mkdir(parents=True, exist_ok=True)
            datos = {'titulo': video.name}
    (carpeta / 'datos.json').write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding='utf-8')

    dura, ancho, alto, tiene_audio = medir(video, ff)
    if not dura:
        sys.exit('No pude leer el vídeo (¿está dañado?).')
    print(f'✓ Vídeo: {reloj(dura)}, {"vertical" if alto > ancho else "horizontal"}', flush=True)
    if desde is not None or hasta is not None:
        lupa(video, ff, carpeta, desde or 0.0, min(hasta if hasta is not None else dura, dura), cada or 0.1,
             VERTICAL if alto >= ancho else HORIZONTAL)
        return

    # cuántos cuadros: uno cada medio segundo en un Reel; en uno largo, los justos para no pasar de unas 12 hojas
    if cada is None:
        cada = 0.5 if dura <= 90 else 1 if dura <= 180 else 2 if dura <= 480 else round(dura / 240)
    forma = VERTICAL if alto >= ancho else HORIZONTAL
    por_hoja = forma['columnas'] * forma['filas']

    gancho = sacar_cuadros(video, ff, GANCHO_FPS, round(forma['mini'] * 0.85), dura=GANCHO_SEGUNDOS)
    if gancho:
        hoja(gancho, 8 if forma is VERTICAL else 6, carpeta / 'gancho.jpg', True)
    for viejo in carpeta.glob('hoja-*.jpg'):
        viejo.unlink()
    cuadros = sacar_cuadros(video, ff, 1 / cada, forma['mini'])
    imagenes = []
    for n, k in enumerate(range(0, len(cuadros), por_hoja), 1):
        trozo = cuadros[k:k + por_hoja]
        ruta = f'hoja-{n:02d}.jpg'
        hoja(trozo, forma['columnas'], carpeta / ruta, cada < 1)
        imagenes.append((ruta, trozo[0][0], min(dura, trozo[-1][0] + cada)))
    print(f'✓ {len(cuadros)} cuadros, uno cada {str(cada).replace(".", ",")} s, en {len(imagenes)} hojas', flush=True)

    planos = cortes(video, ff)
    print(f'✓ {len(planos)} cambios de plano', flush=True)

    frases, palabras, idioma = [], [], None
    if tiene_audio:
        print('Escribiendo lo que se dice… (la primera vez baja el modelo de voz: unos minutos)', flush=True)
        a = audio(video, ff)
        if a.size > 8000:
            frases, palabras, idioma = transcribir(a, modelo)
    (carpeta / 'voz.json').write_text(json.dumps(
        {'idioma': idioma,
         'frases': [{'ini': round(a, 2), 'fin': round(b, 2), 'texto': t} for a, b, t in frases],
         'palabras': [{'palabra': p, 'ini': round(a, 2), 'fin': round(b, 2)} for p, a, b in palabras]},
        ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'✓ Lo que se dice: {len(palabras)} palabras' if palabras else '✓ No se oye voz', flush=True)

    resumen(carpeta, datos, dura, ancho, alto, frases, palabras, idioma, planos, imagenes, cada)
    print(f'\nListo: {carpeta / "RESUMEN.md"}')
    print('Ahora se leen, en este orden: RESUMEN.md, gancho.jpg y las hojas.')


if __name__ == '__main__':
    main()
