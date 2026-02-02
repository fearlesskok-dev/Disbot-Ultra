# 檔名: Disbot_Ultra.py
import customtkinter as ctk
import threading, time, random, os, requests, json, uuid, sys, subprocess, webbrowser, ctypes
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox

# === CONFIG ===
CURRENT_VERSION = "1.1"

# 替換為您的實際 GIST 資訊
GIST_ID = "fb0cae35ea1752f634a5cb5bf72c3f20"
# 修改為環境變數讀取，預設為空字串避免報錯
GITHUB_TOKEN = os.getenv("DISBOT_GITHUB_TOKEN", "") 
CONFIG_FILE = "user_config.json"
AUTH_FILE = "auth.json"

# === 全域樣式設定 ===
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# 字體設定
FONT_MAIN = ("Microsoft JhengHei UI", 12)
FONT_BOLD = ("Microsoft JhengHei UI", 12, "bold")
FONT_HEAD = ("Microsoft JhengHei UI", 14, "bold")
FONT_DASH_NAME = ("Microsoft JhengHei UI", 14, "bold") 
FONT_DASH_STATUS = ("Microsoft JhengHei UI", 13, "bold") 
FONT_TIMER = ("Consolas", 24, "bold") 

COLOR_ACCENT = "#3B8ED0"
COLOR_BG_CARD = "#232323"
COLOR_IDLE = "#666666"
COLOR_SUCCESS = "#00E676"
COLOR_FAIL = "#FF5252"
COLOR_WARN = "#FFB74D"

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === API ===
class API:
    @staticmethod
    def get_headers():
        return {"Authorization": f"token {GITHUB_TOKEN}"}
    
    @staticmethod
    def get_gist_file(filename):
        try:
            r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=API.get_headers(), timeout=10)
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

# === Updater ===
class Updater:
    @staticmethod
    def check_and_update():
        cfg = API.get_gist_file("config.json")
        if not cfg: return
        remote_ver = cfg.get("version", CURRENT_VERSION)
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

# === Login ===
class LoginWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('disbot.ultra.login')
        except: pass
        
        self.title(f"Disbot Ultra v{CURRENT_VERSION} - 系統驗證")
        self.geometry("450x650")
        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path): self.iconbitmap(icon_path)
        
        self.hwid = str(uuid.getnode())
        self.authorized = False
        self.expiry_info = ""
        self.valid_key = ""
        self.global_cfg = API.get_gist_file("config.json") or {}

        main = ctk.CTkFrame(self, corner_radius=15, fg_color="#181818"); main.pack(expand=True, fill="both", padx=20, pady=20)
        ctk.CTkLabel(main, text="Disbot Ultra", font=("Microsoft JhengHei UI", 32, "bold"), text_color="#3B8ED0").pack(pady=(40, 5))
        ctk.CTkLabel(main, text="精準排程 ‧ 解放雙手", font=("Microsoft JhengHei UI", 16), text_color="gray").pack(pady=(0, 30))

        h_frame = ctk.CTkFrame(main, fg_color="transparent"); h_frame.pack(pady=5)
        ctk.CTkLabel(h_frame, text="設備識別碼:", font=("", 12)).pack(anchor="w")
        self.hwid_ent = ctk.CTkEntry(h_frame, width=280, justify="center", fg_color="#111")
        self.hwid_ent.insert(0, self.hwid); self.hwid_ent.configure(state="readonly"); self.hwid_ent.pack(side="left", padx=(0,5))
        ctk.CTkButton(h_frame, text="複製", width=50, fg_color="#444", command=lambda: [self.clipboard_clear(), self.clipboard_append(self.hwid)]).pack(side="left")

        self.key_ent = ctk.CTkEntry(main, placeholder_text="請輸入 PROV1 授權金鑰", width=340, height=45, font=("Consolas", 14), justify="center", border_color="#3B8ED0")
        self.key_ent.pack(pady=20)
        
        if os.path.exists(AUTH_FILE):
            try: 
                with open(AUTH_FILE, "r") as f: self.key_ent.insert(0, json.load(f).get("key", ""))
            except: pass

        ctk.CTkButton(main, text="🚀 立即驗證登入", font=("", 16, "bold"), height=50, width=280, fg_color="#2E7D32", hover_color="#1B5E20", command=self.verify).pack(pady=10)
        
        link_frame = ctk.CTkFrame(main, fg_color="transparent"); link_frame.pack(pady=10)
        if self.global_cfg.get("discord_link"):
            ctk.CTkButton(link_frame, text="用戶群", fg_color="#5865F2", width=130, command=lambda: webbrowser.open(self.global_cfg["discord_link"])).pack(side="left", padx=5)
        ctk.CTkButton(link_frame, text="聯絡管理員", fg_color="#424242", width=130, command=self.open_contact).pack(side="left", padx=5)

    def verify(self):
        key = self.key_ent.get().strip()
        if not key: return messagebox.showwarning("提示", "請輸入金鑰")
        try:
            db = API.get_gist_file("keys.json")
            if not db: return messagebox.showerror("連線錯誤", "無法連接伺服器")

            if key in db and str(db[key]['hwid']) == self.hwid:
                exp_date = datetime.strptime(db[key]['expiry'], "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                if now < exp_date:
                    with open(AUTH_FILE, "w") as f: json.dump({"key": key}, f)
                    if (exp_date - now).total_seconds() < 86400:
                        messagebox.showwarning("續費提醒", "您的授權即將在 24 小時內到期！")
                    self.expiry_info = db[key]['expiry']
                    self.valid_key = key
                    self.authorized = True
                    self.destroy()
                else: messagebox.showerror("驗證失敗", "授權已到期")
            else: messagebox.showerror("驗證失敗", "金鑰無效")
        except Exception as e: messagebox.showerror("錯誤", str(e))

    def open_contact(self):
        ContactWindow(self, self.global_cfg.get("contact_info", "請留言"))

class ContactWindow(ctk.CTkToplevel):
    def __init__(self, parent, info_text):
        super().__init__(parent)
        self.title("聯絡管理員"); self.geometry("400x500")
        self.attributes('-topmost', True); self.lift(); self.focus_force()
        ctk.CTkLabel(self, text=info_text, font=FONT_HEAD).pack(pady=15)
        self.method = ctk.StringVar(value="Discord ID")
        ctk.CTkSegmentedButton(self, values=["Discord ID", "Line ID"], variable=self.method).pack(pady=5)
        self.contact = ctk.CTkEntry(self, placeholder_text="請輸入您的 ID", width=300); self.contact.pack(pady=5)
        
        self.placeholder = "請在此輸入您的問題或續費需求..."
        self.msg = ctk.CTkTextbox(self, width=300, height=200, text_color="gray")
        self.msg.pack(pady=10)
        self.msg.insert("1.0", self.placeholder)
        self.msg.bind("<FocusIn>", self.on_enter); self.msg.bind("<FocusOut>", self.on_leave)
        
        ctk.CTkButton(self, text="送出訊息", command=self.submit, fg_color=COLOR_ACCENT, font=FONT_BOLD).pack(pady=10)

    def on_enter(self, event):
        if self.msg.get("1.0", "end-1c") == self.placeholder:
            self.msg.delete("1.0", "end"); self.msg.configure(text_color="#FFFFFF")
    def on_leave(self, event):
        if not self.msg.get("1.0", "end-1c").strip():
            self.msg.configure(text_color="gray"); self.msg.insert("1.0", self.placeholder)
    def submit(self):
        content = self.msg.get("1.0", "end").strip()
        contact = self.contact.get().strip()
        if not content or content == self.placeholder or not contact: return messagebox.showwarning("提示", "請填寫完整內容")
        if API.post_message(self.method.get(), contact, content):
            messagebox.showinfo("成功", "訊息已發送"); self.destroy()
        else: messagebox.showerror("錯誤", "發送失敗")

# === Main App ===
class BotGroup(ctk.CTkFrame):
    def __init__(self, master, name, default_interval, is_ab=False, **kwargs):
        super().__init__(master, fg_color=COLOR_BG_CARD, corner_radius=12, border_width=1, border_color="#333", **kwargs)
        self.name, self.is_ab, self.channels = name, is_ab, []
        self.selected_path = None
        
        header = ctk.CTkFrame(self, fg_color="transparent", height=35)
        header.pack(fill="x", padx=12, pady=(10, 5))
        ctk.CTkLabel(header, text=f"▌ {name}", font=FONT_HEAD, text_color=COLOR_ACCENT).pack(side="left")
        self.en_var = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(header, text="", variable=self.en_var, width=35, progress_color="#4CAF50").pack(side="right")
        
        if not is_ab:
            ctk.CTkLabel(header, text="秒", font=("", 11)).pack(side="right", padx=2)
            self.int_ent = ctk.CTkEntry(header, width=50, height=24, justify="center", font=("Consolas", 12))
            self.int_ent.insert(0, str(default_interval)); self.int_ent.pack(side="right")

        content_grid = ctk.CTkFrame(self, fg_color="transparent")
        content_grid.pack(fill="both", expand=True, padx=10, pady=5)
        content_grid.grid_columnconfigure(0, weight=7); content_grid.grid_columnconfigure(1, weight=3); content_grid.grid_rowconfigure(0, weight=1)

        self.placeholder = "在此輸入訊息內容..."
        self.msg_txt = ctk.CTkTextbox(content_grid, height=150, fg_color="#1A1A1A", border_width=1, border_color="#333", font=FONT_MAIN, text_color="gray")
        self.msg_txt.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        self.msg_txt.insert("1.0", self.placeholder)
        self.msg_txt.bind("<FocusIn>", self.on_enter); self.msg_txt.bind("<FocusOut>", self.on_leave)

        tools_panel = ctk.CTkFrame(content_grid, fg_color="transparent"); tools_panel.grid(row=0, column=1, sticky="nsew")
        self.img_btn = ctk.CTkButton(tools_panel, text="📂 圖片資料夾", height=28, fg_color="#333", hover_color="#444", command=self.pick, font=("", 11)); self.img_btn.pack(fill="x", pady=(0, 5))
        self.ch_list = ctk.CTkScrollableFrame(tools_panel, height=80, fg_color="#181818", label_text="發送頻道", label_font=("", 11, "bold")); self.ch_list.pack(fill="both", expand=True, pady=(0, 5))
        add_box = ctk.CTkFrame(tools_panel, fg_color="transparent"); add_box.pack(fill="x")
        self.ch_ent = ctk.CTkEntry(add_box, placeholder_text="ID / 網址", height=28, font=("Consolas", 11)); self.ch_ent.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(add_box, text="+", width=28, height=28, fg_color=COLOR_ACCENT, command=self.add_ch).pack(side="right", padx=(3,0))

    def on_enter(self, event):
        if self.msg_txt.get("1.0", "end-1c") == self.placeholder: self.msg_txt.delete("1.0", "end"); self.msg_txt.configure(text_color="#FFFFFF")
    def on_leave(self, event):
        if not self.msg_txt.get("1.0", "end-1c").strip(): self.msg_txt.configure(text_color="gray"); self.msg_txt.insert("1.0", self.placeholder)
    def pick(self):
        p = filedialog.askdirectory()
        if p: self.selected_path = p; self.img_btn.configure(text=f"📂 {os.path.basename(p)[:8]}..", fg_color="#2E7D32")
    def add_ch(self):
        raw = self.ch_ent.get().strip()
        if not raw: return
        c = raw.split('/')[-1] if "discord" in raw else raw
        if c.isdigit() and c not in self.channels: self.channels.append(c); self.refresh_ch(); self.ch_ent.delete(0, 'end')
        elif not c.isdigit(): messagebox.showerror("錯誤", "無法識別的頻道 ID 格式")
    def refresh_ch(self):
        for w in self.ch_list.winfo_children(): w.destroy()
        for c in self.channels:
            f = ctk.CTkFrame(self.ch_list, fg_color="#222", height=25); f.pack(fill="x", pady=1)
            ctk.CTkLabel(f, text=c, font=("Microsoft JhengHei UI", 13, "bold")).pack(side="left", padx=5)
            ctk.CTkButton(f, text="×", width=20, height=20, fg_color="transparent", text_color="#F44336", hover_color="#333", command=lambda x=c: [self.channels.remove(x), self.refresh_ch()]).pack(side="right")

class MainApp(ctk.CTk):
    def __init__(self, expiry, current_key):
        super().__init__()
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('disbot.ultra.main')
        except: pass
        self.title(f"Disbot Ultra v{CURRENT_VERSION} - 精準排程 - 解放雙手")
        self.geometry("1400x900"); self.running = False
        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path): self.iconbitmap(icon_path)
        
        self.start_timestamp = None 
        self.auth_key = current_key 
        
        # 啟動後台驗證守護線程
        threading.Thread(target=self.security_monitor, daemon=True).start()

        # Top Bar
        top_bar = ctk.CTkFrame(self, height=60, fg_color="#181818", corner_radius=0); top_bar.pack(fill="x")
        ctk.CTkLabel(top_bar, text="DISBOT ULTRA", font=("Impact", 28), text_color=COLOR_ACCENT).pack(side="left", padx=20)
        ctk.CTkLabel(top_bar, text="Professional Scheduler", font=("Arial", 12), text_color="gray").pack(side="left", pady=(10,0))
        
        info_f = ctk.CTkFrame(top_bar, fg_color="transparent"); info_f.pack(side="right", padx=20)
        ctk.CTkLabel(info_f, text="授權狀態: ", font=FONT_MAIN).pack(side="left")
        ctk.CTkLabel(info_f, text=f"{expiry}", font=("Consolas", 14, "bold"), text_color="#00E676").pack(side="left")

        # Control Panel
        ctrl_panel = ctk.CTkFrame(self, fg_color="#222", corner_radius=0); ctrl_panel.pack(fill="x", pady=(0, 10))
        r1 = ctk.CTkFrame(ctrl_panel, fg_color="transparent"); r1.pack(fill="x", padx=20, pady=12)
        
        self.tk_ent = ctk.CTkEntry(r1, width=400, placeholder_text="在此輸入 Discord Token", font=("Consolas", 12), border_color="#444"); self.tk_ent.pack(side="left")
        self.st_btn = ctk.CTkButton(r1, text="▶ 啟動排程", fg_color="#2E7D32", hover_color="#1B5E20", font=FONT_BOLD, width=150, height=36, command=self.toggle); self.st_btn.pack(side="left", padx=15)
        ctk.CTkButton(r1, text="💾 儲存配置", fg_color=COLOR_ACCENT, font=FONT_BOLD, width=120, height=36, command=self.save_cfg).pack(side="left")

        t_f = ctk.CTkFrame(r1, fg_color="#2A2A2A", corner_radius=6); t_f.pack(side="right")
        self.time_en = ctk.BooleanVar(value=False); ctk.CTkCheckBox(t_f, text="時段限制", variable=self.time_en, font=FONT_MAIN).pack(side="left", padx=12, pady=6)
        self.start_t = ctk.CTkEntry(t_f, width=60, justify="center", font=("Consolas", 12)); self.start_t.insert(0, "00:00"); self.start_t.pack(side="left")
        ctk.CTkLabel(t_f, text=" ~ ").pack(side="left")
        self.end_t = ctk.CTkEntry(t_f, width=60, justify="center", font=("Consolas", 12)); self.end_t.insert(0, "23:59"); self.end_t.pack(side="left", padx=(0,10))

        # Dashboard Area
        mid = ctk.CTkFrame(self, height=200, fg_color="transparent"); mid.pack(fill="x", padx=20)
        self.log_box = ctk.CTkTextbox(mid, height=220, font=("Consolas", 11), fg_color="#111", corner_radius=10, text_color="#ddd"); self.log_box.pack(side="left", fill="both", expand=True)

        dash = ctk.CTkFrame(mid, width=420, fg_color="#181818", corner_radius=12); dash.pack(side="right", fill="y", padx=(15,0))
        
        ctk.CTkLabel(dash, text="本次總運行時間", font=("", 10), text_color="gray").pack(pady=(15, 0))
        self.runtime_lbl = ctk.CTkLabel(dash, text="00:00:00", font=FONT_TIMER, text_color=COLOR_SUCCESS)
        self.runtime_lbl.pack(pady=(0, 10))

        ctk.CTkFrame(dash, height=1, fg_color="#333").pack(fill="x", padx=15, pady=5)
        
        self.dash_labels = {}
        items = [("系統狀態", "System"), ("A/B循環", "Loop"), ("C組排程", "Grp C"), ("D組排程", "Grp D"), ("E組排程", "Grp E"), ("F組排程", "Grp F")]
        
        for name, key in items:
            row = ctk.CTkFrame(dash, fg_color="transparent", height=38) 
            row.pack(fill="x", pady=2, padx=20)
            ind = ctk.CTkLabel(row, text="●", font=("Arial", 16), text_color=COLOR_IDLE, width=20); ind.pack(side="left", padx=(0,5))
            ctk.CTkLabel(row, text=name, width=120, anchor="w", font=FONT_DASH_NAME).pack(side="left")
            st = ctk.CTkLabel(row, text="待命中", text_color=COLOR_IDLE, width=120, anchor="w", font=FONT_DASH_STATUS); st.pack(side="left")
            self.dash_labels[name if "排程" in name or "循環" in name else "系統狀態"] = {"st": st, "ind": ind}

        # Scroll Area
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent"); scroll.pack(fill="both", expand=True, padx=15, pady=10)
        scroll.grid_columnconfigure((0, 1), weight=1)
        
        ab_frame = ctk.CTkFrame(scroll, fg_color="#1E1E1E", border_width=1, border_color="#333"); ab_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=10)
        ab_head = ctk.CTkFrame(ab_frame, fg_color="transparent"); ab_head.pack(fill="x", padx=15, pady=8)
        
        ctk.CTkLabel(ab_head, text="A/B 智能循環核心", font=FONT_HEAD, text_color="#FFB74D").pack(side="left")
        
        self.ab_en = ctk.BooleanVar(value=True); ctk.CTkSwitch(ab_head, text="啟用核心", variable=self.ab_en, font=FONT_BOLD).pack(side="right", padx=(10, 0))
        self.ab_int = ctk.CTkEntry(ab_head, width=50, justify="center"); self.ab_int.insert(0, "300"); self.ab_int.pack(side="right")
        ctk.CTkLabel(ab_head, text="總循環間隔:", font=FONT_MAIN).pack(side="right", padx=(10, 5))
        self.ab_max = ctk.CTkEntry(ab_head, width=40, justify="center"); self.ab_max.insert(0, "30"); self.ab_max.pack(side="right")
        ctk.CTkLabel(ab_head, text="-").pack(side="right", padx=2)
        self.ab_min = ctk.CTkEntry(ab_head, width=40, justify="center"); self.ab_min.insert(0, "15"); self.ab_min.pack(side="right")
        ctk.CTkLabel(ab_head, text="組間隨機(s):", font=FONT_MAIN).pack(side="right", padx=(0, 5))

        ab_content = ctk.CTkFrame(ab_frame, fg_color="transparent"); ab_content.pack(fill="both", expand=True, padx=5, pady=5)
        ab_content.grid_columnconfigure((0,1), weight=1)
        self.ga = BotGroup(ab_content, "A組", 0, True); self.ga.grid(row=0, column=0, padx=5, sticky="nsew")
        self.gb = BotGroup(ab_content, "B組", 0, True); self.gb.grid(row=0, column=1, padx=5, sticky="nsew")
        
        self.gps = {"c": BotGroup(scroll, "C組", 720), "d": BotGroup(scroll, "D組", 1800), "e": BotGroup(scroll, "E組", 3600), "f": BotGroup(scroll, "F組", 7200)}
        self.gps["c"].grid(row=1, column=0, sticky="nsew", padx=10, pady=10); self.gps["d"].grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.gps["e"].grid(row=2, column=0, sticky="nsew", padx=10, pady=10); self.gps["f"].grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        
        self.load_cfg()
        threading.Thread(target=self.ui_ticker, daemon=True).start()

    def security_monitor(self):
        cached_hwid = str(uuid.getnode())
        while True:
            time.sleep(random.randint(300, 600))
            try:
                db = API.get_gist_file("keys.json")
                if db:
                    if self.auth_key not in db:
                        self.force_logout("授權已被撤銷")
                        break
                    
                    exp_date = datetime.strptime(db[self.auth_key]['expiry'], "%Y-%m-%d %H:%M:%S")
                    if datetime.now() > exp_date:
                        self.force_logout("授權已到期")
                        break
                    
                    remote_hwid = str(db[self.auth_key]['hwid'])
                    if remote_hwid != cached_hwid:
                         self.force_logout("設備識別碼不匹配")
                         break
            except Exception:
                pass

    def force_logout(self, reason):
        self.running = False
        def _show_and_exit():
            messagebox.showerror("授權終止", f"系統偵測到授權異常：\n{reason}\n\n程式將關閉。")
            os._exit(0) 
        self.after(0, _show_and_exit)

    def log(self, msg):
        def _update():
            time_str = datetime.now().strftime('%H:%M:%S')
            self.log_box.insert("end", f"[{time_str}] {msg}\n")
            self.log_box.see("end")
        self.after(0, _update)
    
    def ui_ticker(self):
        while True:
            if self.running and self.start_timestamp:
                delta = datetime.now() - self.start_timestamp
                total_seconds = int(delta.total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours:02}:{minutes:02}:{seconds:02}"
                try: self.runtime_lbl.configure(text=time_str)
                except: pass
            else:
                try: self.runtime_lbl.configure(text="00:00:00")
                except: pass

            if not self.running:
                for key, widgets in self.dash_labels.items():
                    try:
                        if key == "系統狀態":
                            widgets["st"].configure(text="已停止", text_color=COLOR_FAIL)
                            widgets["ind"].configure(text="●", text_color=COLOR_FAIL)
                        else:
                            widgets["st"].configure(text="待命中", text_color=COLOR_IDLE)
                            widgets["ind"].configure(text="●", text_color=COLOR_IDLE)
                    except: pass
            else:
                try:
                    sys_st = self.dash_labels["系統狀態"]
                    in_time = self.is_in_time()
                    txt = "運行中" if in_time else "時段待機"
                    col = COLOR_SUCCESS if in_time else COLOR_WARN
                    sys_st["st"].configure(text=txt, text_color=col)
                    sys_st["ind"].configure(text="●", text_color=col)
                except: pass
            
            time.sleep(1)

    def is_in_time(self):
        if not self.time_en.get(): return True
        try:
            now = datetime.now().time()
            s = datetime.strptime(self.start_t.get(), "%H:%M").time()
            e = datetime.strptime(self.end_t.get(), "%H:%M").time()
            return s <= now <= e if s <= e else now >= s or now <= e
        except: return True

    def send(self, gn, ch, txt, path):
        if not self.is_in_time(): return
        tk = self.tk_ent.get().strip()
        msg = txt.get("1.0", "end-1c")
        if "在此輸入" in msg: msg = ""
        
        files = []
        opened_files = []
        try:
            if path and os.path.exists(path):
                all_imgs = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.png','.jpg','.jpeg','.gif'))]
                target_imgs = all_imgs[:10]
                for i, p in enumerate(target_imgs):
                    f = open(p, "rb")
                    opened_files.append(f)
                    files.append((f"files[{i}]", (os.path.basename(p), f)))

            if not msg and not files: return
            
            r = requests.post(f"https://discord.com/api/v9/channels/{ch}/messages", headers={"Authorization": tk}, data={"content": msg}, files=files, timeout=30)
            
            if r.status_code in [200, 201]: 
                img_info = f" (+{len(files)}圖)" if files else ""
                self.log(f"✅ [{gn}] 頻道 {ch} 發送成功{img_info}")
            else: 
                self.log(f"❌ [{gn}] 發送失敗 | 代碼: {r.status_code}")
        except Exception as e: 
            self.log(f"❌ [{gn}] 系統錯誤: {e}")
        finally:
            for f in opened_files:
                try: f.close()
                except: pass

    def worker_ab(self):
        while self.running:
            if not self.is_in_time(): time.sleep(10); continue
            if self.ab_en.get():
                if self.ga.en_var.get():
                    self.set_dash("A/B循環", "A組發送中...", "#29B6F6")
                    for c in self.ga.channels: self.send("A組", c, self.ga.msg_txt, self.ga.selected_path); time.sleep(2)
                
                if self.ga.en_var.get() and self.ga.channels:
                    self.log("✅ [A組] 本輪發送已完成")

                try:
                    mn, mx = int(self.ab_min.get()), int(self.ab_max.get())
                    if mn > mx: mn, mx = mx, mn
                    wait = random.randint(mn, mx)
                except: wait = 20
                
                for i in range(wait, 0, -1):
                    if not self.running: return
                    self.set_dash("A/B循環", f"組間冷卻 {i}s", COLOR_WARN); time.sleep(1)

                if self.gb.en_var.get():
                    self.set_dash("A/B循環", "B組發送中...", "#29B6F6")
                    for c in self.gb.channels: self.send("B組", c, self.gb.msg_txt, self.gb.selected_path); time.sleep(2)

                if self.gb.en_var.get() and self.gb.channels:
                    self.log("✅ [B組] 本輪發送已完成")

                try: cycle = int(self.ab_int.get())
                except: cycle = 300
                for i in range(cycle, 0, -1):
                    if not self.running: return
                    self.set_dash("A/B循環", f"循環等待 {i}s", COLOR_SUCCESS); time.sleep(1)
            else: time.sleep(5)

    def worker_ind(self, g):
        while self.running:
            if not self.is_in_time(): time.sleep(10); continue
            if g.en_var.get():
                self.set_dash(g.name + "排程", "發送中...", "#29B6F6")
                for c in g.channels: self.send(g.name, c, g.msg_txt, g.selected_path); time.sleep(2)
                
                if g.channels:
                    self.log(f"✅ [{g.name}] 本輪發送已完成")

                try: wait = int(g.int_ent.get())
                except: wait = 600
                for i in range(wait, 0, -1):
                    if not self.running: return
                    self.set_dash(g.name + "排程", f"等待中 {i}s", COLOR_SUCCESS); time.sleep(1)
            else:
                self.set_dash(g.name + "排程", "已停用", COLOR_IDLE); time.sleep(5)

    def set_dash(self, key, st, col):
        def _update():
            try:
                self.dash_labels[key]["st"].configure(text=st, text_color=col)
                self.dash_labels[key]["ind"].configure(text="●", text_color=col)
            except: pass
        self.after(0, _update)

    def toggle(self):
        self.running = not self.running
        self.st_btn.configure(text="⛔ 停止排程" if self.running else "▶ 啟動排程", fg_color=COLOR_FAIL if self.running else "#2E7D32")
        
        if self.running:
            self.start_timestamp = datetime.now()
            self.log("🚀 排程系統已啟動")
            threading.Thread(target=self.worker_ab, daemon=True).start()
            for k, g in self.gps.items(): threading.Thread(target=self.worker_ind, args=(g,), daemon=True).start()
        else:
            self.start_timestamp = None
            self.log("🛑 排程系統已停止")

    def save_cfg(self):
        d = {"token": self.tk_ent.get(), "ab_int": self.ab_int.get(), 
             "ab_min": self.ab_min.get(), "ab_max": self.ab_max.get(),
             "ab_en": self.ab_en.get(), "time_en": self.time_en.get(), 
             "start_t": self.start_t.get(), "end_t": self.end_t.get()}
        for k, o in {"a":self.ga, "b":self.gb, **self.gps}.items():
            msg = o.msg_txt.get("1.0", "end-1c")
            if msg == o.placeholder: msg = ""
            d[k] = {"ch": o.channels, "msg": msg, "img": o.selected_path or "", "en": o.en_var.get()}
            if not o.is_ab: d[k]["int"] = o.int_ent.get()
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump(d, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("成功", "配置已儲存")

    def load_cfg(self):
        if not os.path.exists(CONFIG_FILE): return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                self.tk_ent.insert(0, d.get("token", ""))
                self.ab_int.delete(0, 'end'); self.ab_int.insert(0, d.get("ab_int", "300"))
                self.ab_min.delete(0, 'end'); self.ab_min.insert(0, d.get("ab_min", "15"))
                self.ab_max.delete(0, 'end'); self.ab_max.insert(0, d.get("ab_max", "30"))
                self.ab_en.set(d.get("ab_en", True)); self.time_en.set(d.get("time_en", False))
                
                self.start_t.delete(0, 'end'); self.start_t.insert(0, d.get("start_t", "00:00"))
                self.end_t.delete(0, 'end'); self.end_t.insert(0, d.get("end_t", "23:59"))

                for k, o in {"a":self.ga, "b":self.gb, **self.gps}.items():
                    g = d.get(k, {}); o.channels = g.get("ch", [])
                    saved_msg = g.get("msg", "")
                    o.msg_txt.delete("1.0", "end")
                    if saved_msg: 
                        o.msg_txt.insert("1.0", saved_msg); o.msg_txt.configure(text_color="#FFFFFF")
                    else:
                        o.msg_txt.insert("1.0", o.placeholder); o.msg_txt.configure(text_color="gray")
                    
                    if g.get("img"): o.selected_path = g["img"]; o.img_btn.configure(text=f"📂 {os.path.basename(g['img'])[:8]}..", fg_color="#2E7D32")
                    o.en_var.set(g.get("en", True)); o.refresh_ch()
                    if not o.is_ab: o.int_ent.delete(0, 'end'); o.int_ent.insert(0, g.get("int", "600"))
        except: pass

if __name__ == "__main__":
    mutex_name = "Global\\Disbot_Ultra_Unique_Mutex_v1"
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, mutex_name)
    
    if kernel32.GetLastError() == 183: 
        root = ctk.CTk(); root.withdraw() 
        messagebox.showerror("重複開啟", "Disbot Ultra 已經在運行中！\n請勿重複開啟程式。")
        root.destroy(); sys.exit()

    Updater.check_and_update()
    login = LoginWindow()
    login.mainloop()
    if login.authorized: MainApp(login.expiry_info, login.valid_key).mainloop()