import copy
import json
import os
import random
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.scrolledtext as scrolledtext
import urllib.parse
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import requests
from PIL import Image, ImageTk


HERE = Path(__file__).resolve().parent
DEFAULT_PACK = HERE / "pack.json"


class WanDesktopApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Wan 2.2 Enhanced NSFW")
        self.root.geometry("980x720")
        self.root.minsize(860, 620)

        self.image_path = tk.StringVar()
        self.comfy_url = tk.StringVar(value=os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188"))
        self.output_dir = tk.StringVar(value=str(HERE / "output"))
        self.comfy_dir = tk.StringVar(value=os.environ.get("COMFYUI_DIR", ""))
        self.prompt_id = None
        self.preview_image = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        left = ttk.Frame(outer)
        left.pack(side="left", fill="y", padx=(0, 12))
        right = ttk.Frame(outer)
        right.pack(side="right", fill="both", expand=True)

        ttk.Label(left, text="Starting image").grid(row=0, column=0, columnspan=2, sticky="w")
        self.preview = tk.Canvas(left, width=360, height=360, bg="#202020", highlightthickness=1, highlightbackground="#555")
        self.preview.grid(row=1, column=0, columnspan=2, pady=(6, 8))
        ttk.Button(left, text="Choose image...", command=self.choose_image).grid(row=2, column=0, sticky="w")
        ttk.Label(left, textvariable=self.image_path, wraplength=330).grid(row=2, column=1, sticky="w", padx=(8, 0))

        ttk.Label(left, text="Prompt").grid(row=3, column=0, columnspan=2, sticky="w", pady=(12, 4))
        self.prompt = scrolledtext.ScrolledText(left, width=44, height=7, wrap="word")
        self.prompt.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.prompt.insert("1.0", "she turns her head and smiles")

        ttk.Label(left, text="Size").grid(row=5, column=0, sticky="w", pady=(10, 4))
        self.size_name = tk.StringVar(value="Landscape")
        ttk.Combobox(left, textvariable=self.size_name, values=["Landscape", "Portrait", "Square"], state="readonly", width=18).grid(row=5, column=1, sticky="w")

        ttk.Label(left, text="Seed").grid(row=6, column=0, sticky="w", pady=(8, 4))
        seed_frame = ttk.Frame(left)
        seed_frame.grid(row=6, column=1, sticky="w")
        self.seed = tk.IntVar(value=random.randint(1, 2_147_483_647))
        ttk.Entry(seed_frame, textvariable=self.seed, width=17).pack(side="left")
        ttk.Button(seed_frame, text="Random", command=lambda: self.seed.set(random.randint(1, 2_147_483_647))).pack(side="left", padx=(6, 0))

        ttk.Label(left, text="ComfyUI address").grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 4))
        ttk.Entry(left, textvariable=self.comfy_url, width=44).grid(row=8, column=0, columnspan=2, sticky="ew")

        ttk.Label(left, text="ComfyUI directory").grid(row=9, column=0, columnspan=2, sticky="w", pady=(10, 4))
        ttk.Entry(left, textvariable=self.comfy_dir, width=44).grid(row=10, column=0, columnspan=2, sticky="ew")

        self.generate_button = ttk.Button(left, text="Generate video", command=self.generate)
        self.generate_button.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(14, 6))
        ttk.Button(left, text="Start local ComfyUI", command=self.start_comfyui).grid(row=12, column=0, columnspan=2, sticky="ew")

        ttk.Label(right, text="Status").pack(anchor="w")
        self.status = scrolledtext.ScrolledText(right, height=25, wrap="word", state="disabled")
        self.status.pack(fill="both", expand=True, pady=(6, 8))

        output_frame = ttk.Frame(right)
        output_frame.pack(fill="x")
        ttk.Label(output_frame, text="Output folder").pack(side="left")
        ttk.Entry(output_frame, textvariable=self.output_dir).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(output_frame, text="Open", command=self.open_output).pack(side="left")

        self.progress = ttk.Progressbar(right, mode="indeterminate")
        self.progress.pack(fill="x", pady=(8, 0))

    def log(self, message):
        self.root.after(0, lambda: self._append_log(message))

    def _append_log(self, message):
        self.status.configure(state="normal")
        self.status.insert("end", message.rstrip() + "\n")
        self.status.see("end")
        self.status.configure(state="disabled")

    def choose_image(self):
        path = filedialog.askopenfilename(
            title="Choose a starting image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp"), ("All files", "*.*")],
        )
        if not path:
            return
        self.image_path.set(path)
        try:
            image = Image.open(path)
            image.thumbnail((360, 360), Image.Resampling.LANCZOS)
            self.preview_image = ImageTk.PhotoImage(image)
            self.preview.delete("all")
            self.preview.create_image(180, 180, image=self.preview_image)
        except Exception as exc:
            messagebox.showerror("Image error", str(exc))

    def start_comfyui(self):
        directory = self.comfy_dir.get().strip()
        if not directory:
            directory = filedialog.askdirectory(title="Select your ComfyUI directory")
            if not directory:
                return
            self.comfy_dir.set(directory)

        path = Path(directory)
        main_py = path / "main.py"
        if not main_py.exists():
            messagebox.showerror("ComfyUI not found", f"main.py was not found in:\n{directory}")
            return

        python = path / ".venv" / "Scripts" / "python.exe"
        if not python.exists():
            python = path / "python_embeded" / "python.exe"
        if not python.exists():
            python = Path(sys.executable)

        try:
            subprocess.Popen(
                [str(python), str(main_py), "--listen", "127.0.0.1", "--port", "8188"],
                cwd=str(path),
            )
            self.log("Starting local ComfyUI...")
        except Exception as exc:
            messagebox.showerror("Could not start ComfyUI", str(exc))

    def open_output(self):
        directory = Path(self.output_dir.get())
        directory.mkdir(parents=True, exist_ok=True)
        os.startfile(str(directory))

    def generate(self):
        image_path = self.image_path.get().strip()
        if not image_path or not Path(image_path).is_file():
            messagebox.showwarning("Missing image", "Choose a starting image first.")
            return

        prompt_text = self.prompt.get("1.0", "end").strip()
        if not prompt_text:
            messagebox.showwarning("Missing prompt", "Enter a motion prompt.")
            return

        try:
            seed = int(self.seed.get())
        except tk.TclError:
            messagebox.showwarning("Invalid seed", "Seed must be an integer.")
            return

        self.generate_button.configure(state="disabled")
        self.progress.start(10)
        threading.Thread(
            target=self._generate_worker,
            args=(image_path, prompt_text, seed),
            daemon=True,
        ).start()

    def _generate_worker(self, image_path, prompt_text, seed):
        base_url = self.comfy_url.get().strip().rstrip("/")
        try:
            self.log("Checking ComfyUI...")
            requests.get(base_url + "/", timeout=5).raise_for_status()

            self.log("Uploading starting image...")
            with open(image_path, "rb") as image_file:
                upload = requests.post(
                    base_url + "/upload/image",
                    files={"image": (Path(image_path).name, image_file)},
                    data={"overwrite": "true", "subfolder": ""},
                    timeout=60,
                )
            upload.raise_for_status()
            uploaded_name = upload.json()["name"]

            with DEFAULT_PACK.open("r", encoding="utf-8") as pack_file:
                workflow = copy.deepcopy(json.load(pack_file)["workflow"])

            workflow["6"]["inputs"]["text"] = prompt_text
            workflow["30"]["inputs"]["noise_seed"] = seed
            workflow["31"]["inputs"]["noise_seed"] = seed
            workflow["14"]["inputs"]["image"] = uploaded_name

            sizes = {"Landscape": (832, 480), "Portrait": (480, 832), "Square": (624, 624)}
            width, height = sizes[self.size_name.get()]
            workflow["55"]["inputs"]["width"] = width
            workflow["55"]["inputs"]["height"] = height

            self.log("Submitting generation...")
            response = requests.post(
                base_url + "/prompt",
                json={"prompt": workflow, "client_id": "wan22-desktop"},
                timeout=60,
            )
            response.raise_for_status()
            payload = response.json()
            if "error" in payload:
                raise RuntimeError(json.dumps(payload["error"], indent=2))

            prompt_id = payload["prompt_id"]
            self.prompt_id = prompt_id
            self.log(f"Prompt ID: {prompt_id}")
            self._wait_for_output(base_url, prompt_id)
        except Exception as exc:
            self.log("ERROR: " + str(exc))
            self.root.after(0, lambda: messagebox.showerror("Generation failed", str(exc)))
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.generate_button.configure(state="normal"))

    def _wait_for_output(self, base_url, prompt_id):
        while True:
            history = requests.get(base_url + "/history/" + prompt_id, timeout=30)
            history.raise_for_status()
            record = history.json().get(prompt_id)
            if record and record.get("outputs"):
                output_files = []
                for node_output in record["outputs"].values():
                    for image_info in node_output.get("images", []) + node_output.get("gifs", []):
                        output_files.append(image_info)
                if output_files:
                    self._download_output(base_url, output_files[0])
                    return

            status = record.get("status", {}) if record else {}
            if status.get("status_str") == "error":
                raise RuntimeError(json.dumps(status, indent=2))
            self.log("Generating...")
            threading.Event().wait(1.2)

    def _download_output(self, base_url, file_info):
        params = urllib.parse.urlencode({
            "filename": file_info["filename"],
            "subfolder": file_info.get("subfolder", ""),
            "type": file_info.get("type", "output"),
        })
        response = requests.get(base_url + "/view?" + params, timeout=120)
        response.raise_for_status()

        output_dir = Path(self.output_dir.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / file_info["filename"]
        output_path.write_bytes(response.content)
        self.log("Saved: " + str(output_path))
        self.root.after(0, lambda: messagebox.showinfo("Video ready", str(output_path)))
        self.root.after(0, lambda: os.startfile(str(output_path)))


def main():
    root = tk.Tk()
    app = WanDesktopApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
