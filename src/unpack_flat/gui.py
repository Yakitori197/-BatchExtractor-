"""
unpack-flat 圖形介面應用程式（繁體中文版）
"""

import os
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from rich.console import Console


class UnpackFlatGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("批次壓縮檔工具 - YoLab工作室")
        self.root.geometry("620x550")
        self.root.resizable(False, False)

        # 視窗置中
        self.center_window()

        # 變數
        self.mode = tk.StringVar(value="A")
        self.selected_path = tk.StringVar(value="")
        # filedialog 回傳的是字串路徑（消費端才轉成 Path）
        self.selected_files: list[str] = []
        self.is_running = False

        # 尋找 7z
        self.seven_zip = self.find_7z()

        # 建立介面
        self.create_widgets()

        # 檢查 7z
        if not self.seven_zip:
            self.log("⚠ 警告：找不到 7-Zip！")
            self.log("請從 https://7-zip.org 下載安裝")
            self.log("")
        else:
            self.log(f"✓ 已找到 7-Zip：{self.seven_zip}")
            self.log("✓ 準備就緒！")
            self.log("")

    def center_window(self) -> None:
        self.root.update_idletasks()
        width = 620
        height = 550
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def find_7z(self) -> str | None:
        """尋找 7z 執行檔"""
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

    def create_widgets(self) -> None:
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 標題
        title_label = ttk.Label(
            main_frame,
            text="批次壓縮檔工具",
            font=("Microsoft JhengHei UI", 18, "bold")
        )
        title_label.pack(pady=(0, 15))

        # 模式選擇框架
        mode_frame = ttk.LabelFrame(main_frame, text="選擇模式", padding="15")
        mode_frame.pack(fill=tk.X, pady=(0, 15))

        # 模式 A
        mode_a_frame = ttk.Frame(mode_frame)
        mode_a_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(
            mode_a_frame,
            text="模式 A：解壓並整合",
            variable=self.mode,
            value="A",
            command=self.on_mode_change
        ).pack(side=tk.LEFT)

        ttk.Label(
            mode_a_frame,
            text="（選擇資料夾 → 所有檔案合併輸出）",
            foreground="gray"
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 模式 B
        mode_b_frame = ttk.Frame(mode_frame)
        mode_b_frame.pack(fill=tk.X, pady=5)

        ttk.Radiobutton(
            mode_b_frame,
            text="模式 B：解壓並分檔",
            variable=self.mode,
            value="B",
            command=self.on_mode_change
        ).pack(side=tk.LEFT)

        ttk.Label(
            mode_b_frame,
            text="（選擇多個檔案 → 各自輸出到獨立資料夾）",
            foreground="gray"
        ).pack(side=tk.LEFT, padx=(10, 0))

        # 選擇框架
        select_frame = ttk.LabelFrame(main_frame, text="選擇來源", padding="15")
        select_frame.pack(fill=tk.X, pady=(0, 15))

        # 路徑顯示
        path_frame = ttk.Frame(select_frame)
        path_frame.pack(fill=tk.X, pady=(0, 10))

        self.path_entry = ttk.Entry(
            path_frame,
            textvariable=self.selected_path,
            state="readonly",
            width=50
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.browse_btn = ttk.Button(
            path_frame,
            text="瀏覽...",
            command=self.browse,
            width=12
        )
        self.browse_btn.pack(side=tk.RIGHT, padx=(10, 0))

        # 檔案數量標籤（模式 B 用）
        self.file_count_label = ttk.Label(select_frame, text="")
        self.file_count_label.pack(anchor=tk.W)

        # 開始按鈕
        self.start_btn = ttk.Button(
            main_frame,
            text="開始解壓縮",
            command=self.start_extraction,
            width=20
        )
        self.start_btn.pack(pady=(0, 15))

        # 日誌框架
        log_frame = ttk.LabelFrame(main_frame, text="執行記錄", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        # 日誌文字區域與捲軸
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_frame,
            height=10,
            wrap=tk.WORD,
            yscrollcommand=log_scroll.set,
            state=tk.DISABLED,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)

        # 進度條
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.pack(fill=tk.X, pady=(10, 0))

        # YoLab 工作室標示（右下角）- 使用 place 絕對定位
        credit_label = tk.Label(
            self.root,
            text="YoLab工作室設計",
            font=("Microsoft JhengHei UI", 8),
            fg="gray"
        )
        credit_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-5)

    def on_mode_change(self) -> None:
        """模式變更時重置選擇"""
        self.selected_path.set("")
        self.selected_files = []
        self.file_count_label.config(text="")

    def browse(self) -> None:
        """根據模式開啟檔案/資料夾瀏覽器"""
        if self.mode.get() == "A":
            # 模式 A：選擇資料夾
            folder = filedialog.askdirectory(
                title="選擇包含壓縮檔的資料夾"
            )
            if folder:
                self.selected_path.set(folder)
                self.selected_files = []
                self.file_count_label.config(text="")
        else:
            # 模式 B：選擇多個檔案
            files = filedialog.askopenfilenames(
                title="選擇壓縮檔（按住 Ctrl 可多選）",
                filetypes=[
                    ("壓縮檔", "*.zip *.7z *.rar *.tar *.gz *.bz2 *.xz *.tgz *.tbz2"),
                    ("ZIP 檔案", "*.zip"),
                    ("7z 檔案", "*.7z"),
                    ("RAR 檔案", "*.rar"),
                    ("所有檔案", "*.*"),
                ]
            )
            if files:
                self.selected_files = list(files)
                self.selected_path.set(f"已選擇 {len(files)} 個檔案")
                self.file_count_label.config(
                    text=f"檔案：{', '.join(Path(f).name for f in files[:3])}{'...' if len(files) > 3 else ''}"
                )

    def log(self, message: str) -> None:
        """新增訊息到日誌"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()

    def clear_log(self) -> None:
        """清除日誌"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def set_running(self, running: bool) -> None:
        """設定執行狀態"""
        self.is_running = running
        state = "disabled" if running else "normal"
        self.start_btn.config(state=state)
        self.browse_btn.config(state=state)

        if running:
            self.progress.start(10)
        else:
            self.progress.stop()

    def start_extraction(self) -> None:
        """在背景執行緒開始解壓縮"""
        if not self.seven_zip:
            messagebox.showerror(
                "錯誤",
                "找不到 7-Zip！\n\n請從 https://7-zip.org 下載安裝"
            )
            return

        if self.mode.get() == "A":
            if not self.selected_path.get():
                messagebox.showwarning("提示", "請先選擇資料夾！")
                return
            thread = threading.Thread(target=self.run_mode_a, daemon=True)
        else:
            if not self.selected_files:
                messagebox.showwarning("提示", "請先選擇壓縮檔！")
                return
            thread = threading.Thread(target=self.run_mode_b, daemon=True)

        self.clear_log()
        self.set_running(True)
        thread.start()

    def run_mode_a(self) -> None:
        """執行模式 A 解壓縮"""
        try:
            input_folder = Path(self.selected_path.get())
            output_folder = input_folder.parent / f"{input_folder.name}_extracted"

            self.log("=" * 45)
            self.log("  模式 A：解壓並整合")
            self.log("=" * 45)
            self.log(f"輸入：{input_folder}")
            self.log(f"輸出：{output_folder}")
            self.log("")

            # 使用 unpack_flat CLI
            self.log("開始解壓縮...")
            self.log("")

            try:
                from unpack_flat.extractor import UnpackFlat

                # 建立簡單的 console 輸出到 GUI
                class GUIConsole:
                    # log 函式由建構子注入。原本是先建立實例、再從外部
                    # 掛上 gui_log 屬性（猴子補丁），型別檢查無從得知該屬性存在。
                    def __init__(self, log_fn: Callable[[str], None]) -> None:
                        self.gui_log = log_fn

                    def print(self, *args: Any, **kwargs: Any) -> None:
                        text = " ".join(str(a) for a in args)
                        import re
                        text = re.sub(r'\[.*?\]', '', text)
                        self.gui_log(text)

                    def is_terminal(self) -> bool:
                        return False

                gui_console = GUIConsole(self.log)

                extractor = UnpackFlat(
                    input_dir=input_folder,
                    output_dir=output_folder,
                    max_rounds=50,
                    keep_archives=False,
                    dry_run=False,
                    workers=4,
                    compute_hash=True,
                    # GUIConsole 是刻意的 duck-typing 替身，只實作 UnpackFlat
                    # 用到的 print/is_terminal 子集，並非真正的 rich Console。
                    console=cast("Console", gui_console)
                )

                stats = extractor.run()

                self.log("")
                self.log("=" * 45)
                self.log(f"  解壓檔案數：{stats.files_output}")
                self.log(f"  重新命名數：{stats.files_renamed}")
                self.log(f"  錯誤數量：  {stats.errors}")
                self.log("=" * 45)

            except Exception as e:
                self.log(f"錯誤：{e}")
                self.log("使用備用方式解壓...")
                self.extract_folder_flat(input_folder, output_folder)

            self.log("")
            self.log("✓ 完成！")

            # 開啟輸出資料夾
            self.root.after(0, lambda: self.open_folder(output_folder))

        except Exception as e:
            self.log(f"錯誤：{e}")
        finally:
            self.root.after(0, lambda: self.set_running(False))

    def extract_folder_flat(self, input_folder: Path, output_folder: Path) -> None:
        """備用方式：解壓所有壓縮檔到平坦資料夾"""
        # find_7z() 可能回傳 None（未安裝 7-Zip）。原本直接把它塞進 subprocess，
        # 沒裝 7-Zip 時會在執行期爆掉，這裡明確擋下並告知使用者。
        seven_zip = self.seven_zip
        if not seven_zip:
            self.log("✗ 找不到 7-Zip，無法解壓縮。請先安裝 7-Zip。")
            return

        output_folder.mkdir(parents=True, exist_ok=True)

        archive_exts = {'.zip', '.7z', '.rar', '.tar', '.gz', '.bz2', '.xz', '.tgz', '.tbz2'}
        archives = [f for f in input_folder.rglob('*') if f.suffix.lower() in archive_exts]

        for i, arc in enumerate(archives, 1):
            self.log(f"[{i}/{len(archives)}] {arc.name}")
            result = subprocess.run(
                [seven_zip, "x", str(arc), f"-o{output_folder}", "-y"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                self.log("       ✓ 成功")
            else:
                self.log("       ✗ 失敗")

    def run_mode_b(self) -> None:
        """執行模式 B 解壓縮"""
        # 同 extract_folder_flat：未安裝 7-Zip 時明確擋下，不要把 None 丟給 subprocess
        seven_zip = self.seven_zip
        if not seven_zip:
            self.log("✗ 找不到 7-Zip，無法解壓縮。請先安裝 7-Zip。")
            self.root.after(0, lambda: self.set_running(False))
            return

        try:
            files = self.selected_files

            # 決定輸出資料夾
            first_file = Path(files[0])
            parent_folder = first_file.parent
            output_base = parent_folder.parent / f"{parent_folder.name}_extracted"
            output_base.mkdir(parents=True, exist_ok=True)

            self.log("=" * 45)
            self.log("  模式 B：解壓並分檔")
            self.log("=" * 45)
            self.log(f"輸出位置：{output_base}")
            self.log(f"檔案數量：{len(files)}")
            self.log("")

            success_count = 0
            fail_count = 0

            for i, selected in enumerate(files, 1):
                # selected 是字串路徑；用另一個變數存 Path，不要覆寫原變數的型別
                file_path = Path(selected)

                # 取得不含副檔名的名稱
                name = file_path.stem
                if name.endswith('.tar'):
                    name = name[:-4]

                output_dir = output_base / name
                output_dir.mkdir(parents=True, exist_ok=True)

                self.log(f"[{i}/{len(files)}] {file_path.name}")
                self.log(f"       → {name}/")

                result = subprocess.run(
                    [seven_zip, "x", str(file_path), f"-o{output_dir}", "-y"],
                    capture_output=True,
                    text=True,
                    timeout=3600
                )

                if result.returncode == 0:
                    self.log("       ✓ 成功")
                    success_count += 1
                else:
                    self.log("       ✗ 失敗")
                    fail_count += 1

                self.log("")

            self.log("=" * 45)
            self.log(f"  完成：{success_count} 個成功，{fail_count} 個失敗")
            self.log("=" * 45)
            self.log("")
            self.log("✓ 完成！")

            # 開啟輸出資料夾
            self.root.after(0, lambda: self.open_folder(output_base))

        except Exception as e:
            self.log(f"錯誤：{e}")
        finally:
            self.root.after(0, lambda: self.set_running(False))

    def open_folder(self, folder: Path) -> None:
        """在檔案總管開啟資料夾"""
        if sys.platform == "win32":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder)])
        else:
            subprocess.run(["xdg-open", str(folder)])


def main() -> None:
    root = tk.Tk()
    UnpackFlatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
