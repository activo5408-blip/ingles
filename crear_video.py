#!/usr/bin/env python3
"""Generador de lecciones para Windows. Admite una narración única de ElevenLabs."""
import argparse, json, subprocess, sys, shutil
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

def render_slide(scene, title, path, practice=False):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    if scene.get("kicker"): d.text((120, 80), scene["kicker"], font=font(38), fill=ACCENT)
    blocks = scene.get("bloques", [{"texto": scene.get("texto", ""), "estilo": "principal"}])
    colors = {"principal": FG, "secundario": MUTED, "nota": ACCENT, "bueno": "#4ade80", "malo": "#f87171", "dialogo": FG}
    sizes = {"principal": 88, "secundario": 52, "nota": 44, "bueno": 78, "malo": 78, "dialogo": 48}
    rows, total = [], 0
    for b in blocks:
        size = sizes.get(b.get("estilo", "principal"), 72); f = font(size)
        lines = wrap(d, b.get("texto", ""), f, W-280)
        while len(lines) > 3 and size > 36:
            size -= 4; f = font(size); lines = wrap(d, b.get("texto", ""), f, W-280)
        rows.append((b, lines, f, size, colors.get(b.get("estilo", "principal"), FG)))
        total += len(lines) * int(size*1.3) + (42 if b.get("etiqueta") else 0) + 28
    y = max(170, (H - total) // 2)
    for b, lines, f, size, color in rows:
        if b.get("etiqueta"):
            ef=font(30); label=b["etiqueta"]; d.text(((W-d.textlength(label,font=ef))/2,y),label,font=ef,fill=color); y+=42
        for line in lines:
            x=120 if scene.get("alineacion")=="izquierda" else (W-d.textlength(line,font=f))/2
            d.text((x,y),line,font=f,fill=color); y+=int(size*1.3)
        y+=28
    if practice:
        label="AHORA TÚ · REPITE EN VOZ ALTA"; f=font(42); x=(W-d.textlength(label,font=f))/2
        d.rounded_rectangle([350,H-190,1570,H-90],radius=24,fill=ACCENT); d.text((x,H-170),label,font=f,fill="#1a1204")
    d.text((120,H-70),title,font=font(28),fill=MUTED)
    im.save(path)

def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True,encoding="utf-8",errors="replace")
    if p.returncode: raise RuntimeError(p.stderr[-2500:] or "Error ejecutando: "+cmd[0])
    return p.stdout.strip()

def duration(path):
    return float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)]))

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
    target_seconds=duration(narration_file) if narration_file else max(60,float(lesson.get("objetivo_minutos",8))*60)
    total_weight=sum(weights)
    durations=[target_seconds*w/total_weight for w in weights]
    segments=[]
    for i,sc in enumerate(scenes,1):
        scene_text=" ".join(str(sc.get("voz",sc.get("texto",""))).split())
        (texts/f"{i:02d}.txt").write_text(scene_text+"\n",encoding="utf-8")
        sp=slides/f"{i:02d}.png"; render_slide(sc,title,sp)
        if sc.get("practica"): render_slide(sc,title,slides/f"{i:02d}-practica.png",True)
        seg=tmp/f"{i:02d}.mp4"; dur=durations[i-1]
        run(["ffmpeg","-y","-loop","1","-framerate","25","-i",str(sp),
             "-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-t",f"{dur:.3f}",
             "-vf","format=yuv420p","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p",
             "-c:a","aac","-b:a","128k","-shortest",str(seg)])
        segments.append(seg)
        print(f"Escena {i}/{len(scenes)} lista ({dur:.0f} s)")
    concat=tmp/"lista.txt"
    concat.write_text("".join("file '"+str(p).replace("\\","/").replace("'","'\\''")+"'\n" for p in segments),encoding="utf-8")
    silent_video=tmp/"video_base.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent_video)])
    final=out/f"{name}.mp4"
    if narration_file:
        run(["ffmpeg","-y","-i",str(silent_video),"-i",str(narration_file),"-map","0:v:0","-map","1:a:0",
             "-c:v","copy","-c:a","aac","-b:a","192k","-t",f"{target_seconds:.3f}","-movflags","+faststart",str(final)])
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
