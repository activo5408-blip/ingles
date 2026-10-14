#!/usr/bin/env python3
"""Generador de lecciones para Windows. Admite una narración única de ElevenLabs."""
import argparse, json, subprocess, sys, shutil, re, unicodedata
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1920, 1080
BG, FG, MUTED, ACCENT = "#0f172a", "#f8fafc", "#94a3b8", "#fbbf24"
FONT_CANDIDATES = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
AUDIO_EXTS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".opus", ".flac")

def font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for word in str(text).split():
        test = (cur + " " + word).strip()
        if not cur or draw.textlength(test, font=fnt) <= max_w: cur = test
        else: lines.append(cur); cur = word
    if cur: lines.append(cur)
    return lines

def render_slide(scene, title, path, practice=False, hide_blocks=False):
    """Diseño editorial moderno para clases: fondos, tarjetas y recursos visuales según el tipo de actividad."""
    im = Image.new("RGB", (W, H))
    px = im.load()
    # Fondo degradado azul noche con un brillo lateral suave.
    top = (10, 17, 35); bottom = (18, 32, 58)
    for y in range(H):
        t = y / max(1, H-1)
        base = tuple(int(top[i]*(1-t) + bottom[i]*t) for i in range(3))
        for x in range(W):
            glow = max(0, 1 - (((x-1570)/760)**2 + ((y-220)/650)**2)**0.5) * 10
            px[x,y] = tuple(min(255, int(c+glow*(1 if i==2 else 0.65))) for i,c in enumerate(base))
    d = ImageDraw.Draw(im)
    accent = "#f6c453"; white = "#f7f9ff"; muted = "#a8b6cc"
    panel = "#172640"; panel2 = "#1d3150"; green = "#6ee7b7"; blue = "#78b7ff"
    kicker = str(scene.get("kicker", "INGLÉS PRÁCTICO")).upper()
    chapter = str(scene.get("capitulo", title))
    blocks = scene.get("bloques", [{"texto": scene.get("texto", ""), "estilo": "principal"}])
    chapter_l = (chapter + " " + kicker).lower()
    if any(k in chapter_l for k in ("convers", "dialog", "escucha")):
        mode = "dialogo"
    elif any(k in chapter_l for k in ("práctica", "practica", "repaso", "ahora te", "cierre")):
        mode = "practica"
    elif any(k in chapter_l for k in ("bienvenida", "objetivo", "introduc", "presenta")):
        mode = "inicio"
    elif any(k in chapter_l for k in ("vocab", "palabra", "saludar", "desped", "nombre", "preguntar", "país", "pais")):
        mode = "vocabulario"
    else:
        mode = "explicacion"

    # Marca de capítulo y cabecera de estilo editorial.
    d.rounded_rectangle((80, 64, 92, 126), radius=6, fill=accent)
    d.text((122, 72), kicker, font=font(30), fill=accent)
    d.text((122, 116), chapter, font=font(26), fill=muted)
    d.line((80, 166, 1840, 166), fill="#30415d", width=2)

    # Marco visual cambia con la dinámica didáctica de cada escena.
    if mode == "inicio":
        d.rounded_rectangle((120, 245, 1800, 815), radius=42, fill=panel, outline="#314969", width=2)
        d.ellipse((1450, 315, 1690, 555), fill=panel2, outline=accent, width=5)
        d.ellipse((1510, 375, 1630, 495), outline=blue, width=7)
        d.line((1530, 435, 1560, 465, 1615, 400), fill=green, width=12)
        d.rounded_rectangle((220, 675, 690, 735), radius=25, fill="#263d5d")
        d.text((255, 691), "ESCUCHA  ·  COMPRENDE  ·  HABLA", font=font(23), fill=white)
    elif mode == "dialogo":
        d.rounded_rectangle((110, 260, 900, 790), radius=36, fill=panel, outline="#304969", width=2)
        d.rounded_rectangle((1020, 260, 1810, 790), radius=36, fill=panel2, outline="#304969", width=2)
        d.ellipse((170, 315, 250, 395), fill=accent)
        d.ellipse((1080, 315, 1160, 395), fill=blue)
        d.text((190, 330), "A", font=font(38), fill="#101a2c")
        d.text((1100, 330), "B", font=font(38), fill="#101a2c")
        d.rounded_rectangle((220, 690, 790, 742), radius=22, fill="#263d5d")
        d.rounded_rectangle((1120, 690, 1690, 742), radius=22, fill="#263d5d")
        d.text((350, 704), "ESCUCHA A", font=font(22), fill=white)
        d.text((1250, 704), "RESPONDE B", font=font(22), fill=white)
        d.line((940, 400, 980, 400), fill=accent, width=8)
        d.polygon([(980,400),(960,384),(960,416)], fill=accent)
    elif mode == "practica":
        d.rounded_rectangle((120, 245, 1800, 815), radius=42, fill=panel, outline="#314969", width=2)
        for i, (label, color) in enumerate((("1", accent), ("2", blue), ("3", green))):
            cx = 420 + i*540
            d.ellipse((cx-58, 330, cx+58, 446), fill=color)
            ff = font(54); tw = d.textlength(label, font=ff)
            d.text((cx-tw/2, 350), label, font=ff, fill="#101a2c")
            if i < 2:
                d.line((cx+90, 388, cx+360, 388), fill="#3c506d", width=5)
        for x, label in ((300, "ESCUCHA"), (840, "REPITE"), (1380, "PRACTICA")):
            ff=font(28); tw=d.textlength(label,font=ff)
            d.text((x-tw/2, 490), label, font=ff, fill=muted)
        d.rounded_rectangle((460, 590, 1460, 655), radius=28, fill="#263d5d")
        d.text((570, 608), "TU TURNO · HABLA EN VOZ ALTA", font=font(26), fill=green)
    elif mode == "vocabulario":
        d.rounded_rectangle((120, 245, 1800, 815), radius=42, fill=panel, outline="#314969", width=2)
        # Tarjetas de aprendizaje para inglés, traducción y pronunciación.
        cards = [(190, 570, 650, 730, accent), (730, 570, 1190, 730, blue), (1270, 570, 1730, 730, green)]
        labels = ["ENGLISH", "ESPAÑOL", "PRONUNCIACIÓN"]
        for (x1,y1,x2,y2,c), label in zip(cards,labels):
            d.rounded_rectangle((x1,y1,x2,y2), radius=24, fill=panel2, outline=c, width=3)
            ff=font(22); d.text((x1+28,y1+22), label, font=ff, fill=c)
        d.ellipse((820, 320, 1100, 500), outline=accent, width=8)
        d.arc((870, 355, 1050, 465), 15, 165, fill=blue, width=7)
        d.line((920, 420, 950, 450, 1010, 380), fill=green, width=9)
    else:
        d.rounded_rectangle((120, 245, 1800, 815), radius=42, fill=panel, outline="#314969", width=2)
        d.rounded_rectangle((150, 285, 1768, 335), radius=18, fill="#223958")
        d.ellipse((1680, 275, 1728, 323), fill=accent)
        d.ellipse((1692, 287, 1716, 311), fill=panel)
        # Puntos de avance y líneas de apoyo visual.
        for i in range(5):
            x = 260 + i*330
            d.ellipse((x-8, 700, x+8, 716), fill=accent if i == 0 else "#50627d")
        d.line((280, 745, 1640, 745), fill="#30415d", width=3)

    # En modo de karaoke, el texto lo aporta el subtítulo sincronizado; el diseño queda despejado.
    if not hide_blocks:
        colors = {"principal": white, "secundario": muted, "nota": accent, "bueno": green, "malo": "#fca5a5", "dialogo": white}
        sizes = {"principal": 76, "secundario": 48, "nota": 40, "bueno": 68, "malo": 68, "dialogo": 46}
        rows, total = [], 0
        for b in blocks:
            size = sizes.get(b.get("estilo", "principal"), 58); f = font(size)
            lines = wrap(d, b.get("texto", ""), f, W-320)
            while len(lines) > 2 and size > 34:
                size -= 3; f = font(size); lines = wrap(d, b.get("texto", ""), f, W-320)
            rows.append((b, lines, f, size, colors.get(b.get("estilo", "principal"), white)))
            total += len(lines) * int(size*1.22) + (34 if b.get("etiqueta") else 0) + 16
        y = max(340, min(560, 535-total//2))
        for b, lines, f, size, color in rows:
            if b.get("etiqueta"):
                ef=font(26); label=b["etiqueta"]; d.text(((W-d.textlength(label,font=ef))/2,y),label,font=ef,fill=color); y+=36
            for line in lines:
                x=(W-d.textlength(line,font=f))/2
                d.text((x+2,y+3),line,font=f,fill="#08111f",stroke_width=1)
                d.text((x,y),line,font=f,fill=color)
                y+=int(size*1.22)
            y+=16

    # Pie con marca, número de capítulo y barra de progreso.
    d.line((80, 930, 1840, 930), fill="#30415d", width=2)
    d.text((82, 958), "CANAL DE INGLÉS", font=font(22), fill=muted)
    d.text((1500, 958), "APRENDE · PRACTICA · AVANZA", font=font(20), fill=muted)
    d.rounded_rectangle((80, 1020, 1840, 1030), radius=5, fill="#263750")
    d.rounded_rectangle((80, 1020, 520 if mode=="inicio" else 920 if mode=="vocabulario" else 1320 if mode=="dialogo" else 1640, 1030), radius=5, fill=accent)
    if practice:
        label="AHORA TÚ · REPITE EN VOZ ALTA"; f=font(34); x=(W-d.textlength(label,font=f))/2
        d.rounded_rectangle([350,H-190,1570,H-90],radius=24,fill=accent); d.text((x,H-170),label,font=f,fill="#1a1204")
    im.save(path)

def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace",cwd=str(ROOT))
    if p.returncode: raise RuntimeError(p.stderr[-2500:] or "Error ejecutando: "+cmd[0])
    return p.stdout.strip()

def duration(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)]))


def normalize_words(text):
    text = unicodedata.normalize("NFKD", str(text).lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.findall(r"[a-z0-9]+(?:['’][a-z0-9]+)?", text)

def ass_time(seconds):
    cs = max(0, int(round(seconds * 100)))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def karaoke_ass(scene, seconds, path):
    """Karaoke aproximado: los bloques se iluminan por palabra al ritmo estimado de la narración."""
    voice = str(scene.get("voz", scene.get("texto", "")))
    tokens = normalize_words(voice)
    blocks = scene.get("bloques", [{"texto": scene.get("texto", ""), "estilo": "principal"}])
    events = []
    used_until = 0
    for block in blocks:
        phrase = str(block.get("texto", "")).strip()
        words = normalize_words(phrase)
        if not words:
            continue
        found = -1
        for pos in range(used_until, max(used_until, len(tokens)-len(words)+1)):
            if tokens[pos:pos+len(words)] == words:
                found = pos
                break
        if found >= 0:
            start_ratio = found / max(1, len(tokens))
            used_until = found + len(words)
        else:
            start_ratio = min(0.88, len(events) / max(1, len(blocks)) * 0.82)
        span = max(1.0, seconds * len(words) / max(1, len(tokens)) * 1.18)
        start = min(max(0, seconds-0.5), start_ratio * seconds)
        end = min(seconds, start + span)
        weights = [max(2, len(w)) for w in words]
        total = sum(weights)
        tags = []
        for j, (word, weight) in enumerate(zip(words, weights)):
            word_dur = max(0.08, (end-start) * weight/total)
            tags.append(r"{\kf%d}%s" % (max(1, int(round(word_dur*100))), word))
            if j < len(words)-1: tags.append(" ")
        events.append((start, end, "".join(tags)))
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Arial,72,&H0000D7FF,&H00FFFFFF,&H00101828,&H80101828,-1,0,1,3,1,5,100,100,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]
    for start, end, text in events:
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Karaoke,,0,0,0,,{{\\an5\\pos(960,480)}}{text}\n")
    path.write_text("".join(lines), encoding="utf-8-sig")
    return bool(events)

def main():
    ap=argparse.ArgumentParser(description="Crear vídeo de una lección")
    ap.add_argument("leccion", help="Ruta del JSON de la lección")
    args=ap.parse_args()
    missing=[tool for tool in ("ffmpeg","ffprobe") if shutil.which(tool) is None]
    if missing:
        raise RuntimeError("No se encuentra "+ " y ".join(missing) +". Comprueba FFmpeg y su carpeta bin en el PATH.")
    lp=Path(args.leccion).resolve()
    if not lp.is_file(): raise FileNotFoundError(f"No se encuentra el JSON: {lp}")
    lesson=json.loads(lp.read_text(encoding="utf-8-sig"))
    scenes=lesson.get("escenas",[])
    if not scenes: raise ValueError("El JSON no contiene escenas.")
    name=lp.stem; out=ROOT/"salida"/name; slides=out/"slides"; texts=out/"texto-para-voz"; tmp=out/"tmp"
    audio=ROOT/"audio"/name
    for p in (slides,texts,tmp,audio): p.mkdir(parents=True,exist_ok=True)
    for old in texts.glob("*.txt"): old.unlink()
    title=lesson.get("titulo",name)
    # Un solo TXT listo para copiar y pegar en ElevenLabs, en el orden de las escenas.
    narration="\n\n".join(" ".join(str(sc.get("voz",sc.get("texto",""))).split()) for sc in scenes).strip()
    script_path=out/"texto-para-elevenlabs.txt"
    script_path.write_text(narration+"\n",encoding="utf-8")
    # También conserva un TXT por escena como apoyo, pero el principal es el único TXT completo.
    weights=[max(1,len(str(sc.get("voz",sc.get("texto",""))).split())) for sc in scenes]
    narration_file=next((audio/("narracion"+ext) for ext in AUDIO_EXTS if (audio/("narracion"+ext)).exists()),None)
    # La duración objetivo manda: si el audio de ElevenLabs no mide exactamente lo mismo,
    # ajustamos ligeramente su velocidad para que el vídeo final mantenga los 8 minutos.
    target_seconds=max(60,float(lesson.get("objetivo_minutos",8))*60)
    narration_duration=duration(narration_file) if narration_file else None
    total_weight=sum(weights)
    durations=[target_seconds*w/total_weight for w in weights]
    segments=[]
    for i,sc in enumerate(scenes,1):
        scene_text=" ".join(str(sc.get("voz",sc.get("texto",""))).split())
        (texts/f"{i:02d}.txt").write_text(scene_text+"\n",encoding="utf-8")
        seg=tmp/f"{i:02d}.mp4"; dur=durations[i-1]
        sp=slides/f"{i:02d}.png"; render_slide(sc,title,sp,hide_blocks=True)
        ass_path=tmp/f"karaoke_{i:02d}.ass"
        has_karaoke=karaoke_ass(sc,dur,ass_path)
        if not has_karaoke:
            render_slide(sc,title,sp)
        if sc.get("practica"): render_slide(sc,title,slides/f"{i:02d}-practica.png",True)
        filters = f"ass={ass_path.relative_to(ROOT).as_posix()},format=yuv420p" if has_karaoke else "format=yuv420p"
        run(["ffmpeg","-y","-loop","1","-framerate","25","-i",str(sp),
             "-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-t",f"{dur:.3f}",
             "-vf",filters,"-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",
             "-c:a","aac","-b:a","128k","-shortest",str(seg)])
        segments.append(seg)
        print(f"Escena {i}/{len(scenes)} lista ({dur:.0f} s)")
    concat=tmp/"lista.txt"
    concat.write_text("".join("file '"+str(p).replace("\\","/").replace("'","'\\''")+"'\n" for p in segments),encoding="utf-8")
    silent_video=tmp/"video_base.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent_video)])
    final=out/f"{name}.mp4"
    if narration_file:
        tempo=max(0.5,min(2.0,narration_duration/target_seconds))
        run(["ffmpeg","-y","-i",str(silent_video),"-i",str(narration_file),"-map","0:v:0","-map","1:a:0",
             "-c:v","copy","-filter:a",f"atempo={tempo:.6f}","-c:a","aac","-b:a","192k",
             "-t",f"{target_seconds:.3f}","-movflags","+faststart",str(final)])
        print(f"Narración incorporada: {narration_file}")
    else:
        shutil.copy2(silent_video,final)
        print("AVISO: vídeo de 8 minutos sin narración. Genera el audio en ElevenLabs y guárdalo como audio/"+name+"/narracion.mp3; luego vuelve a crear el vídeo.")
    total=duration(final); elapsed=0; chapters=[]
    for i,(sc,dur) in enumerate(zip(scenes,durations),1):
        if sc.get("capitulo"): chapters.append(f"{int(elapsed//60)}:{int(elapsed%60):02d} {sc['capitulo']}")
        elapsed+=dur
    (out/"capitulos.txt").write_text("\n".join(chapters)+"\n",encoding="utf-8")
    description=title+"\n\n"+ "\n".join(f"- {s.get('capitulo','Escena '+str(i))}: {s.get('texto',s.get('voz',''))[:180]}" for i,s in enumerate(scenes,1))
    (out/"descripcion-youtube.txt").write_text(description+"\n",encoding="utf-8")
    thumb=Image.new("RGB",(1280,720),BG); d=ImageDraw.Draw(thumb)
    big=lesson.get("miniatura",{}).get("grande",title); small=lesson.get("miniatura",{}).get("chico","INGLÉS PRÁCTICO")
    f=font(92)
    while d.textlength(big,font=f)>1100 and f.size>40: f=font(f.size-4)
    d.rectangle([0,0,24,720],fill=ACCENT); d.text((80,230),big,font=f,fill=ACCENT); d.text((80,360),small,font=font(54),fill=FG)
    thumb.save(out/"miniatura.png")
    (out/"indice.txt").write_text("Escena | Capítulo | Duración aproximada (s)\n"+"\n".join(f"{i:02d} | {s.get('capitulo','-')} | {d:.1f}" for i,(s,d) in enumerate(zip(scenes,durations),1))+f"\nDuración final del vídeo: {int(total//60)}:{int(total%60):02d}\n",encoding="utf-8")
    print(f"Vídeo creado: {final}")
    print(f"Duración final: {int(total//60)} min {int(total%60):02d} s")
    print(f"TXT completo para ElevenLabs: {script_path}")
    print(f"Resultados: {out}")

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"ERROR: {e}",file=sys.stderr); sys.exit(1)
