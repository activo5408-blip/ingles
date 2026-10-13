#!/usr/bin/env python3
"""Generador básico de lecciones de inglés para Windows 10/11.
Uso: python crear_video.py lecciones/leccion-01.json
"""
import argparse, json, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H = 1920, 1080
BG, FG, MUTED, ACCENT = "#0f172a", "#f8fafc", "#94a3b8", "#fbbf24"
FONT_CANDIDATES = ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
def font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
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
def main():
    ap=argparse.ArgumentParser(description="Crear vídeo de una lección")
    ap.add_argument("leccion", help="Ruta del JSON de la lección")
    args=ap.parse_args()
    lp=Path(args.leccion).resolve()
    lesson=json.loads(lp.read_text(encoding="utf-8-sig"))
    scenes=lesson.get("escenas",[])
    if not scenes: raise ValueError("El JSON no contiene escenas.")
    name=lp.stem; out=ROOT/"salida"/name; slides=out/"slides"; texts=out/"texto-para-voz"; tmp=out/"tmp"
    audio=ROOT/"audio"/name
    for p in (slides,texts,tmp,audio): p.mkdir(parents=True,exist_ok=True)
    for old in texts.glob("*.txt"): old.unlink()
    title=lesson.get("titulo",name)
    durations=[]; segments=[]
    for i,sc in enumerate(scenes,1):
        text=" ".join(sc.get("texto","").split())
        (texts/f"{i:02d}.txt").write_text(text+"\n",encoding="utf-8")
        sp=slides/f"{i:02d}.png"; render_slide(sc,title,sp)
        if sc.get("practica"): render_slide(sc,title,slides/f"{i:02d}-practica.png",True)
        candidates=[audio/f"{i:02d}{ext}" for ext in (".mp3",".wav",".m4a",".aac",".ogg",".opus",".flac")]
        apath=next((p for p in candidates if p.exists()),None)
        if apath:
            dur=float(run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(apath)]))
            pause=float(sc.get("pausa",0.8))
            seg=tmp/f"{i:02d}.mp4"
            run(["ffmpeg","-y","-loop","1","-framerate","25","-i",str(sp),"-i",str(apath),
                 "-f","lavfi","-t",str(pause),"-i","anullsrc=r=44100:cl=stereo",
                 "-filter_complex",f"[1:a]aresample=44100[a1];[2:a]atrim=duration={pause},asetpts=PTS-STARTPTS[a2];[a1][a2]concat=n=2:v=0:a=1[a]",
                 "-map","0:v","-map","[a]","-t",str(dur+pause),"-vf","format=yuv420p","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","-c:a","aac","-shortest",str(seg)])
            durations.append(dur+pause)
        else:
            dur=max(3.0,len(text.split())/2.3+float(sc.get("pausa",0.8)))
            seg=tmp/f"{i:02d}.mp4"
            run(["ffmpeg","-y","-loop","1","-framerate","25","-i",str(sp),"-f","lavfi","-i","anullsrc=r=44100:cl=stereo","-t",str(dur),"-vf","format=yuv420p","-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","-c:a","aac","-shortest",str(seg)])
            durations.append(dur)
        segments.append(seg)
        print(f"Escena {i}/{len(scenes)} lista")
    concat=tmp/"lista.txt"
    concat.write_text("".join("file '"+str(p).replace("\\","/").replace("'","'\\''")+"'\n" for p in segments),encoding="utf-8")
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(out/f"{name}.mp4")])
    total=sum(durations); elapsed=0; chapters=[]
    for i,(sc,dur) in enumerate(zip(scenes,durations),1):
        if sc.get("capitulo"): chapters.append(f"{int(elapsed//60)}:{int(elapsed%60):02d} {sc['capitulo']}")
        elapsed+=dur
    (out/"capitulos.txt").write_text("\n".join(chapters)+"\n",encoding="utf-8")
    description=title+"\n\n"+ "\n".join(f"- {s.get('capitulo','Escena '+str(i))}: {s.get('texto','')[:180]}" for i,s in enumerate(scenes,1))
    (out/"descripcion-youtube.txt").write_text(description+"\n",encoding="utf-8")
    thumb=Image.new("RGB",(1280,720),BG); d=ImageDraw.Draw(thumb)
    big=lesson.get("miniatura",{}).get("grande",title); small=lesson.get("miniatura",{}).get("chico","INGLÉS PRÁCTICO")
    f=font(92)
    while d.textlength(big,font=f)>1100 and f.size>40: f=font(f.size-4)
    d.rectangle([0,0,24,720],fill=ACCENT); d.text((80,230),big,font=f,fill=ACCENT); d.text((80,360),small,font=font(54),fill=FG)
    thumb.save(out/"miniatura.png")
    (out/"indice.txt").write_text("Escena | Capítulo | Duración aproximada (s)\n"+"\n".join(f"{i:02d} | {s.get('capitulo','-')} | {d:.1f}" for i,(s,d) in enumerate(zip(scenes,durations),1))+"\n",encoding="utf-8")
    print(f"Vídeo creado: {out/name}.mp4")
    print(f"Resultados y archivos auxiliares: {out}")
if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"ERROR: {e}",file=sys.stderr); sys.exit(1)
