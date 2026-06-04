#!/usr/bin/env python3
# ============================================================
#  tools/marker_tool.py
#  Click on image differences to auto-generate level data
#
#  Usage: python marker_tool.py
#  Install: pip install Pillow
# ============================================================

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json, os

try:
    from PIL import Image, ImageTk, ImageDraw
except ImportError:
    print("Install Pillow: pip install Pillow")
    exit(1)

IMG_W, IMG_H = 660, 500

class MarkerTool:
    def __init__(self):
        self.root   = tk.Tk()
        self.root.title("Spot the Difference — Marker Tool")
        self.root.configure(bg="#0d0d1a")
        self.root.geometry("1440x680")

        self.img1_path = ""
        self.img2_path = ""
        self.img1_orig = None
        self.img2_orig = None
        self.markers   = []
        self.radius    = 30

        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        # Top bar
        top = tk.Frame(self.root, bg="#1a1a2e", pady=8)
        top.pack(fill=tk.X)

        tk.Button(top, text="📂 Load Image 1 (Original)", command=self._load1,
                  bg="#6c5ce7", fg="white", font=("Consolas",12), padx=10).pack(side=tk.LEFT, padx=8)
        tk.Button(top, text="📂 Load Image 2 (Modified)", command=self._load2,
                  bg="#a855f7", fg="white", font=("Consolas",12), padx=10).pack(side=tk.LEFT, padx=8)
        tk.Button(top, text="↩ Undo", command=self._undo,
                  bg="#e67e22", fg="white", font=("Consolas",12), padx=10).pack(side=tk.LEFT, padx=8)
        tk.Button(top, text="🗑 Clear All", command=self._clear,
                  bg="#e74c3c", fg="white", font=("Consolas",12), padx=10).pack(side=tk.LEFT, padx=8)
        tk.Button(top, text="💾 Save Level JSON", command=self._save,
                  bg="#2ecc71", fg="white", font=("Consolas",12,  "bold"), padx=10).pack(side=tk.LEFT, padx=8)

        # Radius
        tk.Label(top, text="Radius:", bg="#1a1a2e", fg="#ffcc44",
                 font=("Consolas",12)).pack(side=tk.LEFT, padx=(20,4))
        self.radius_var = tk.IntVar(value=30)
        tk.Scale(top, from_=10, to=70, orient=tk.HORIZONTAL,
                 variable=self.radius_var, bg="#1a1a2e", fg="#ffcc44",
                 length=120, command=lambda v: setattr(self,'radius',int(v))
                 ).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Load both images to start marking differences")
        tk.Label(top, textvariable=self.status_var, bg="#1a1a2e", fg="#aaffaa",
                 font=("Consolas",11)).pack(side=tk.LEFT, padx=20)

        # Canvas area
        mid = tk.Frame(self.root, bg="#0d0d1a")
        mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        self.canvas = tk.Canvas(mid, width=IMG_W*2+30, height=IMG_H+30,
                                bg="#0d0d1a", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT)
        self.canvas.bind("<Button-1>", self._on_click)

        # Right: marker list
        right = tk.Frame(mid, bg="#0d0d1a")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        tk.Label(right, text="Marked Differences", bg="#0d0d1a", fg="#6c5ce7",
                 font=("Consolas",13,"bold")).pack(anchor=tk.W)
        self.list_box = tk.Text(right, bg="#1a1a2e", fg="#aaffaa",
                                font=("Consolas",11), width=36, state=tk.DISABLED)
        self.list_box.pack(fill=tk.BOTH, expand=True)

        # How-to
        tk.Label(right, text="LEFT CLICK → Mark difference\nScroll slider → change radius\nUndo → remove last\nSave → export JSON",
                 bg="#0d0d1a", fg="#666688", font=("Consolas",10),
                 justify=tk.LEFT).pack(anchor=tk.W, pady=8)

    def _load1(self):
        p = filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg")])
        if not p: return
        self.img1_path = p
        self.img1_orig = Image.open(p).convert("RGB")
        self._render()

    def _load2(self):
        p = filedialog.askopenfilename(filetypes=[("Images","*.png *.jpg *.jpeg")])
        if not p: return
        self.img2_path = p
        self.img2_orig = Image.open(p).convert("RGB")
        self._render()

    def _on_click(self, event):
        if not self.img1_orig or not self.img2_orig: return
        # Which side?
        if event.x > IMG_W + 15:
            ix = event.x - (IMG_W + 30)
        else:
            ix = event.x - 5
        iy = event.y - 5

        # Scale back to original image coords
        scale_x = self.img1_orig.width  / IMG_W
        scale_y = self.img1_orig.height / IMG_H
        orig_x = int(ix * scale_x)
        orig_y = int(iy * scale_y)

        self.markers.append({"cx": orig_x, "cy": orig_y,
                              "radius": self.radius,
                              "desc": f"Difference {len(self.markers)+1}"})
        self._render()

    def _undo(self):
        if self.markers: self.markers.pop(); self._render()

    def _clear(self):
        if messagebox.askyesno("Clear", "Remove all markers?"): self.markers=[]; self._render()

    def _render(self):
        self.canvas.delete("all")
        def draw_img(img_orig, offset_x):
            img_r = img_orig.resize((IMG_W, IMG_H), Image.LANCZOS)
            draw  = ImageDraw.Draw(img_r)
            scale_x = IMG_W / img_orig.width
            scale_y = IMG_H / img_orig.height
            for i, m in enumerate(self.markers):
                cx_d = int(m["cx"] * scale_x)
                cy_d = int(m["cy"] * scale_y)
                r_d  = int(m["radius"] * min(scale_x, scale_y))
                draw.ellipse([cx_d-r_d,cy_d-r_d,cx_d+r_d,cy_d+r_d], outline="#00ff88", width=3)
                draw.text((cx_d-6,cy_d-10), str(i+1), fill="#00ff88")
            return ImageTk.PhotoImage(img_r)

        if self.img1_orig:
            self.tk1 = draw_img(self.img1_orig, 0)
            self.canvas.create_image(5, 5, anchor=tk.NW, image=self.tk1)
            self.canvas.create_text(5+IMG_W//2, IMG_H+18, text="Image 1 — Original",
                                    fill="#888888", font=("Consolas",11))
        if self.img2_orig:
            self.tk2 = draw_img(self.img2_orig, IMG_W+30)
            self.canvas.create_image(IMG_W+25, 5, anchor=tk.NW, image=self.tk2)
            self.canvas.create_text(IMG_W+25+IMG_W//2, IMG_H+18, text="Image 2 — Modified",
                                    fill="#888888", font=("Consolas",11))

        self.canvas.create_line(IMG_W+12, 0, IMG_W+12, IMG_H+30, fill="#333355", width=2)

        # Update marker list
        self.list_box.config(state=tk.NORMAL)
        self.list_box.delete("1.0", tk.END)
        for i, m in enumerate(self.markers):
            self.list_box.insert(tk.END, f"{i+1}. ({m['cx']},{m['cy']}) r={m['radius']}\n")
        self.list_box.config(state=tk.DISABLED)
        self.status_var.set(f"{len(self.markers)} difference(s) marked | Radius: {self.radius}px")

    def _save(self):
        if not self.img1_path or not self.img2_path:
            messagebox.showerror("Error","Load both images first"); return
        if not self.markers:
            messagebox.showerror("Error","Mark at least one difference first"); return

        lvl_id   = simpledialog.askinteger("Level ID","Enter level ID (1-9):",minvalue=1,maxvalue=9)
        if not lvl_id: return
        title    = simpledialog.askstring("Title","Level title (e.g. 'Kitchen Morning'):") or f"Level {lvl_id}"
        category = simpledialog.askstring("Category","Category (easy/medium/hard):") or "easy"
        t_limit  = simpledialog.askinteger("Time","Time limit in seconds:",initialvalue=120)
        max_w    = simpledialog.askinteger("Lives","Max wrong clicks (lives):",initialvalue=5)

        # Copy images to assets/levels/
        import shutil
        cat_prefix = {"easy":"easy","medium":"med","hard":"hard"}.get(category,"easy")
        col_map    = {1:"1",2:"2",3:"3",4:"1",5:"2",6:"3",7:"1",8:"2",9:"3"}
        n          = col_map.get(lvl_id,"1")
        dest1 = f"../frontend/assets/levels/{cat_prefix}_{n}a.png"
        dest2 = f"../frontend/assets/levels/{cat_prefix}_{n}b.png"
        os.makedirs("../frontend/assets/levels", exist_ok=True)
        try:
            shutil.copy2(self.img1_path, dest1)
            shutil.copy2(self.img2_path, dest2)
            print(f"[Tool] Copied images → {dest1}, {dest2}")
        except Exception as e:
            print(f"[Tool] Could not copy images: {e}")

        # Update level definition in game_engine.py message
        result = {
            "id": lvl_id, "title": title, "category": category,
            "img1": dest1.replace("../",""), "img2": dest2.replace("../",""),
            "time_limit": t_limit, "max_wrong": max_w, "tolerance": 20,
            "differences": self.markers
        }
        out_path = f"../data/level_{lvl_id:02d}_marker_output.json"
        os.makedirs("../data", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)

        # Also print the Python dict to paste into game_engine.py
        print("\n" + "="*60)
        print("COPY THIS INTO game_engine.py → LEVEL_DEFINITIONS:")
        print("="*60)
        print(json.dumps(result, indent=4))
        print("="*60 + "\n")

        messagebox.showinfo("Saved",
            f"Saved {len(self.markers)} differences!\n"
            f"Output: {out_path}\n\n"
            f"Also check the terminal — copy the printed dict\n"
            f"into LEVEL_DEFINITIONS in game_engine.py")

if __name__ == "__main__":
    MarkerTool()
