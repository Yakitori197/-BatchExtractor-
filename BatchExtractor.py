"""
批次壓縮檔工具 - YoLab工作室設計
Standalone version for PyInstaller packaging
"""

import os
import sys
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


# Language strings
LANG = {
    "zh-TW": {
        "title": "批次壓縮檔工具",
        "window_title": "批次壓縮檔工具 - YoLab工作室",
        "mode_frame": "選擇模式",
        "mode_a": "模式 A：解壓並整合",
        "mode_a_desc": "（選擇資料夾 → 資料夾內部所有壓縮檔解壓並合併輸出至指定位置）",
        "mode_b": "模式 B：解壓並分檔",
        "mode_b_desc": "（選擇多個檔案 → 選擇指定位置後各自輸出到獨立資料夾）",
        "input_frame": "輸入來源",
        "output_frame": "輸出位置",
        "browse": "瀏覽...",
        "start": "開始解壓縮",
        "log_frame": "執行記錄",
        "credit": "YoLab工作室設計",
        "warning_no_7zip": "⚠ 警告：找不到 7-Zip！",
        "warning_install": "請從 https://7-zip.org 下載安裝",
        "ready": "✓ 準備就緒！",
        "found_7zip": "✓ 已找到 7-Zip：",
        "error": "錯誤",
        "hint": "提示",
        "error_no_7zip": "找不到 7-Zip！\n\n請從 https://7-zip.org 下載安裝",
        "error_no_input": "請先選擇輸入資料夾！",
        "error_no_files": "請先選擇壓縮檔！",
        "error_no_output": "請先選擇輸出位置！",
        "select_folder": "選擇包含壓縮檔的資料夾",
        "select_files": "選擇壓縮檔（按住 Ctrl 可多選）",
        "select_output": "選擇輸出位置",
        "archives": "壓縮檔",
        "zip_files": "ZIP 檔案",
        "7z_files": "7z 檔案",
        "rar_files": "RAR 檔案",
        "all_files": "所有檔案",
        "files_selected": "已選擇 {0} 個檔案",
        "files_label": "檔案：",
        "mode_a_title": "  模式 A：解壓並整合",
        "mode_b_title": "  模式 B：解壓並分檔",
        "input_label": "輸入：",
        "output_label": "輸出：",
        "output_location": "輸出位置：",
        "file_count": "檔案數量：",
        "found_archives": "找到 {0} 個壓縮檔",
        "round_nested": "--- 第 {0} 輪：發現 {1} 個巢狀壓縮檔 ---",
        "extracting": "  解壓：",
        "success": "       ✓ 成功",
        "failed": "       ✗ 失敗",
        "complete": "  完成：{0} 個成功，{1} 個失敗",
        "done": "✓ 完成！",
        "error_prefix": "錯誤：",
    },
    "en": {
        "title": "Batch Extractor",
        "window_title": "Batch Extractor - YoLab Studio",
        "mode_frame": "Select Mode",
        "mode_a": "Mode A: Extract & Merge",
        "mode_a_desc": "(Select folder → Extract all archives to single output)",
        "mode_b": "Mode B: Extract & Separate",
        "mode_b_desc": "(Select files → Extract each to its own folder)",
        "input_frame": "Input Source",
        "output_frame": "Output Location",
        "browse": "Browse...",
        "start": "Start Extraction",
        "log_frame": "Log",
        "credit": "Designed by YoLab Studio",
        "warning_no_7zip": "⚠ Warning: 7-Zip not found!",
        "warning_install": "Please download from https://7-zip.org",
        "ready": "✓ Ready!",
        "found_7zip": "✓ Found 7-Zip: ",
        "error": "Error",
        "hint": "Hint",
        "error_no_7zip": "7-Zip not found!\n\nPlease download from https://7-zip.org",
        "error_no_input": "Please select input folder first!",
        "error_no_files": "Please select archive files first!",
        "error_no_output": "Please select output location first!",
        "select_folder": "Select folder containing archives",
        "select_files": "Select archives (Ctrl+Click for multiple)",
        "select_output": "Select output location",
        "archives": "Archives",
        "zip_files": "ZIP files",
        "7z_files": "7z files",
        "rar_files": "RAR files",
        "all_files": "All files",
        "files_selected": "{0} files selected",
        "files_label": "Files: ",
        "mode_a_title": "  Mode A: Extract & Merge",
        "mode_b_title": "  Mode B: Extract & Separate",
        "input_label": "Input: ",
        "output_label": "Output: ",
        "output_location": "Output: ",
        "file_count": "File count: ",
        "found_archives": "Found {0} archives",
        "round_nested": "--- Round {0}: Found {1} nested archives ---",
        "extracting": "  Extracting: ",
        "success": "       ✓ Success",
        "failed": "       ✗ Failed",
        "complete": "  Complete: {0} success, {1} failed",
        "done": "✓ Done!",
        "error_prefix": "Error: ",
    }
}


class BatchExtractorGUI:
    def __init__(self, root):
        self.root = root
        self.current_lang = "zh-TW"
        self.lang = LANG[self.current_lang]
        
        self.root.title(self.lang["window_title"])
        self.root.geometry("750x720")
        self.root.resizable(False, False)
        
        # Center window
        self.center_window()
        
        # Variables
        self.mode = tk.StringVar(value="A")
        self.selected_path = tk.StringVar(value="")
        self.output_path = tk.StringVar(value="")
        self.language_var = tk.StringVar(value="繁體中文")
        self.selected_files = []
        self.is_running = False
        
        # Find 7z
        self.seven_zip = self.find_7z()
        
        # Create UI
        self.create_widgets()
        
        # Check 7z
        if not self.seven_zip:
            self.log(self.lang["warning_no_7zip"])
            self.log(self.lang["warning_install"])
            self.log("")
        else:
            self.log(f"{self.lang['found_7zip']}{self.seven_zip}")
            self.log(self.lang["ready"])
            self.log("")
    
    def center_window(self):
        self.root.update_idletasks()
        width = 750
        height = 720
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def find_7z(self):
        """Find 7z executable"""
        path = shutil.which("7z")
        if path:
            return path
        
        locations = [
            r"C:\Program Files\7-Zip\7z.exe",
            r"C:\Program Files (x86)\7-Zip\7z.exe",
        ]
        for loc in locations:
            if Path(loc).exists():
                return loc
        return None
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top bar: Title (left/center) + Language selector (right)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Empty label for spacing on left
        ttk.Label(top_frame, text="", width=15).pack(side=tk.LEFT)
        
        # Title (center)
        self.title_label = ttk.Label(
            top_frame, 
            text=self.lang["title"], 
            font=("Microsoft JhengHei UI", 22, "bold")
        )
        self.title_label.pack(side=tk.LEFT, expand=True)
        
        # Language selector (right)
        self.lang_combo = ttk.Combobox(
            top_frame,
            textvariable=self.language_var,
            values=["繁體中文", "English"],
            state="readonly",
            width=12,
            font=("Microsoft JhengHei UI", 10)
        )
        self.lang_combo.pack(side=tk.RIGHT)
        self.lang_combo.bind("<<ComboboxSelected>>", self.on_language_change)
        
        # Mode selection frame
        self.mode_frame = ttk.LabelFrame(main_frame, text=self.lang["mode_frame"], padding="15")
        self.mode_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Mode A
        mode_a_frame = ttk.Frame(self.mode_frame)
        mode_a_frame.pack(fill=tk.X, pady=8)
        
        self.mode_a_radio = ttk.Radiobutton(
            mode_a_frame,
            text=self.lang["mode_a"],
            variable=self.mode,
            value="A",
            command=self.on_mode_change
        )
        self.mode_a_radio.pack(side=tk.LEFT)
        
        self.mode_a_desc = ttk.Label(
            mode_a_frame,
            text=self.lang["mode_a_desc"],
            foreground="gray"
        )
        self.mode_a_desc.pack(side=tk.LEFT, padx=(10, 0))
        
        # Mode B
        mode_b_frame = ttk.Frame(self.mode_frame)
        mode_b_frame.pack(fill=tk.X, pady=8)
        
        self.mode_b_radio = ttk.Radiobutton(
            mode_b_frame,
            text=self.lang["mode_b"],
            variable=self.mode,
            value="B",
            command=self.on_mode_change
        )
        self.mode_b_radio.pack(side=tk.LEFT)
        
        self.mode_b_desc = ttk.Label(
            mode_b_frame,
            text=self.lang["mode_b_desc"],
            foreground="gray"
        )
        self.mode_b_desc.pack(side=tk.LEFT, padx=(10, 0))
        
        # === Input Selection frame ===
        self.input_frame = ttk.LabelFrame(main_frame, text=self.lang["input_frame"], padding="15")
        self.input_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Input path display
        input_path_frame = ttk.Frame(self.input_frame)
        input_path_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.path_entry = ttk.Entry(
            input_path_frame,
            textvariable=self.selected_path,
            state="readonly",
            width=60,
            font=("Microsoft JhengHei UI", 10)
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_btn = ttk.Button(
            input_path_frame,
            text=self.lang["browse"],
            command=self.browse_input,
            width=12
        )
        self.browse_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # File count label (for Mode B)
        self.file_count_label = ttk.Label(self.input_frame, text="")
        self.file_count_label.pack(anchor=tk.W)
        
        # === Output Selection frame ===
        self.output_frame_widget = ttk.LabelFrame(main_frame, text=self.lang["output_frame"], padding="15")
        self.output_frame_widget.pack(fill=tk.X, pady=(0, 15))
        
        # Output path display
        output_path_frame = ttk.Frame(self.output_frame_widget)
        output_path_frame.pack(fill=tk.X)
        
        self.output_entry = ttk.Entry(
            output_path_frame,
            textvariable=self.output_path,
            state="readonly",
            width=60,
            font=("Microsoft JhengHei UI", 10)
        )
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_output_btn = ttk.Button(
            output_path_frame,
            text=self.lang["browse"],
            command=self.browse_output,
            width=12
        )
        self.browse_output_btn.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Start button
        self.start_btn = ttk.Button(
            main_frame,
            text=self.lang["start"],
            command=self.start_extraction,
            width=25
        )
        self.start_btn.pack(pady=(5, 15))
        
        # Log frame (includes progress bar now)
        self.log_frame = ttk.LabelFrame(main_frame, text=self.lang["log_frame"], padding="10")
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text with scrollbar
        log_container = ttk.Frame(self.log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        log_scroll = ttk.Scrollbar(log_container)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(
            log_container,
            height=10,
            wrap=tk.WORD,
            yscrollcommand=log_scroll.set,
            state=tk.DISABLED,
            font=("Consolas", 10)
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Progress bar (inside log frame, at bottom)
        self.progress = ttk.Progressbar(self.log_frame, mode="indeterminate", length=400)
        self.progress.pack(fill=tk.X, pady=(10, 5))
        
        # Credit at bottom right (using place for absolute positioning)
        self.credit_label = tk.Label(
            self.root,
            text=self.lang["credit"],
            font=("Microsoft JhengHei UI", 9),
            fg="gray"
        )
        self.credit_label.place(relx=1.0, rely=1.0, anchor="se", x=-15, y=-10)
    
    def on_language_change(self, event=None):
        """Change language"""
        selected = self.language_var.get()
        if selected == "繁體中文":
            self.current_lang = "zh-TW"
        else:
            self.current_lang = "en"
        
        self.lang = LANG[self.current_lang]
        self.update_ui_language()
    
    def update_ui_language(self):
        """Update all UI elements with new language"""
        self.root.title(self.lang["window_title"])
        self.title_label.config(text=self.lang["title"])
        self.mode_frame.config(text=self.lang["mode_frame"])
        self.mode_a_radio.config(text=self.lang["mode_a"])
        self.mode_a_desc.config(text=self.lang["mode_a_desc"])
        self.mode_b_radio.config(text=self.lang["mode_b"])
        self.mode_b_desc.config(text=self.lang["mode_b_desc"])
        self.input_frame.config(text=self.lang["input_frame"])
        self.output_frame_widget.config(text=self.lang["output_frame"])
        self.browse_btn.config(text=self.lang["browse"])
        self.browse_output_btn.config(text=self.lang["browse"])
        self.start_btn.config(text=self.lang["start"])
        self.log_frame.config(text=self.lang["log_frame"])
        self.credit_label.config(text=self.lang["credit"])
    
    def on_mode_change(self):
        """Reset selection when mode changes"""
        self.selected_path.set("")
        self.output_path.set("")
        self.selected_files = []
        self.file_count_label.config(text="")
    
    def browse_input(self):
        """Open file/folder browser based on mode"""
        if self.mode.get() == "A":
            folder = filedialog.askdirectory(
                title=self.lang["select_folder"]
            )
            if folder:
                self.selected_path.set(folder)
                self.selected_files = []
                self.file_count_label.config(text="")
                # Auto-suggest output path
                if not self.output_path.get():
                    self.output_path.set(folder + "_extracted")
        else:
            files = filedialog.askopenfilenames(
                title=self.lang["select_files"],
                filetypes=[
                    (self.lang["archives"], "*.zip *.7z *.rar *.tar *.gz *.bz2 *.xz *.tgz *.tbz2"),
                    (self.lang["zip_files"], "*.zip"),
                    (self.lang["7z_files"], "*.7z"),
                    (self.lang["rar_files"], "*.rar"),
                    (self.lang["all_files"], "*.*"),
                ]
            )
            if files:
                self.selected_files = list(files)
                self.selected_path.set(self.lang["files_selected"].format(len(files)))
                self.file_count_label.config(
                    text=f"{self.lang['files_label']}{', '.join(Path(f).name for f in files[:3])}{'...' if len(files) > 3 else ''}"
                )
                # Auto-suggest output path
                if not self.output_path.get():
                    first_file = Path(files[0])
                    parent_folder = first_file.parent
                    self.output_path.set(str(parent_folder / "extracted"))
    
    def browse_output(self):
        """Open folder browser for output location"""
        folder = filedialog.askdirectory(
            title=self.lang["select_output"]
        )
        if folder:
            self.output_path.set(folder)
    
    def log(self, message):
        """Add message to log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def set_running(self, running):
        """Set running state"""
        self.is_running = running
        state = "disabled" if running else "normal"
        self.start_btn.config(state=state)
        self.browse_btn.config(state=state)
        self.browse_output_btn.config(state=state)
        self.lang_combo.config(state="disabled" if running else "readonly")
        
        if running:
            self.progress.start(10)
        else:
            self.progress.stop()
    
    def start_extraction(self):
        """Start extraction in background thread"""
        if not self.seven_zip:
            messagebox.showerror(
                self.lang["error"],
                self.lang["error_no_7zip"]
            )
            return
        
        # Check input
        if self.mode.get() == "A":
            if not self.selected_path.get():
                messagebox.showwarning(self.lang["hint"], self.lang["error_no_input"])
                return
        else:
            if not self.selected_files:
                messagebox.showwarning(self.lang["hint"], self.lang["error_no_files"])
                return
        
        # Check output
        if not self.output_path.get():
            messagebox.showwarning(self.lang["hint"], self.lang["error_no_output"])
            return
        
        if self.mode.get() == "A":
            thread = threading.Thread(target=self.run_mode_a, daemon=True)
        else:
            thread = threading.Thread(target=self.run_mode_b, daemon=True)
        
        self.clear_log()
        self.set_running(True)
        thread.start()
    
    def run_mode_a(self):
        """Run Mode A extraction"""
        try:
            input_folder = Path(self.selected_path.get())
            output_folder = Path(self.output_path.get())
            
            self.log("=" * 50)
            self.log(self.lang["mode_a_title"])
            self.log("=" * 50)
            self.log(f"{self.lang['input_label']}{input_folder}")
            self.log(f"{self.lang['output_label']}{output_folder}")
            self.log("")
            
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Find all archives
            archive_exts = {'.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2'}
            archives = []
            for f in input_folder.rglob('*'):
                if f.is_file() and f.suffix.lower() in archive_exts:
                    archives.append(f)
            
            self.log(self.lang["found_archives"].format(len(archives)))
            self.log("")
            
            success_count = 0
            fail_count = 0
            
            for i, arc in enumerate(archives, 1):
                self.log(f"[{i}/{len(archives)}] {arc.name}")
                
                result = subprocess.run(
                    [self.seven_zip, "x", str(arc), f"-o{output_folder}", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=3600
                )
                
                if result.returncode == 0:
                    self.log(self.lang["success"])
                    success_count += 1
                else:
                    self.log(self.lang["failed"])
                    fail_count += 1
                
                self.log("")
            
            # Handle nested archives
            max_rounds = 10
            for round_num in range(2, max_rounds + 1):
                nested = []
                for f in output_folder.rglob('*'):
                    if f.is_file() and f.suffix.lower() in archive_exts:
                        nested.append(f)
                
                if not nested:
                    break
                
                self.log(self.lang["round_nested"].format(round_num, len(nested)))
                self.log("")
                
                for arc in nested:
                    self.log(f"{self.lang['extracting']}{arc.name}")
                    result = subprocess.run(
                        [self.seven_zip, "x", str(arc), f"-o{output_folder}", "-y"],
                        capture_output=True,
                        text=True,
                        timeout=3600
                    )
                    if result.returncode == 0:
                        success_count += 1
                        # Delete nested archive after extraction
                        try:
                            arc.unlink()
                        except:
                            pass
                    else:
                        fail_count += 1
                
                self.log("")
            
            self.log("=" * 50)
            self.log(self.lang["complete"].format(success_count, fail_count))
            self.log("=" * 50)
            self.log("")
            self.log(self.lang["done"])
            
            self.root.after(0, lambda: self.open_folder(output_folder))
            
        except Exception as e:
            self.log(f"{self.lang['error_prefix']}{e}")
        finally:
            self.root.after(0, lambda: self.set_running(False))
    
    def run_mode_b(self):
        """Run Mode B extraction"""
        try:
            files = self.selected_files
            output_base = Path(self.output_path.get())
            output_base.mkdir(parents=True, exist_ok=True)
            
            self.log("=" * 50)
            self.log(self.lang["mode_b_title"])
            self.log("=" * 50)
            self.log(f"{self.lang['output_location']}{output_base}")
            self.log(f"{self.lang['file_count']}{len(files)}")
            self.log("")
            
            success_count = 0
            fail_count = 0
            
            for i, file_path in enumerate(files, 1):
                file_path = Path(file_path)
                
                name = file_path.stem
                if name.endswith('.tar'):
                    name = name[:-4]
                
                output_dir = output_base / name
                output_dir.mkdir(parents=True, exist_ok=True)
                
                self.log(f"[{i}/{len(files)}] {file_path.name}")
                self.log(f"       → {name}/")
                
                result = subprocess.run(
                    [self.seven_zip, "x", str(file_path), f"-o{output_dir}", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=3600
                )
                
                if result.returncode == 0:
                    self.log(self.lang["success"])
                    success_count += 1
                else:
                    self.log(self.lang["failed"])
                    fail_count += 1
                
                self.log("")
            
            self.log("=" * 50)
            self.log(self.lang["complete"].format(success_count, fail_count))
            self.log("=" * 50)
            self.log("")
            self.log(self.lang["done"])
            
            self.root.after(0, lambda: self.open_folder(output_base))
            
        except Exception as e:
            self.log(f"{self.lang['error_prefix']}{e}")
        finally:
            self.root.after(0, lambda: self.set_running(False))
    
    def open_folder(self, folder):
        """Open folder in explorer"""
        if sys.platform == "win32":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder)])
        else:
            subprocess.run(["xdg-open", str(folder)])


def main():
    root = tk.Tk()
    app = BatchExtractorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
