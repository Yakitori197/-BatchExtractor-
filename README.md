# 批次壓縮檔工具 BatchExtractor

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

簡單好用的批次解壓縮工具，支援遞迴解壓巢狀壓縮檔。

---

## 功能特色

- **模式 A：解壓並整合** - 將所有壓縮檔內容解壓到單一資料夾
- **模式 B：解壓並分檔** - 每個壓縮檔解壓到各自獨立的資料夾
- **自訂輸出位置** - 可選擇任意資料夾作為輸出位置
- **多語言介面** - 支援繁體中文 / English 即時切換
- 支援 ZIP、7Z、RAR、TAR、GZ、BZ2、XZ 等格式
- 自動處理檔名衝突

---

## 下載與安裝

### 方式一：直接使用 EXE（推薦）

1. 到 [Releases](https://github.com/Yakitori197/-BatchExtractor-/releases) 下載 `壓縮檔工具.exe`
2. 確保電腦已安裝 [7-Zip](https://7-zip.org/)
3. 雙擊執行即可

### 方式二：從原始碼執行

需要 Python 3.9+ 環境：

```bash
git clone https://github.com/Yakitori197/-BatchExtractor-.git
cd -BatchExtractor-
pip install -e .
```

執行 `Debug.bat` 啟動程式。

### 方式三：自行打包 EXE

1. 確保已安裝 Python 3.9+
2. 執行 `Install.bat`
3. 等待打包完成，`壓縮檔工具.exe` 會出現在專案資料夾

---

## 使用方式

1. 執行 `壓縮檔工具.exe`（或 `Debug.bat`）
2. 右上角可切換語言（繁體中文 / English）
3. 選擇模式：
   - **模式 A**：選擇包含壓縮檔的資料夾
   - **模式 B**：選擇多個壓縮檔（Ctrl+點擊多選）
4. 選擇輸出位置（可自訂）
5. 點擊「開始解壓縮」
6. 完成後自動開啟輸出資料夾

---

## 介面預覽

```
┌──────────────────────────────────────────────────────────────┐
│                                              [繁體中文 ▼]    │
│                                                              │
│                     批次壓縮檔工具                            │
│                                                              │
│  ┌─ 選擇模式 ──────────────────────────────────────────────┐ │
│  │  ◉ 模式 A：解壓並整合（選擇資料夾 → 合併輸出）          │ │
│  │  ○ 模式 B：解壓並分檔（選擇多個檔案 → 各自輸出）        │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ 輸入來源 ──────────────────────────────────────────────┐ │
│  │  [____________________________________]    [瀏覽...]    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ 輸出位置 ──────────────────────────────────────────────┐ │
│  │  [____________________________________]    [瀏覽...]    │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                              │
│                      [開始解壓縮]                             │
│                                                              │
│  ┌─ 執行記錄 ──────────────────────────────────────────────┐ │
│  │  ✓ 已找到 7-Zip：C:\Program Files\7-Zip\7z.exe         │ │
│  │  ✓ 準備就緒！                                           │ │
│  └─────────────────────────────────────────────────────────┘ │
│  [════════════════════ 進度條 ════════════════════════════]  │
│                                              YoLab工作室設計 │
└──────────────────────────────────────────────────────────────┘
```

---

## 輸出範例

### 模式 A：解壓並整合
```
輸入資料夾/
├── archive1.zip
├── archive2.7z
└── subfolder/
    └── archive3.rar

輸出 → 自訂輸出位置/
├── file1.txt
├── file2.pdf
├── file3.jpg
└── ...（所有檔案平坦化）
```

### 模式 B：解壓並分檔
```
選擇：archive1.zip, archive2.zip, archive3.zip

輸出 → 自訂輸出位置/
├── archive1/
│   └── （archive1 的內容）
├── archive2/
│   └── （archive2 的內容）
└── archive3/
    └── （archive3 的內容）
```

---

## 系統需求

- Windows 10/11
- [7-Zip](https://7-zip.org/)（必須安裝）

---

## 支援格式

| 格式 | 副檔名 |
|------|--------|
| ZIP | .zip |
| 7-Zip | .7z |
| RAR | .rar |
| TAR | .tar |
| Gzip | .gz, .tgz |
| Bzip2 | .bz2, .tbz2 |
| XZ | .xz |

---

## 授權

MIT License

## 作者

YoLab工作室

---
---

# English Version

**Recursively extract nested archives and flatten all files to a single output directory.**

`BatchExtractor` is a tool that takes a directory full of (possibly nested) archives and extracts everything into a single, flat output folder. Perfect for dealing with messy downloads, backup archives, or any situation where files are buried in layers of compression.

## Features

- **Mode A: Extract & Merge** - Extract all archives to a single folder
- **Mode B: Extract & Separate** - Extract each archive to its own folder
- **Custom Output Location** - Choose any folder as output destination
- **Multi-language UI** - Supports Traditional Chinese / English (switchable)
- Supports ZIP, 7Z, RAR, TAR, GZ, BZ2, XZ and more
- Automatic filename conflict handling

## Installation

### Option 1: Use EXE directly (Recommended)

1. Download `壓縮檔工具.exe` from [Releases](https://github.com/Yakitori197/-BatchExtractor-/releases)
2. Make sure [7-Zip](https://7-zip.org/) is installed
3. Double-click to run

### Option 2: Run from source

Requires Python 3.9+:

```bash
git clone https://github.com/Yakitori197/-BatchExtractor-.git
cd -BatchExtractor-
pip install -e .
```

Run `Debug.bat` to start the program.

### Option 3: Build EXE yourself

1. Make sure Python 3.9+ is installed
2. Run `Install.bat`
3. Wait for build to complete, `壓縮檔工具.exe` will appear in project folder

## Usage

1. Run `壓縮檔工具.exe` (or `Debug.bat`)
2. Switch language in top-right corner (繁體中文 / English)
3. Select mode:
   - **Mode A**: Select folder containing archives
   - **Mode B**: Select multiple archive files (Ctrl+Click for multiple)
4. Choose output location
5. Click "Start Extraction"
6. Output folder opens automatically when complete

## Supported Formats

| Format | Extensions |
|--------|------------|
| ZIP | .zip |
| 7-Zip | .7z |
| RAR | .rar |
| TAR | .tar |
| Gzip | .gz, .tgz |
| Bzip2 | .bz2, .tbz2 |
| XZ | .xz |

## System Requirements

- Windows 10/11
- [7-Zip](https://7-zip.org/) (required)

## License

MIT License

## Author

YoLab Studio
