# 檔名: disbot_core.py
import requests, json, sys, os, subprocess
from datetime import datetime
from tkinter import messagebox

# === 敏感配置 (改由環境變數讀取以提升安全性) ===
CURRENT_VERSION = "1.0"
GIST_ID = "fb0cae35ea1752f634a5cb5bf72c3f20"
# 優先嘗試讀取環境變數，如果沒有則使用空字串或測試用的Token
GITHUB_TOKEN = os.getenv("DISBOT_GITHUB_TOKEN", "") 
CONFIG_FILE = "user_config.json"
AUTH_FILE = "auth.json"

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class API:
    # 使用 property 動態獲取 headers，確保能抓到最新的 TOKEN
    @property
    def HEADERS(self):
        return {"Authorization": f"token {GITHUB_TOKEN}"}
    
    @staticmethod
    def get_headers():
        return {"Authorization": f"token {GITHUB_TOKEN}"}

    @staticmethod
    def get_gist_file(filename):
        try:
            r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=API.get_headers(), timeout=5)
            if r.status_code != 200: return None
            content = r.json()['files'][filename]['content']
            return json.loads(content)
        except: return None

    @staticmethod
    def post_message(method, contact, content):
        try:
            r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=API.get_headers())
            if r.status_code != 200: return False
            current_content = r.json()['files']['messages.json']['content']
            data = json.loads(current_content) if current_content else []
            data.append({"method": method, "contact": contact, "content": content, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
            payload = {"files": {"messages.json": {"content": json.dumps(data, indent=4, ensure_ascii=False)}}}
            requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=API.get_headers(), json=payload)
            return True
        except: return False

class Updater:
    @staticmethod
    def check_and_update():
        cfg = API.get_gist_file("config.json")
        if not cfg: return
        remote_ver = cfg.get("version", "1.0")
        if remote_ver > CURRENT_VERSION:
            if messagebox.askyesno("更新", f"新版本 v{remote_ver} 可用，是否更新？"):
                Updater.perform_update(cfg.get("download_url"))
            else: sys.exit()

    @staticmethod
    def perform_update(url):
        if not url: return messagebox.showerror("錯誤", "無效下載連結")
        try:
            new_exe = "Disbot Ultra_new.exe"
            r = requests.get(url, stream=True)
            with open(new_exe, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
            
            bat_script = f"""
            @echo off
            timeout /t 1 /nobreak > NUL
            del "{sys.executable}"
            ren "{new_exe}" "{os.path.basename(sys.executable)}"
            start "" "{os.path.basename(sys.executable)}"
            del "%~f0"
            """
            with open("update.bat", "w") as f: f.write(bat_script)
            subprocess.Popen("update.bat", shell=True)
            sys.exit()
        except Exception as e: messagebox.showerror("更新失敗", str(e))