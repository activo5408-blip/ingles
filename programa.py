#!/usr/bin/env python3
"""Interfaz sencilla para Canal de Inglés en Windows."""
import os, sys, json, subprocess, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

ROOT = Path(__file__).resolve().parent
FFBIN = Path(r"G:\INSTALL\!!!Proyectos Yeinier\ffmpeg\bin")
if FFBIN.is_dir():
    os.environ["PATH"] = str(FFBIN) + os.pathsep + os.environ.get("PATH", "")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Canal de Inglés · Generador de lecciones")
        self.geometry("780x520")
        self.minsize(680, 440)
        self.configure(bg="#0f172a")
        style = ttk.Style(self)
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("TFrame", background="#0f172a")
        style.configure("TLabel", background="#0f172a", foreground="#f8fafc", font=("Arial", 10))
        style.configure("Title.TLabel", font=("Arial", 20, "bold"), foreground="#fbbf24")
        style.configure("TButton", font=("Arial", 10, "bold"), padding=8)
        style.configure("TCombobox", padding=5)
        root = ttk.Frame(self, padding=22); root.pack(fill="both", expand=True)
        ttk.Label(root, text="CANAL DE INGLÉS", style="Title.TLabel").pack(anchor="w")
        ttk.Label(root, text="Prepara lecciones y genera vídeos educativos").pack(anchor="w", pady=(3,18))
        ttk.Label(root, text="Lección disponible").pack(anchor="w")
        self.lesson = tk.StringVar()
        self.combo = ttk.Combobox(root, textvariable=self.lesson, state="readonly")
        self.combo.pack(fill="x", pady=(5,10))
        self.refresh_lessons()
        buttons = ttk.Frame(root); buttons.pack(fill="x", pady=4)
        ttk.Button(buttons, text="Elegir archivo JSON…", command=self.choose).pack(side="left")
        ttk.Button(buttons, text="Abrir carpeta de resultados", command=self.open_output).pack(side="left", padx=8)
        self.runbtn = ttk.Button(root, text="▶  CREAR VÍDEO", command=self.start)
        self.runbtn.pack(anchor="w", pady=(14,10))
        ttk.Label(root, text="Registro").pack(anchor="w")
        self.log = tk.Text(root, height=12, bg="#111827", fg="#e5e7eb", insertbackground="white",
                           relief="flat", font=("Consolas", 9), wrap="word")
        self.log.pack(fill="both", expand=True, pady=(5,0))
        self.write("Listo. Selecciona una lección y pulsa CREAR VÍDEO.")
        self.write("FFmpeg detectado en: " + (str(FFBIN) if FFBIN.is_dir() else "PATH de Windows"))

    def refresh_lessons(self):
        files = sorted((ROOT / "lecciones").glob("*.json"))
        self.combo["values"] = [str(p.relative_to(ROOT)) for p in files]
        if files: self.lesson.set(str(files[0].relative_to(ROOT)))

    def write(self, text):
        self.log.insert("end", text.rstrip() + "\n"); self.log.see("end")

    def choose(self):
        p = filedialog.askopenfilename(title="Seleccionar lección JSON",
              initialdir=str(ROOT / "lecciones"), filetypes=[("Lecciones JSON","*.json"),("Todos los archivos","*.*")])
        if p:
            try:
                data = json.loads(Path(p).read_text(encoding="utf-8-sig"))
                if not data.get("escenas"): raise ValueError("El JSON no contiene escenas.")
            except Exception as e:
                messagebox.showerror("Lección inválida", str(e)); return
            self.lesson.set(os.path.relpath(p, ROOT))

    def start(self):
        p = (ROOT / self.lesson.get()).resolve()
        if not p.is_file():
            messagebox.showerror("Falta la lección", "Selecciona un archivo JSON válido."); return
        missing = [x for x in ("ffmpeg.exe","ffprobe.exe") if not ((FFBIN / x).is_file() or any((Path(d)/x).is_file() for d in os.environ.get("PATH","").split(os.pathsep) if d))]
        if missing:
            messagebox.showerror("Falta FFmpeg", "No encuentro ffmpeg.exe y ffprobe.exe. Revisa la carpeta bin de FFmpeg."); return
        self.runbtn.configure(state="disabled")
        self.write("\nGenerando: " + p.name)
        threading.Thread(target=self.worker, args=(p,), daemon=True).start()

    def worker(self, p):
        env = os.environ.copy()
        if FFBIN.is_dir(): env["PATH"] = str(FFBIN) + os.pathsep + env.get("PATH","")
        try:
            proc = subprocess.Popen([sys.executable, str(ROOT/"crear_video.py"), str(p)],
                 cwd=str(ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                 text=True, encoding="utf-8", errors="replace")
            for line in proc.stdout:
                self.after(0, self.write, line)
            code = proc.wait()
            self.after(0, self.write, "Proceso terminado correctamente." if code == 0 else f"El proceso terminó con código {code}.")
        except Exception as e:
            self.after(0, self.write, "ERROR: " + str(e))
        finally:
            self.after(0, lambda: self.runbtn.configure(state="normal"))

    def open_output(self):
        out = ROOT / "salida"
        out.mkdir(exist_ok=True)
        os.startfile(str(out))

if __name__ == "__main__":
    App().mainloop()
