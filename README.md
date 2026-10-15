# Bandcamp Downloader (Multiplatform)

**[English](#-english) | [Русский](#-русский)**

---

## 🇬🇧 English

A cross-platform desktop application for downloading tracks, albums, and full artist discographies from **Bandcamp** on **Windows**, **macOS (Intel & Apple Silicon)**, and **Linux**.

Inspired by the original [Otiel/BandcampDownloader](https://github.com/Otiel/BandcampDownloader) (which is Windows-only due to C#/WPF), this project is built from the ground up in Python + Tkinter to run natively across all major desktop operating systems.

### ✨ Features

* **Download Anything:** single tracks (`/track/`), albums (`/album/`), label showcases, and complete artist discographies (`/music`), including lazy-loaded `data-client-items` releases.
* **Automatic ID3v2.3 Tagging:** embeds Track Title, Artist, Album Artist, Album, Track Number, Release Year, Lyrics (`USLT` extracted from JSON-LD), and Front Cover Art (`APIC`) directly into `.mp3` files.
* **Cover Art & Playlists:** saves high-resolution album art (`cover.jpg`) and generates `.m3u8` playlists.
* **Cloudflare / WAF Bypass:** 3-tier page fetcher (`curl_cffi` with Chrome TLS fingerprint impersonation → `requests` → system `curl` fallback).
* **On-the-fly Localization & GitHub Sync:** switches UI and event log languages instantly without restarting. Automatically checks the `lang/` folder in the GitHub repository on startup to download new or updated translations.
* **Persistent Settings:** saves the selected language, option checkboxes, and custom download path to `settings.json` next to the executable.

---

### 🚀 Option 1: Easy Way (Pre-built Releases)

No Python installation is required. Download the standalone executable for your OS:

1. Go to the **[Releases](https://github.com/murza-enikeeff/BandcampDownloader-multiplatform/releases)** page and download the package for your platform:
   * **Windows (x64):** `BandcampDownloader-Windows-x64.exe`
   * **macOS (Intel, macOS 11/12+):** `BandcampDownloader-macOS-Intel-x64.zip`
   * **macOS (Apple Silicon M1/M2/M3/M4):** `BandcampDownloader-macOS-AppleSilicon-arm64.zip`
   * **Linux (x64):** `BandcampDownloader-Linux-x64`
2. Run the application:
   * **Windows:** double-click `BandcampDownloader-Windows-x64.exe`.
   * **macOS:** extract the `.zip` archive and open `BandcampDownloader.app`.  
     *(If macOS Gatekeeper blocks the first launch, run `xattr -cr BandcampDownloader.app` in Terminal or Right-Click → Open).*
   * **Linux:** make the binary executable (`chmod +x BandcampDownloader-Linux-x64`) and launch it. On first run, it automatically registers a `.desktop` shortcut with an icon in `~/.local/share/applications/`.
3. On first launch, the app will automatically create `settings.json` and the `lang/` directory next to the executable and sync available translations from the repository.

---

### 🛠 Option 2: Developer Guide (Run from Source)

If you want to run the script directly with Python, customize the code, or build binaries locally:

#### 1. Clone the repository
```bash
git clone https://github.com/murza-enikeeff/BandcampDownloader-multiplatform.git
cd BandcampDownloader-multiplatform
```

#### 2. Install dependencies
Requires **Python 3.10+**.

```bash
pip install requests beautifulsoup4 mutagen curl_cffi pillow
```

> **Note on `tkinter`:**
> * Included by default on **Windows** and official **macOS** (`python.org`) installers.
> * On **macOS (Homebrew)**: `brew install python-tk`
> * On **Linux (Ubuntu/Debian)**: `sudo apt-get install -y python3-tk`

#### 3. Generate icons and run
```bash
python3 make_icons.py
python3 main.py
```

#### 4. Build standalone binaries locally (`PyInstaller`)
```bash
pip install pyinstaller
python3 make_icons.py
```

* **macOS (Intel `x86_64` or Apple Silicon `arm64`):**
  ```bash
  pyinstaller --noconfirm --windowed --name "BandcampDownloader" --icon "icon.icns" --add-data "icon.png:." --add-data "lang:lang" --collect-all curl_cffi main.py
  ```
* **Windows (`.exe`):**
  ```powershell
  pyinstaller --noconfirm --onefile --windowed --name "BandcampDownloader" --icon "icon.ico" --add-data "icon.png;." --add-data "lang;lang" --collect-all curl_cffi main.py
  ```
* **Linux:**
  ```bash
  pyinstaller --noconfirm --onefile --windowed --name "BandcampDownloader" --add-data "icon.png:." --add-data "lang:lang" --collect-all curl_cffi main.py
  ```

---

### 🌍 Localization (Adding New Languages)

Translations are stored in the `lang/` folder as standard JSON files (`en.json`, `nog.json`, `ru.json`, `hy.json`, etc.).
1. Copy an existing language file (e.g., `lang/en.json` → `lang/de.json`).
2. Set the display name in `"_lang_name"` and translate the string values.
3. Once a new `.json` file is committed to the `lang/` folder in the repository, existing release builds will automatically download it on their next startup.

---

## 🇷🇺 Русский

Кроссплатформенное десктопное приложение для скачивания треков, альбомов и полных дискографий с **Bandcamp** на **Windows**, **macOS (Intel и Apple Silicon)** и **Linux**.

Проект вдохновлён оригинальным [Otiel/BandcampDownloader](https://github.com/Otiel/BandcampDownloader) (который работал только на Windows из-за привязки к C#/WPF) и полностью переписан на Python + Tkinter с поддержкой всех современных десктопных ОС.

### ✨ Возможности

* **Скачивание любых релизов:** отдельные треки (`/track/`), альбомы (`/album/`), витрины лейблов и полные дискографии артистов (`/music`), включая скрытые релизы с ленивой подгрузкой (`data-client-items`).
* **Автоматические теги ID3v2.3:** прописывает Исполнителя, Исполнителя альбома, Название, Альбом, Номер трека, Год выпуска, Текст песни (`USLT` из JSON-LD) и вшивает обложку прямо в `.mp3`.
* **Обложки и плейлисты:** сохраняет обложку в высоком разрешении (`cover.jpg`) и создаёт плейлист формата `.m3u8`.
* **Обход защиты Cloudflare / WAF:** использует трёхуровневый механизм загрузки страниц (`curl_cffi` с имитацией TLS-отпечатка браузера Chrome → `requests` → системный `curl`).
* **Переключение языка «на лету» и автосинхронизация с GitHub:** мгновенно переводит весь интерфейс и уже выведенный журнал событий без перезапуска. При запуске автоматически проверяет папку `lang/` в репозитории и докачивает новые переводы.
* **Сохранение настроек:** выбранный язык, отмеченные галочки и нестандартный путь загрузки автоматически сохраняются в `settings.json` рядом с программой.

---

### 🚀 Способ 1. Простой путь (для пользователей)

Ничего устанавливать в систему (включая Python) не требуется — достаточно скачать готовый исполняемый файл для своей ОС:

1. Перейдите в раздел **[Releases](https://github.com/murza-enikeeff/BandcampDownloader-multiplatform/releases)** и скачайте версию под вашу систему:
   * **Windows (x64):** `BandcampDownloader-Windows-x64.exe`
   * **macOS (Intel, macOS 11/12+):** `BandcampDownloader-macOS-Intel-x64.zip`
   * **macOS (Apple Silicon M1/M2/M3/M4):** `BandcampDownloader-macOS-AppleSilicon-arm64.zip`
   * **Linux (x64):** `BandcampDownloader-Linux-x64`
2. Запустите приложение:
   * **Windows:** запустите `BandcampDownloader-Windows-x64.exe`.
   * **macOS:** распакуйте архив и запустите `BandcampDownloader.app`.  
     *(Если Gatekeeper выдаст предупреждение при первом запуске, выполните в Терминале: `xattr -cr BandcampDownloader.app` или откройте через ПКМ → «Открыть»).*
   * **Linux:** сделайте файл исполняемым (`chmod +x BandcampDownloader-Linux-x64`) и запустите его. При первом запуске программа автоматически создаст ярлык с иконкой в меню приложений (`~/.local/share/applications/`).
3. При первом запуске рядом с приложением автоматически создадутся файл настроек `settings.json` и папка `lang/` со всеми актуальными языковыми пакетами.

---

### 🛠 Способ 2. Путь разработчика (запуск из исходников)

Если вы хотите запускать программу напрямую через Python, вносить изменения в код или собирать бинарники самостоятельно:

#### 1. Клонирование репозитория
```bash
git clone https://github.com/murza-enikeeff/BandcampDownloader-multiplatform.git
cd BandcampDownloader-multiplatform
```

#### 2. Установка зависимостей
Требуется **Python 3.10+**.

```bash
pip install requests beautifulsoup4 mutagen curl_cffi pillow
```

> **Примечание по `tkinter`:**
> * На **Windows** и в официальном установщике Python для **macOS** (`python.org`) библиотека `tkinter` уже встроена.
> * Если на **macOS** используется Python из Homebrew: `brew install python-tk`
> * На **Linux (Ubuntu/Debian)**: `sudo apt-get install -y python3-tk`

#### 3. Генерация иконок и запуск
```bash
python3 make_icons.py
python3 main.py
```

#### 4. Самостоятельная сборка в исполняемый файл (`PyInstaller`)
```bash
pip install pyinstaller
python3 make_icons.py
```

* **macOS (Intel `x86_64` или Apple Silicon `arm64`):**
  ```bash
  pyinstaller --noconfirm --windowed --name "BandcampDownloader" --icon "icon.icns" --add-data "icon.png:." --add-data "lang:lang" --collect-all curl_cffi main.py
  ```
* **Windows (`.exe`):**
  ```powershell
  pyinstaller --noconfirm --onefile --windowed --name "BandcampDownloader" --icon "icon.ico" --add-data "icon.png;." --add-data "lang;lang" --collect-all curl_cffi main.py
  ```
* **Linux:**
  ```bash
  pyinstaller --noconfirm --onefile --windowed --name "BandcampDownloader" --add-data "icon.png:." --add-data "lang:lang" --collect-all curl_cffi main.py
  ```

---

### 🌍 Добавление новых языков (Локализация)

Все переводы хранятся в папке `lang/` в виде обычных JSON-файлов (например, `en.json`, `nog.json`, `ru.json`, `hy.json`).
1. Скопируйте существующий файл (например, `lang/en.json` → `lang/de.json`).
2. Укажите отображаемое название языка в поле `"_lang_name"` и переведите значения ключей.
3. При добавлении нового `.json` файла в папку `lang/` репозитория все пользователи собранных релизов получат его автоматически при следующем запуске программы.
