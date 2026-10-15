#!/usr/bin/env python3
# -*- coding: utf-8 -*-
APP_VERSION = "1.0.0"

import hashlib
import html
import json
import os
import queue
import re
import requests
import shutil
import subprocess
import sys
import threading
import tkinter as tk

from bs4 import BeautifulSoup
from datetime import datetime
from mutagen.id3 import (
    APIC,
    ID3,
    ID3NoHeaderError,
    TALB,
    TDRC,
    TIT2,
    TPE1,
    TPE2,
    TRCK,
    USLT,
)
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk
from urllib.parse import urljoin, urlparse

# Decoy for TLS-filter Bandcamp/Cloudflare
try:
    from curl_cffi import requests as cffi_requests
    HAS_CURL_CFFI = True
except ImportError:
    HAS_CURL_CFFI = False


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        exe_path = Path(sys.executable).resolve()
        # macOS lang and settings path
        if sys.platform == "darwin" and ".app/Contents/MacOS" in exe_path.as_posix():
            app_parent = exe_path.parents[3]
            if app_parent != Path("/Applications") and os.access(app_parent, os.W_OK):
                return app_parent
            support_dir = Path.home() / "Library" / "Application Support" / "BandcampDownloader"
            support_dir.mkdir(parents=True, exist_ok=True)
            return support_dir
        return exe_path.parent
    return Path(__file__).resolve().parent


def get_bundled_resource(filename: str) -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidate = Path(meipass) / filename
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parent / filename


BASE_DIR = get_base_dir()
DEFAULT_DOWNLOAD_DIR = Path.home() / "Downloads" / "Bandcamp"

DEFAULT_TRANSLATIONS = {
    "nog": {
        "_lang_name": "Ногъайша (nog)",
        "window_title": "Bandcamp Downloader (Multiplatform)",
        "lbl_lang": "Тил:",
        "lbl_urls": "Bandcamp силтемелери (аьр сыдыргъа бирер — треклер, альбомлар яде артистлер):",
        "lbl_folder": "Юклев къапшыгъы:",
        "btn_browse": "Сайлав...",
        "frame_options": "Сазлавлар",
        "chk_disco": "Артисттинъ сав дискографиясын юклев (/music)",
        "chk_cover": "Къаплама суьвретин сакълав (cover.jpg + ID3 ишине язув)",
        "chk_m3u": "Плейлист туьзуьв (.m3u8)",
        "btn_start": "Юклев",
        "btn_stop": "Токътатув",
        "lbl_log": "Вакъыялар журналы:",
        "warn_title": "Эскертуьв",
        "warn_no_urls": "Энъ азында бир Bandcamp силтемесин къосынъыз.",
        "log_cffi_active": "[+] curl_cffi модули ислейди (TLS-къоршалав Chrome режиминде оьтиледи).",
        "log_cffi_tip": "[i] Къосымша режим (requests + системалы curl). Chrome режими уьшин: pip install curl_cffi",
        "log_langs_synced": "[+] GitHub-тан тил пакетлери юкленди/янъыртылды: {langs}",
        "log_stop_signal": "[*] Токътатув белгиси йибериледи...",
        "log_queue_count": "[*] Кезектеги сав релизлер саны: {count}",
        "log_done": "\n=== Тамамланды ===",
        "log_check_disco": "[*] Дискографияды текшеруьв: {url}",
        "log_found_releases": "[+] Табылгъан релизлер: {count}",
        "log_processing": "\n=== Ишленуьв: {url} ===",
        "log_empty_response": "[!] Серверден бос явап келди. Интернет байланысынъызды текшеринъиз.",
        "log_showcase_found": "[*] Бу бет — витрина. Табылгъан релизлер: {count}",
        "log_no_tralbum": "[!] Бетте data-tralbum билдируьвлери табылмады (Беттинъ басы: '{title}').",
        "log_cloudflare": "[!] Сылтавы: Bandcamp браузерди текшеруьв бетин къайтарды (Cloudflare/WAF).",
        "log_cover_dl": "[*] Къаплама суьврети юкленеди...",
        "log_cover_err": "[!] Къаплама суьвретин юклеп болмады: {error}",
        "log_no_tracks": "[!] Треклер тизмеги бос яде релиз аьли де шыкъмагъан (pre-order).",
        "log_stopped": "[!] Къолланувшы ман токътатылды.",
        "log_skip_track": "[-] '{title}' къалдырылды (агъым ябыкъ яде табылмайды)",
        "log_dl_track": "[{idx}/{total}] Юкленуьв: {filename}",
        "log_m3u_created": "[+] Плейлист туьзилди: {name}",
        "log_release_done": "[✓] Аьзир ({downloaded}/{total} трек): {path}",
        "log_curl_fallback": "[*] Беттинъ къоршалавын оьтуьв уьшин системалы curl къолланылады...",
    },
    "en": {
        "_lang_name": "English (en)",
        "window_title": "Bandcamp Downloader (Multiplatform)",
        "lbl_lang": "Language:",
        "lbl_urls": "Bandcamp URLs (one per line — tracks, albums, or artists):",
        "lbl_folder": "Download folder:",
        "btn_browse": "Browse...",
        "frame_options": "Options",
        "chk_disco": "Download full artist discography (/music)",
        "chk_cover": "Save cover art (cover.jpg + embed in ID3)",
        "chk_m3u": "Create playlist (.m3u8)",
        "btn_start": "Download",
        "btn_stop": "Stop",
        "lbl_log": "Event log:",
        "warn_title": "Warning",
        "warn_no_urls": "Please add at least one Bandcamp URL.",
        "log_cffi_active": "[+] curl_cffi module is active (Chrome TLS impersonation enabled).",
        "log_cffi_tip": "[i] Fallback mode (requests + system curl). For Chrome TLS: pip install curl_cffi",
        "log_langs_synced": "[+] Downloaded/updated language packs from GitHub: {langs}",
        "log_stop_signal": "[*] Sending stop signal...",
        "log_queue_count": "[*] Total releases in queue: {count}",
        "log_done": "\n=== Finished ===",
        "log_check_disco": "[*] Checking discography: {url}",
        "log_found_releases": "[+] Releases found: {count}",
        "log_processing": "\n=== Processing: {url} ===",
        "log_empty_response": "[!] Empty response from server. Check your network connection.",
        "log_showcase_found": "[*] Page is a showcase. Releases found: {count}",
        "log_no_tralbum": "[!] No data-tralbum found on page (Page title: '{title}').",
        "log_cloudflare": "[!] Reason: Bandcamp returned a browser challenge page (Cloudflare/WAF).",
        "log_cover_dl": "[*] Downloading cover art...",
        "log_cover_err": "[!] Failed to download cover art: {error}",
        "log_no_tracks": "[!] Tracklist is empty or release is a pre-order.",
        "log_stopped": "[!] Stopped by user.",
        "log_skip_track": "[-] Skipping '{title}' (stream unavailable)",
        "log_dl_track": "[{idx}/{total}] Downloading: {filename}",
        "log_m3u_created": "[+] Playlist created: {name}",
        "log_release_done": "[✓] Completed ({downloaded}/{total} tracks): {path}",
        "log_curl_fallback": "[*] Using system curl to bypass page protection...",
    },
}

GITHUB_REPO = "murza-enikeeff/BandcampDownloader-multiplatform"
GITHUB_BRANCH = "main"
LANG_DIR = BASE_DIR / "lang"
SETTINGS_FILE = BASE_DIR / "settings.json"


class LocalizationManager:

    def __init__(self, lang_dir: Path):
        self.lang_dir = lang_dir
        self.available_langs: dict[str, dict[str, str]] = {}
        self.current_lang = "en"
        self._ensure_default_files()
        self._unpack_bundled_langs()
        self.scan_languages()

    def _ensure_default_files(self):
        self.lang_dir.mkdir(parents=True, exist_ok=True)
        for code, data in DEFAULT_TRANSLATIONS.items():
            file_path = self.lang_dir / f"{code}.json"
            need_write = False
            if not file_path.exists() or file_path.stat().st_size == 0:
                need_write = True
            else:
                try:
                    loaded = json.loads(file_path.read_text(encoding="utf-8"))
                    if not isinstance(loaded, dict) or not loaded:
                        need_write = True
                except Exception:
                    need_write = True

            if need_write:
                file_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )

    def _unpack_bundled_langs(self):
        meipass = getattr(sys, "_MEIPASS", None)
        if not meipass:
            return
        bundled_dir = Path(meipass) / "lang"
        if not bundled_dir.is_dir():
            return
        for src_file in bundled_dir.glob("*.json"):
            dst_file = self.lang_dir / src_file.name
            if not dst_file.exists() or dst_file.stat().st_size == 0:
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception:
                    pass

    @staticmethod
    def _git_blob_sha(data: bytes) -> str:
        header = f"blob {len(data)}\0".encode("utf-8")
        return hashlib.sha1(header + data).hexdigest()

    def sync_from_github(self, repo: str, branch: str = "main") -> list[str]:
        if not repo or "/" not in repo:
            return []

        api_url = f"https://api.github.com/repos/{repo.strip('/')}/contents/lang?ref={branch}"
        updated_codes = []

        try:
            resp = requests.get(
                api_url,
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "BandcampDownloader-multiplatform",
                },
                timeout=8,
            )
            if resp.status_code != 200:
                return []

            items = resp.json()
            if not isinstance(items, list):
                return []

            for item in items:
                name = item.get("name", "")
                if not name.endswith(".json") or item.get("type") != "file":
                    continue

                remote_sha = item.get("sha")
                download_url = item.get("download_url")
                if not download_url:
                    continue

                local_file = self.lang_dir / name
                need_download = True

                if local_file.exists() and remote_sha:
                    try:
                        local_bytes = local_file.read_bytes()
                        if self._git_blob_sha(local_bytes) == remote_sha:
                            need_download = False
                    except Exception:
                        pass

                if need_download:
                    file_resp = requests.get(download_url, timeout=8)
                    if file_resp.status_code == 200:
                        try:
                            parsed_json = json.loads(file_resp.text)
                            if isinstance(parsed_json, dict) and parsed_json:
                                local_file.write_bytes(file_resp.content)
                                updated_codes.append(Path(name).stem)
                        except Exception:
                            pass
        except Exception:
            pass

        if updated_codes:
            self.scan_languages()
        return updated_codes

    def scan_languages(self):
        self.available_langs.clear()
        for file_path in sorted(self.lang_dir.glob("*.json")):
            code = file_path.stem.lower()
            try:
                content = json.loads(file_path.read_text(encoding="utf-8"))
                if isinstance(content, dict):
                    self.available_langs[code] = content
            except Exception:
                if code in DEFAULT_TRANSLATIONS:
                    self.available_langs[code] = DEFAULT_TRANSLATIONS[code]

        if not self.available_langs:
            self.available_langs = DEFAULT_TRANSLATIONS.copy()

        if self.current_lang not in self.available_langs:
            self.current_lang = (
                "en" if "en" in self.available_langs else next(iter(self.available_langs))
            )

    def get_display_map(self) -> dict[str, str]:
        display_map = {}
        for code, data in self.available_langs.items():
            label = data.get("_lang_name") or f"{code.upper()} ({code}.json)"
            display_map[label] = code
        return display_map

    def set_language(self, code: str):
        if code in self.available_langs:
            self.current_lang = code

    def t(self, key: str, **kwargs) -> str:
        lang_dict = self.available_langs.get(self.current_lang, {})
        fallback_dict = DEFAULT_TRANSLATIONS.get("en", {})
        template = lang_dict.get(key) or fallback_dict.get(key) or key
        if kwargs:
            try:
                return template.format(**kwargs)
            except Exception:
                return template
        return template


class SettingsManager:

    DEFAULT_SETTINGS = {
        "language": "en",
        "download_discography": False,
        "save_cover": True,
        "create_playlist": False,
        "custom_output_dir": "",
    }

    def __init__(self, settings_file: Path, default_download_dir: Path):
        self.settings_file = settings_file
        self.default_download_dir = default_download_dir
        self.data = self.DEFAULT_SETTINGS.copy()
        self.load()

    @staticmethod
    def _normalize_path(p: Path | str) -> str:
        try:
            return str(Path(p).expanduser().resolve())
        except Exception:
            return str(Path(p).expanduser())

    def load(self):
        if self.settings_file.exists():
            try:
                loaded = json.loads(self.settings_file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    for k in self.DEFAULT_SETTINGS:
                        if k in loaded:
                            self.data[k] = loaded[k]
            except Exception:
                pass
        else:
            self.save()

    def save(self):
        try:
            self.settings_file.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def get_effective_output_dir(self) -> str:
        custom = str(self.data.get("custom_output_dir", "")).strip()
        if custom:
            return custom
        return str(self.default_download_dir)

    def update_state(
        self,
        language: str,
        download_discography: bool,
        save_cover: bool,
        create_playlist: bool,
        current_output_dir: str,
    ):
        self.data["language"] = language
        self.data["download_discography"] = bool(download_discography)
        self.data["save_cover"] = bool(save_cover)
        self.data["create_playlist"] = bool(create_playlist)

        norm_current = self._normalize_path(current_output_dir)
        norm_default = self._normalize_path(self.default_download_dir)

        if current_output_dir.strip() and norm_current != norm_default:
            self.data["custom_output_dir"] = current_output_dir.strip()
        else:
            self.data["custom_output_dir"] = ""

        self.save()


class BandcampEngine:

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/avif,image/webp,image/apng,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    def __init__(self, log_callback, progress_callback, stop_event):
        self.log = log_callback
        self.set_progress = progress_callback
        self.stop_event = stop_event

        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

        self.cffi_session = None
        if HAS_CURL_CFFI:
            try:
                self.cffi_session = cffi_requests.Session(impersonate="chrome")
            except Exception:
                self.cffi_session = None

    @staticmethod
    def sanitize_filename(name: str) -> str:
        cleaned = re.sub(r'[\\/*?:"<>|]', "_", str(name)).strip()
        return cleaned.rstrip(".") or "Unknown"

    def fetch_html(self, url: str) -> tuple[str, str]:
        if self.cffi_session is not None:
            try:
                resp = self.cffi_session.get(url, headers=self.HEADERS, timeout=20)
                if resp.status_code == 200 and (
                    "data-tralbum" in resp.text
                    or "music-grid" in resp.text
                    or "TralbumData" in resp.text
                ):
                    return resp.text, str(resp.url)
            except Exception:
                pass

        html_text = ""
        final_url = url
        try:
            resp = self.session.get(url, timeout=20)
            html_text = resp.text
            final_url = str(resp.url)
            if resp.status_code == 200 and (
                "data-tralbum" in html_text
                or "music-grid" in html_text
                or "TralbumData" in html_text
            ):
                return html_text, final_url
        except Exception:
            pass

        curl_bin = shutil.which("curl")
        if curl_bin:
            try:
                self.log("log_curl_fallback")
                cmd = [
                    curl_bin,
                    "-sL",
                    "--compressed",
                    "-A",
                    self.HEADERS["User-Agent"],
                    "-H",
                    f"Accept: {self.HEADERS['Accept']}",
                    "-H",
                    f"Accept-Language: {self.HEADERS['Accept-Language']}",
                    url,
                ]
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=25,
                )
                if proc.returncode == 0 and proc.stdout:
                    return proc.stdout, final_url
            except Exception:
                pass

        return html_text, final_url

    @staticmethod
    def extract_tralbum_data(
        html_text: str, soup: BeautifulSoup | None = None
    ) -> dict | None:
        patterns = [
            r'data-tralbum="([^"]+)"',
            r"data-tralbum='([^']+)'",
        ]
        for pat in patterns:
            match = re.search(pat, html_text, re.DOTALL)
            if match:
                raw_attr = html.unescape(match.group(1))
                try:
                    return json.loads(raw_attr)
                except json.JSONDecodeError:
                    pass

        if soup is None:
            soup = BeautifulSoup(html_text, "html.parser")
        tag = soup.find(attrs={"data-tralbum": True})
        if tag:
            raw_attr = tag.get("data-tralbum", "")
            for candidate in (raw_attr, html.unescape(raw_attr)):
                try:
                    return json.loads(candidate)
                except Exception:
                    pass

        js_match = re.search(
            r"(?:window\.|var\s+)TralbumData\s*=\s*(\{.*?\});\s*\n",
            html_text,
            re.DOTALL,
        )
        if js_match:
            try:
                return json.loads(js_match.group(1))
            except Exception:
                pass

        return None

    def resolve_urls(self, raw_urls: list[str], download_discography: bool) -> list[str]:
        resolved = []
        for raw_url in raw_urls:
            if self.stop_event.is_set():
                break

            url = raw_url.strip()
            parsed = urlparse(url)
            if not parsed.scheme:
                url = "https://" + url
                parsed = urlparse(url)

            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            is_album_or_track = "/album/" in parsed.path or "/track/" in parsed.path

            if download_discography or not is_album_or_track:
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                music_url = urljoin(base_url, "/music")
                self.log("log_check_disco", url=music_url)
                disco_urls = self._extract_discography(music_url, base_url)
                if disco_urls:
                    self.log("log_found_releases", count=len(disco_urls))
                    resolved.extend(disco_urls)
                    continue

            resolved.append(clean_url)

        return list(dict.fromkeys(resolved))

    def _extract_discography(self, music_url: str, base_url: str) -> list[str]:
        urls = []
        try:
            html_text, final_url = self.fetch_html(music_url)
            if not html_text:
                return []

            soup = BeautifulSoup(html_text, "html.parser")

            client_items_raw = None
            grid = soup.find(id="music-grid") or soup.find(
                attrs={"data-client-items": True}
            )
            if grid and grid.get("data-client-items"):
                client_items_raw = grid.get("data-client-items")
            else:
                m = re.search(r'data-client-items="([^"]+)"', html_text)
                if m:
                    client_items_raw = html.unescape(m.group(1))

            search_root = grid if grid else soup
            for a_tag in search_root.find_all("a", href=True):
                href = a_tag["href"].split("?")[0].split("#")[0]
                if "/album/" in href or "/track/" in href:
                    full_link = urljoin(base_url, href)
                    if urlparse(full_link).netloc == urlparse(base_url).netloc:
                        urls.append(full_link)

            if client_items_raw:
                try:
                    for item in json.loads(client_items_raw):
                        page_url = item.get("page_url")
                        if page_url:
                            urls.append(urljoin(base_url, page_url.split("?")[0]))
                except Exception:
                    pass

            if not urls and self.extract_tralbum_data(html_text, soup):
                return [final_url]

        except Exception:
            pass

        return list(dict.fromkeys(urls))

    def download_release(
        self,
        url: str,
        output_dir: Path,
        save_cover: bool = True,
        create_playlist: bool = True,
        _depth: int = 0,
    ):
        self.log("log_processing", url=url)
        html_text, final_url = self.fetch_html(url)
        if not html_text:
            self.log("log_empty_response")
            return

        soup = BeautifulSoup(html_text, "html.parser")
        tralbum = self.extract_tralbum_data(html_text, soup)

        if not tralbum:
            if _depth == 0:
                parsed = urlparse(final_url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                sub_links = []
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"].split("?")[0].split("#")[0]
                    if "/album/" in href or "/track/" in href:
                        full_link = urljoin(base_url, href)
                        if urlparse(full_link).netloc == parsed.netloc:
                            sub_links.append(full_link)
                sub_links = list(dict.fromkeys(sub_links))
                if sub_links:
                    self.log("log_showcase_found", count=len(sub_links))
                    for sub_url in sub_links:
                        if self.stop_event.is_set():
                            break
                        self.download_release(
                            sub_url, output_dir, save_cover, create_playlist, _depth=1
                        )
                    return

            page_title = (
                soup.title.string.strip()
                if (soup.title and soup.title.string)
                else "No Title"
            )
            self.log("log_no_tralbum", title=page_title)
            if (
                "moment" in page_title.lower()
                or "cloudflare" in html_text.lower()
                or "challenge" in html_text.lower()
            ):
                self.log("log_cloudflare")
            return

        current = tralbum.get("current") or {}
        album_artist = (
            tralbum.get("artist")
            or current.get("artist")
            or self._extract_meta_artist(soup)
            or "Unknown Artist"
        )
        album_title = current.get("title") or "Unknown Album"
        art_id = tralbum.get("art_id") or current.get("art_id")

        release_year = ""
        raw_date = (
            current.get("release_date")
            or current.get("publish_date")
            or tralbum.get("album_release_date")
        )
        if raw_date:
            try:
                dt = datetime.strptime(raw_date, "%d %b %Y %H:%M:%S %Z")
                release_year = str(dt.year)
            except ValueError:
                year_match = re.search(r"\b(19\d\d|20\d\d)\b", str(raw_date))
                if year_match:
                    release_year = year_match.group(1)

        lyrics_map = self._extract_lyrics(soup)

        folder_name = self.sanitize_filename(f"{album_artist} - {album_title}")
        if release_year:
            folder_name = self.sanitize_filename(
                f"{album_artist} - ({release_year}) {album_title}"
            )
        album_path = output_dir / folder_name
        album_path.mkdir(parents=True, exist_ok=True)

        cover_bytes = None
        if art_id and save_cover:
            cover_url = f"https://f4.bcbits.com/img/a{art_id}_10.jpg"
            try:
                self.log("log_cover_dl")
                cover_bytes = self._download_bytes(cover_url)
                if cover_bytes:
                    (album_path / "cover.jpg").write_bytes(cover_bytes)
            except Exception as e:
                self.log("log_cover_err", error=str(e))

        tracks = tralbum.get("trackinfo") or []
        if not tracks:
            self.log("log_no_tracks")
            return

        playlist_entries = ["#EXTM3U"]
        total_tracks = len(tracks)
        downloaded_count = 0

        for idx, track in enumerate(tracks, start=1):
            if self.stop_event.is_set():
                self.log("log_stopped")
                return

            track_title = track.get("title") or f"Track {idx}"
            track_num = track.get("track_num") or idx
            track_artist = track.get("artist") or album_artist
            duration = int(track.get("duration") or 0)
            file_info = track.get("file") or {}

            stream_url = file_info.get("mp3-128")
            if not stream_url and file_info:
                stream_url = next(iter(file_info.values()), None)

            if not stream_url:
                self.log("log_skip_track", title=track_title)
                continue

            if stream_url.startswith("//"):
                stream_url = "https:" + stream_url

            filename = self.sanitize_filename(
                f"{int(track_num):02d}. {track_artist} - {track_title}.mp3"
            )
            filepath = album_path / filename

            self.log(
                "log_dl_track",
                idx=idx,
                total=total_tracks,
                filename=filename,
            )
            if self._download_file(stream_url, filepath):
                downloaded_count += 1
                lyrics = track.get("lyrics") or lyrics_map.get(int(track_num), "")
                self._write_id3_tags(
                    filepath=filepath,
                    title=track_title,
                    artist=track_artist,
                    album_artist=album_artist,
                    album=album_title,
                    track_num=f"{track_num}/{total_tracks}",
                    year=release_year,
                    lyrics=lyrics,
                    cover_bytes=cover_bytes,
                )
                playlist_entries.append(
                    f"#EXTINF:{duration},{track_artist} - {track_title}"
                )
                playlist_entries.append(filename)

            self.set_progress((idx / total_tracks) * 100)

        if create_playlist and downloaded_count > 0:
            m3u_name = self.sanitize_filename(f"{album_artist} - {album_title}.m3u8")
            (album_path / m3u_name).write_text(
                "\n".join(playlist_entries), encoding="utf-8"
            )
            self.log("log_m3u_created", name=m3u_name)

        self.log(
            "log_release_done",
            downloaded=downloaded_count,
            total=total_tracks,
            path=album_path,
        )

    @staticmethod
    def _extract_meta_artist(soup: BeautifulSoup) -> str:
        band_name = soup.select_one("#band-name-location .title")
        if band_name and band_name.get_text(strip=True):
            return band_name.get_text(strip=True)
        return ""

    @staticmethod
    def _extract_lyrics(soup: BeautifulSoup) -> dict[int, str]:
        lyrics_by_track = {}
        ld_script = soup.find("script", {"type": "application/ld+json"})
        if not ld_script or not ld_script.string:
            return lyrics_by_track
        try:
            data = json.loads(ld_script.string)
            tracks = data.get("track", {}).get("itemListElement", [])
            for item in tracks:
                pos = item.get("position")
                recording = item.get("item", {})
                lyrics_text = (
                    recording.get("recordingOf", {}).get("lyrics", {}).get("text")
                )
                if pos and lyrics_text:
                    lyrics_by_track[int(pos)] = lyrics_text
        except Exception:
            pass
        return lyrics_by_track

    def _download_bytes(self, url: str) -> bytes | None:
        if self.cffi_session is not None:
            try:
                r = self.cffi_session.get(url, timeout=20)
                if r.status_code == 200:
                    return r.content
            except Exception:
                pass
        r = self.session.get(url, timeout=20)
        return r.content if r.ok else None

    def _download_file(self, url: str, dest: Path) -> bool:
        try:
            with self.session.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if self.stop_event.is_set():
                            return False
                        if chunk:
                            f.write(chunk)
            return True
        except Exception:
            if self.cffi_session is not None:
                try:
                    r = self.cffi_session.get(url, timeout=40)
                    r.raise_for_status()
                    dest.write_bytes(r.content)
                    return True
                except Exception:
                    pass
            return False

    def _write_id3_tags(
        self,
        filepath: Path,
        title: str,
        artist: str,
        album_artist: str,
        album: str,
        track_num: str,
        year: str,
        lyrics: str,
        cover_bytes: bytes | None,
    ):
        try:
            try:
                tags = ID3(filepath)
            except ID3NoHeaderError:
                tags = ID3()

            tags.add(TIT2(encoding=3, text=title))
            tags.add(TPE1(encoding=3, text=artist))
            tags.add(TPE2(encoding=3, text=album_artist))
            tags.add(TALB(encoding=3, text=album))
            tags.add(TRCK(encoding=3, text=str(track_num)))
            if year:
                tags.add(TDRC(encoding=3, text=str(year)))
            if lyrics:
                tags.add(USLT(encoding=3, lang="eng", desc="", text=lyrics))
            if cover_bytes:
                tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=cover_bytes,
                    )
                )
            tags.save(filepath, v2_version=3)
        except Exception:
            pass


class BandcampDownloaderGUI:

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.geometry("750x600")
        self.root.minsize(620, 500)

        self._set_window_icon()
        self._ensure_linux_desktop_entry()

        self.i18n = LocalizationManager(LANG_DIR)
        self.settings = SettingsManager(SETTINGS_FILE, DEFAULT_DOWNLOAD_DIR)

        saved_lang = self.settings.data.get("language", "en")
        if saved_lang not in self.i18n.available_langs:
            saved_lang = self.i18n.current_lang
        self.i18n.set_language(saved_lang)

        self.log_queue = queue.Queue()
        self.log_history: list[tuple[str, dict]] = []
        self.stop_event = threading.Event()
        self.worker_thread = None

        self._build_ui()
        self.apply_localization()
        self._poll_log_queue()

        if sys.platform == "darwin":
            try:
                self.root.createcommand("tkAboutDialog", self.show_about)
            except Exception:
                pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        if HAS_CURL_CFFI:
            self.enqueue_log("log_cffi_active")
        else:
            self.enqueue_log("log_cffi_tip")

        # Update new languages from repo
        threading.Thread(target=self._sync_github_langs_worker, daemon=True).start()

    def show_about(self):
        messagebox.showinfo(
            self.i18n.t("window_title"),
            f"Bandcamp Downloader (Multiplatform)\n"
            f"Version: {APP_VERSION}\n\n"
            f"GitHub: https://github.com/{GITHUB_REPO}",
        )

    def _sync_github_langs_worker(self):
        updated = self.i18n.sync_from_github(GITHUB_REPO, GITHUB_BRANCH)
        if updated:
            self.log_queue.put(("langs_updated", updated))

    def _set_window_icon(self):
        icon_png = get_bundled_resource("icon.png")
        if icon_png.exists():
            try:
                self._icon_img = tk.PhotoImage(file=str(icon_png))
                self.root.iconphoto(True, self._icon_img)
            except Exception:
                pass

    def _ensure_linux_desktop_entry(self):
        if not sys.platform.startswith("linux") or not getattr(sys, "frozen", False):
            return

        try:
            src_icon = get_bundled_resource("icon.png")
            local_icon = BASE_DIR / "icon.png"
            if src_icon.exists() and not local_icon.exists():
                shutil.copy2(src_icon, local_icon)

            apps_dir = Path.home() / ".local" / "share" / "applications"
            apps_dir.mkdir(parents=True, exist_ok=True)
            desktop_file = apps_dir / "bandcamp-downloader.desktop"

            exe_path = Path(sys.executable).resolve()
            content = (
                "[Desktop Entry]\n"
                "Type=Application\n"
                f"Version={APP_VERSION}\n"
                "Name=Bandcamp Downloader\n"
                "Comment=Multiplatform Bandcamp Downloader\n"
                f'Exec="{exe_path}"\n'
                f"Icon={local_icon}\n"
                "Terminal=false\n"
                "Categories=AudioVideo;Audio;Network;\n"
                "StartupWMClass=BandcampDownloader\n"
            )
            if not desktop_file.exists() or desktop_file.read_text(encoding="utf-8") != content:
                desktop_file.write_text(content, encoding="utf-8")
                desktop_file.chmod(0o755)
        except Exception:
            pass

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        self.lbl_urls = ttk.Label(main, text="")
        self.lbl_urls.pack(anchor=tk.W)

        self.urls_text = scrolledtext.ScrolledText(main, height=6, font=("Menlo", 10))
        self.urls_text.pack(fill=tk.X, pady=(4, 10))

        folder_frame = ttk.Frame(main)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_folder = ttk.Label(folder_frame, text="")
        self.lbl_folder.pack(side=tk.LEFT)

        self.output_var = tk.StringVar(value=self.settings.get_effective_output_dir())
        self.output_entry = ttk.Entry(folder_frame, textvariable=self.output_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.output_entry.bind("<FocusOut>", lambda _e: self.save_current_settings())
        self.output_entry.bind("<Return>", lambda _e: self.save_current_settings())

        self.btn_browse = ttk.Button(folder_frame, text="", command=self._choose_dir)
        self.btn_browse.pack(side=tk.RIGHT)

        self.opts_frame = ttk.LabelFrame(main, text="", padding=8)
        self.opts_frame.pack(fill=tk.X, pady=(0, 10))

        opts_inner = ttk.Frame(self.opts_frame)
        opts_inner.pack(fill=tk.X)

        lang_frame = ttk.Frame(opts_inner)
        lang_frame.pack(side=tk.RIGHT, anchor=tk.N, padx=(12, 2), pady=(1, 0))

        self.lbl_lang = ttk.Label(lang_frame, text="")
        self.lbl_lang.grid(row=0, column=0, padx=(0, 6), pady=(0, 2), sticky=tk.E)

        self.display_to_code = self.i18n.get_display_map()
        self.code_to_display = {v: k for k, v in self.display_to_code.items()}

        self.lang_combo_var = tk.StringVar(
            value=self.code_to_display.get(self.i18n.current_lang, "")
        )
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_combo_var,
            values=list(self.display_to_code.keys()),
            state="readonly",
            width=16,
        )
        self.lang_combo.grid(row=0, column=1, sticky=tk.E)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_change)

        self.about_btn = ttk.Button(
            lang_frame, text="?", width=3, command=self.show_about
        )
        self.about_btn.grid(row=1, column=1, pady=(6, 0), sticky=tk.E)

        checks_frame = ttk.Frame(opts_inner)
        checks_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.disco_var = tk.BooleanVar(
            value=bool(self.settings.data.get("download_discography", False))
        )
        self.cover_var = tk.BooleanVar(
            value=bool(self.settings.data.get("save_cover", True))
        )
        self.m3u_var = tk.BooleanVar(
            value=bool(self.settings.data.get("create_playlist", False))
        )

        self.chk_disco = ttk.Checkbutton(
            checks_frame,
            text="",
            variable=self.disco_var,
            command=self.save_current_settings,
        )
        self.chk_disco.pack(anchor=tk.W)

        self.chk_cover = ttk.Checkbutton(
            checks_frame,
            text="",
            variable=self.cover_var,
            command=self.save_current_settings,
        )
        self.chk_cover.pack(anchor=tk.W)

        self.chk_m3u = ttk.Checkbutton(
            checks_frame,
            text="",
            variable=self.m3u_var,
            command=self.save_current_settings,
        )
        self.chk_m3u.pack(anchor=tk.W)

        ctrl_frame = ttk.Frame(main)
        ctrl_frame.pack(fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(ctrl_frame, text="", command=self.start_download)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.stop_btn = ttk.Button(
            ctrl_frame, text="", command=self.stop_download, state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(
            ctrl_frame, variable=self.progress_var, maximum=100.0
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0))

        self.lbl_log = ttk.Label(main, text="")
        self.lbl_log.pack(anchor=tk.W)

        self.log_area = scrolledtext.ScrolledText(
            main, height=12, state=tk.DISABLED, font=("Menlo", 10)
        )
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

    def _refresh_language_combobox(self):
        self.display_to_code = self.i18n.get_display_map()
        self.code_to_display = {v: k for k, v in self.display_to_code.items()}
        self.lang_combo.configure(values=list(self.display_to_code.keys()))
        self.lang_combo_var.set(self.code_to_display.get(self.i18n.current_lang, ""))

    def apply_localization(self):
        t = self.i18n.t
        self.root.title(f"{t('window_title')} v{APP_VERSION}")
        self.lbl_lang.configure(text=t("lbl_lang"))
        self.lbl_urls.configure(text=t("lbl_urls"))
        self.lbl_folder.configure(text=t("lbl_folder"))
        self.btn_browse.configure(text=t("btn_browse"))
        self.opts_frame.configure(text=t("frame_options"))
        self.chk_disco.configure(text=t("chk_disco"))
        self.chk_cover.configure(text=t("chk_cover"))
        self.chk_m3u.configure(text=t("chk_m3u"))
        self.start_btn.configure(text=t("btn_start"))
        self.stop_btn.configure(text=t("btn_stop"))
        self.lbl_log.configure(text=t("lbl_log"))
        self._rerender_log()

    def _rerender_log(self):
        if not self.log_history:
            return
        yview = self.log_area.yview()
        at_bottom = yview[1] >= 0.99

        self.log_area.configure(state=tk.NORMAL)
        self.log_area.delete("1.0", tk.END)
        rendered_lines = [
            self.i18n.t(key, **kwargs) for key, kwargs in self.log_history
        ]
        self.log_area.insert(tk.END, "\n".join(rendered_lines) + "\n")
        if at_bottom:
            self.log_area.see(tk.END)
        else:
            self.log_area.yview_moveto(yview[0])
        self.log_area.configure(state=tk.DISABLED)

    def _on_language_change(self, _event=None):
        self.i18n.scan_languages()
        selected_display = self.lang_combo_var.get()
        lang_code = self.display_to_code.get(selected_display, "en")

        self.i18n.set_language(lang_code)
        self._refresh_language_combobox()
        self.apply_localization()
        self.save_current_settings()

    def save_current_settings(self):
        self.settings.update_state(
            language=self.i18n.current_lang,
            download_discography=self.disco_var.get(),
            save_cover=self.cover_var.get(),
            create_playlist=self.m3u_var.get(),
            current_output_dir=self.output_var.get(),
        )

    def _on_close(self):
        self.save_current_settings()
        self.root.destroy()

    def _choose_dir(self):
        selected = filedialog.askdirectory(initialdir=self.output_var.get())
        if selected:
            self.output_var.set(selected)
            self.save_current_settings()

    def enqueue_log(self, key: str, **kwargs):
        self.log_queue.put(("log", (key, kwargs)))

    def enqueue_progress(self, value: float):
        self.log_queue.put(("progress", value))

    def _poll_log_queue(self):
        while not self.log_queue.empty():
            kind, payload = self.log_queue.get_nowait()
            if kind == "log":
                key, kwargs = payload
                self.log_history.append((key, kwargs))
                translated_line = self.i18n.t(key, **kwargs)
                self.log_area.configure(state=tk.NORMAL)
                self.log_area.insert(tk.END, translated_line + "\n")
                self.log_area.see(tk.END)
                self.log_area.configure(state=tk.DISABLED)
            elif kind == "langs_updated":
                updated_codes = payload
                self._refresh_language_combobox()
                self.apply_localization()
                self.enqueue_log("log_langs_synced", langs=", ".join(updated_codes))
            elif kind == "progress":
                self.progress_var.set(payload)
            elif kind == "done":
                self.start_btn.configure(state=tk.NORMAL)
                self.stop_btn.configure(state=tk.DISABLED)
        self.root.after(100, self._poll_log_queue)

    def start_download(self):
        self.save_current_settings()
        raw_text = self.urls_text.get("1.0", tk.END).strip()
        urls = [line.strip() for line in raw_text.splitlines() if line.strip()]
        if not urls:
            messagebox.showwarning(
                self.i18n.t("warn_title"), self.i18n.t("warn_no_urls")
            )
            return

        output_dir = Path(self.output_var.get()).expanduser()
        self.stop_event.clear()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.progress_var.set(0.0)

        self.worker_thread = threading.Thread(
            target=self._run_worker,
            args=(
                urls,
                output_dir,
                self.disco_var.get(),
                self.cover_var.get(),
                self.m3u_var.get(),
            ),
            daemon=True,
        )
        self.worker_thread.start()

    def stop_download(self):
        self.enqueue_log("log_stop_signal")
        self.stop_event.set()

    def _run_worker(self, urls, output_dir, disco, cover, m3u):
        engine = BandcampEngine(
            self.enqueue_log,
            self.enqueue_progress,
            self.stop_event,
        )
        target_urls = engine.resolve_urls(urls, download_discography=disco)
        self.enqueue_log("log_queue_count", count=len(target_urls))

        for url in target_urls:
            if self.stop_event.is_set():
                break
            engine.download_release(
                url=url,
                output_dir=output_dir,
                save_cover=cover,
                create_playlist=m3u,
            )

        self.enqueue_log("log_done")
        self.log_queue.put(("done", None))


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "bandcamp.downloader.multiplatform.1"
            )
        except Exception:
            pass

    root = tk.Tk(className="BandcampDownloader")
    app = BandcampDownloaderGUI(root)
    root.mainloop()
