import threading
import tkinter as tk
from tkinter import filedialog, messagebox

# Import the backend logic
from comic_gen_backend import generate_comic


class ComicGenApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Graphic Novel Generator - Prototype 1")
        self.root.geometry("500x350")
        self.root.resizable(False, False)

        # Variables to store paths
        self.story_path = tk.StringVar()
        self.output_dir = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        padding = {"padx": 10, "pady": 10}

        # --- Story File Selection ---
        tk.Label(self.root, text="1. Select Story Document:").grid(
            row=0, column=0, sticky="w", **padding
        )
        self.btn_select_story = tk.Button(
            self.root, text="Browse File", command=self.browse_story
        )
        self.btn_select_story.grid(row=0, column=1, sticky="w", **padding)

        self.lbl_story = tk.Label(
            self.root,
            textvariable=self.story_path,
            fg="gray",
            wraplength=300,
            justify="left",
        )
        self.lbl_story.grid(
            row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10)
        )

        # --- Output Directory Selection ---
        tk.Label(self.root, text="2. Select Output Folder:").grid(
            row=2, column=0, sticky="w", **padding
        )
        self.btn_select_dir = tk.Button(
            self.root, text="Browse Folder", command=self.browse_folder
        )
        self.btn_select_dir.grid(row=2, column=1, sticky="w", **padding)

        self.lbl_dir = tk.Label(
            self.root,
            textvariable=self.output_dir,
            fg="gray",
            wraplength=300,
            justify="left",
        )
        self.lbl_dir.grid(
            row=3, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10)
        )

        # --- Project Name Input ---
        tk.Label(self.root, text="3. Project Name:").grid(
            row=4, column=0, sticky="w", **padding
        )
        self.entry_name = tk.Entry(self.root, width=30)
        self.entry_name.grid(row=4, column=1, sticky="w", **padding)

        # --- Generate Button ---
        self.btn_generate = tk.Button(
            self.root,
            text="Generate Graphic Novel",
            command=self.start_generation,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.btn_generate.grid(row=5, column=0, columnspan=2, pady=20)

        # --- Status Label ---
        self.lbl_status = tk.Label(
            self.root, text="Ready", fg="blue", font=("Arial", 10, "italic")
        )
        self.lbl_status.grid(row=6, column=0, columnspan=2)

    def browse_story(self):
        path = filedialog.askopenfilename(
            title="Select Story", filetypes=[("Documents", "*.pdf *.docx *.txt")]
        )
        if path:
            self.story_path.set(path)

    def browse_folder(self):
        path = filedialog.askdirectory(title="Select Output Folder")
        if path:
            self.output_dir.set(path)

    def start_generation(self):
        story = self.story_path.get()
        folder = self.output_dir.get()
        name = self.entry_name.get().strip()

        if not story:
            messagebox.showerror("Error", "Please select a story document.")
            return
        if not folder:
            messagebox.showerror("Error", "Please select an output folder.")
            return
        if not name:
            messagebox.showerror("Error", "Please enter a project name.")
            return

        # Disable UI during generation
        self.btn_generate.config(state=tk.DISABLED)
        self.lbl_status.config(
            text="Status: Generating... (This may take a while)", fg="orange"
        )

        # Run in a separate thread so UI doesn't freeze
        threading.Thread(
            target=self.run_backend, args=(story, folder, name), daemon=True
        ).start()

    def run_backend(self, story, folder, name):
        try:
            generate_comic(story, folder, name)
            self.root.after(0, self.on_generation_complete)
        except Exception as e:
            self.root.after(0, self.on_generation_error, str(e))

    def on_generation_complete(self):
        self.lbl_status.config(text="Status: Complete!", fg="green")
        self.btn_generate.config(state=tk.NORMAL)
        messagebox.showinfo("Success", "Graphic Novel generated successfully!")

    def on_generation_error(self, error_msg):
        self.lbl_status.config(text="Status: Error occurred", fg="red")
        self.btn_generate.config(state=tk.NORMAL)
        messagebox.showerror("Generation Error", f"An error occurred:\n{error_msg}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ComicGenApp(root)
    root.mainloop()
