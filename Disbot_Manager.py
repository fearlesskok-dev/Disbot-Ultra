import customtkinter as ctk
import requests, json, random, string, threading, os, sys, ctypes
from datetime import datetime, timedelta
from tkinter import messagebox

# === 核心配置 ===
# 請確保 GIST_ID 和 TOKEN 是最新的
GIST_ID = "fb0cae35ea1752f634a5cb5bf72c3f20"
GITHUB_TOKEN = os.getenv("DISBOT_GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}

# === 🎨 旗艦版配色方案 ===
THEME = {
    "bg_main": "#0f172a",       # 深藍黑背景
    "bg_sidebar": "#1e293b",    # 側邊欄背景
    "bg_card": "#334155",       # 卡片背景
    "text_main": "#f8fafc",     # 主文字
    "text_sub": "#94a3b8",      # 次要文字
    "accent": "#3b82f6",        # 品牌藍
    "accent_hover": "#2563eb",  # 品牌藍 (深)
    "danger": "#ef4444",        # 危險紅
    "danger_hover": "#dc2626",  # 危險紅 (深)
    "success": "#10b981",       # 成功綠
    "input_bg": "#1e293b"       # 輸入框背景
}

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class GitHubManager:
    @staticmethod
    def get_gist():
        try:
            r = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS, timeout=10)
            if r.status_code == 200: return r.json()
            else: return None
        except: return None

    @staticmethod
    def update_file(filename, content):
        try:
            payload = {"files": {filename: {"content": json.dumps(content, indent=4, ensure_ascii=False)}}}
            r = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=HEADERS, json=payload, timeout=10)
            return r.status_code == 200
        except: return False

class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        try: ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('disbot.manager.pro')
        except: pass
        
        self.title("Disbot Manager - 旗艦後台"); self.geometry("1280x800")
        self.configure(fg_color=THEME["bg_main"])
        icon_path = resource_path("logo1.ico")
        if os.path.exists(icon_path): self.iconbitmap(icon_path)

        # === 佈局 ===
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(0, weight=1)

        # 1. 側邊導航欄
        self.nav_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=THEME["bg_sidebar"])
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_rowconfigure(5, weight=1)

        # Logo
        ctk.CTkLabel(self.nav_frame, text="DISBOT", font=("Impact", 28), text_color=THEME["accent"]).grid(row=0, column=0, padx=20, pady=(25, 0), sticky="w")
        ctk.CTkLabel(self.nav_frame, text="MANAGER PRO", font=("Arial", 10, "bold"), text_color=THEME["text_sub"]).grid(row=1, column=0, padx=22, pady=(0, 10), sticky="w")

        self.frames = {}
        self.btn_keys = self.create_nav_btn("🔑  授權金鑰", 2, "keys")
        self.btn_msgs = self.create_nav_btn("📩  訊息中心", 3, "msgs")
        self.btn_settings = self.create_nav_btn("⚙️  系統參數", 4, "settings")
        
        ctk.CTkLabel(self.nav_frame, text="v1.3 Optimized", text_color="gray30", font=("Arial", 10)).grid(row=6, column=0, pady=20)

        # 2. 內容區域
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_columnconfigure(0, weight=1); self.content_area.grid_rowconfigure(0, weight=1)

        self.setup_keys_frame()
        self.setup_msgs_frame()
        self.setup_settings_frame()
        self.select_frame("keys")

    def create_nav_btn(self, text, row, name):
        btn = ctk.CTkButton(self.nav_frame, text=text, fg_color="transparent", text_color=THEME["text_sub"], 
                            hover_color=THEME["bg_card"], anchor="w", height=42, font=("Microsoft JhengHei UI", 14, "bold"),
                            command=lambda: self.select_frame(name))
        btn.grid(row=row, column=0, sticky="ew", padx=10, pady=1)
        return btn

    def select_frame(self, name):
        btns = {"keys": self.btn_keys, "msgs": self.btn_msgs, "settings": self.btn_settings}
        for n, b in btns.items():
            b.configure(fg_color=THEME["accent"] if n == name else "transparent", text_color="#fff" if n == name else THEME["text_sub"])
        for f in self.frames.values(): f.grid_forget()
        self.frames[name].grid(row=0, column=0, sticky="nsew")

    # === 工具函數 ===
    def parse_expiry(self, date_str):
        try: return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try: return datetime.strptime(date_str, "%Y-%m-%d")
            except: return datetime.now() - timedelta(days=1)

    # === 頁面 1: 金鑰管理 ===
    def setup_keys_frame(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent"); self.frames["keys"] = f
        f.grid_columnconfigure(0, weight=1); f.grid_rowconfigure(2, weight=1)
        
        # 狀態概覽
        metrics = ctk.CTkFrame(f, fg_color="transparent", height=40)
        metrics.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.lbl_total = ctk.CTkLabel(metrics, text="總金鑰: --", font=("Arial", 12, "bold"), text_color="white")
        self.lbl_total.pack(side="left", padx=10)
        self.lbl_active = ctk.CTkLabel(metrics, text="活躍中: --", font=("Arial", 12, "bold"), text_color=THEME["success"])
        self.lbl_active.pack(side="left", padx=10)

        # 控制台 (Grid 佈局)
        ctrl = ctk.CTkFrame(f, fg_color=THEME["bg_sidebar"], corner_radius=8)
        ctrl.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(ctrl, text="新增授權", font=("Microsoft JhengHei UI", 14, "bold"), text_color="#fff").grid(row=0, column=0, rowspan=2, padx=20)

        # 第一行：HWID + 時間
        self.hwid_ent = ctk.CTkEntry(ctrl, placeholder_text="輸入客戶機器碼 (HWID)", height=32, width=320, fg_color=THEME["bg_main"], border_color=THEME["bg_card"])
        self.hwid_ent.grid(row=0, column=1, padx=5, pady=(15, 5), sticky="ew")
        
        self.dur_var = ctk.StringVar(value="1個月")
        ctk.CTkComboBox(ctrl, values=["1天", "1週", "1個月", "1季", "1年", "永久"], variable=self.dur_var, width=120, height=32, button_color=THEME["accent"]).grid(row=0, column=2, padx=5, pady=(15, 5))

        # 第二行：名稱 + 平台選擇 + ID + 按鈕
        row1_frame = ctk.CTkFrame(ctrl, fg_color="transparent")
        row1_frame.grid(row=1, column=1, columnspan=2, sticky="w", padx=5, pady=(5, 15))

        self.user_name_ent = ctk.CTkEntry(row1_frame, placeholder_text="用戶名稱", height=32, width=120, fg_color=THEME["bg_main"], border_color=THEME["bg_card"])
        self.user_name_ent.pack(side="left", padx=(0, 5))

        self.platform_var = ctk.StringVar(value="Line")
        self.platform_combo = ctk.CTkComboBox(row1_frame, values=["Line", "Discord", "Telegram", "Other"], variable=self.platform_var, width=100, height=32, button_color=THEME["accent"])
        self.platform_combo.pack(side="left", padx=(0, 5))

        # ID 輸入框
        self.contact_ent = ctk.CTkEntry(row1_frame, placeholder_text="輸入 ID", height=32, width=150, fg_color=THEME["bg_main"], border_color=THEME["bg_card"])
        self.contact_ent.pack(side="left", padx=(0, 15))

        ctk.CTkButton(row1_frame, text="+ 生成", height=32, width=80, fg_color=THEME["success"], hover_color="#059669", font=("", 12, "bold"), command=self.generate_key).pack(side="left", padx=2)
        ctk.CTkButton(row1_frame, text="↻ 刷新", height=32, width=60, fg_color=THEME["bg_card"], hover_color="gray40", command=lambda: self.refresh_keys(None)).pack(side="left", padx=2)

        # 列表區
        self.key_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent", label_text="金鑰列表", label_font=("Microsoft JhengHei UI", 14, "bold"))
        self.key_scroll.grid(row=2, column=0, sticky="nsew")
        self.refresh_keys(None)

    def generate_key(self):
        hwid = self.hwid_ent.get().strip()
        name = self.user_name_ent.get().strip()
        raw_contact = self.contact_ent.get().strip()
        platform = self.platform_var.get()

        if not hwid: return messagebox.showwarning("提示", "請輸入機器碼")
        if not name: name = "未命名用戶"
        
        if not raw_contact: 
            contact_final = "--"
        else:
            contact_final = f"[{platform}] {raw_contact}"

        try:
            dur_map = {"1天": 1, "1週": 7, "1個月": 30, "1季": 90, "1年": 365, "永久": 36500}
            new_key = "PROV1-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            expiry = (datetime.now() + timedelta(days=dur_map.get(self.dur_var.get(), 30))).strftime("%Y-%m-%d %H:%M:%S")
            
            gist = GitHubManager.get_gist()
            if gist:
                data = json.loads(gist['files']['keys.json']['content']) if gist['files']['keys.json']['content'] else {}
                
                data[new_key] = {
                    "hwid": hwid, 
                    "expiry": expiry,
                    "name": name,
                    "contact": contact_final 
                }
                
                if GitHubManager.update_file("keys.json", data):
                    self.clipboard_clear(); self.clipboard_append(new_key)
                    messagebox.showinfo("成功", f"金鑰已生成:\n{new_key}\n\n(已複製)")
                    self.hwid_ent.delete(0, 'end')
                    self.refresh_keys(local_data=data)
                else: messagebox.showerror("錯誤", "寫入失敗")
        except Exception as e: messagebox.showerror("錯誤", str(e))

    def refresh_keys(self, local_data=None):
        if local_data is None:
            gist = GitHubManager.get_gist()
            if not gist: return
            try:
                content = gist['files']['keys.json']['content']
                data = json.loads(content) if content else {}
            except: return
        else:
            data = local_data

        for w in self.key_scroll.winfo_children(): w.destroy()
        now = datetime.now()
        
        total = len(data)
        active = sum(1 for v in data.values() if self.parse_expiry(v['expiry']) > now)
        self.lbl_total.configure(text=f"總金鑰: {total}")
        self.lbl_active.configure(text=f"活躍中: {active}")

        h = ctk.CTkFrame(self.key_scroll, fg_color="transparent", height=25)
        h.pack(fill="x", pady=(0,5))
        ctk.CTkLabel(h, text="狀態", width=40).pack(side="left")
        ctk.CTkLabel(h, text="用戶名稱", width=100, anchor="w", font=("", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h, text="聯絡方式", width=130, anchor="w", font=("", 11, "bold")).pack(side="left")
        ctk.CTkLabel(h, text="金鑰代碼", width=200, anchor="w").pack(side="left")
        ctk.CTkLabel(h, text="到期日", width=100, anchor="w").pack(side="left")

        for k, v in reversed(list(data.items())):
            try:
                exp = self.parse_expiry(v['expiry'])
                is_exp = now > exp
                col = THEME["bg_card"]
                
                row = ctk.CTkFrame(self.key_scroll, fg_color=col, corner_radius=6, height=40) 
                row.pack(fill="x", pady=3)
                
                st_col = "gray" if is_exp else THEME["success"]
                ctk.CTkLabel(row, text="●", text_color=st_col, width=40).pack(side="left")
                
                u_name = v.get('name', '--')
                u_cont = v.get('contact', '--')
                
                ctk.CTkLabel(row, text=u_name[:10], width=100, anchor="w", font=("Microsoft JhengHei UI", 12), text_color="#fff").pack(side="left")
                ctk.CTkLabel(row, text=u_cont[:18], width=130, anchor="w", font=("Arial", 11), text_color=THEME["text_sub"]).pack(side="left")
                
                ctk.CTkLabel(row, text=k, width=200, anchor="w", font=("Consolas", 12, "bold"), text_color="#fff" if not is_exp else "gray").pack(side="left")
                
                display_date = v['expiry'].split()[0] if " " in v['expiry'] else v['expiry']
                ctk.CTkLabel(row, text=display_date, width=100, anchor="w", text_color=THEME["danger"] if is_exp else "gray").pack(side="left")
                
                ctk.CTkButton(row, text="刪除", width=60, height=28, 
                              fg_color=THEME["danger"], hover_color=THEME["danger_hover"],
                              text_color="white", font=("Microsoft JhengHei UI", 12, "bold"),
                              command=lambda x=k: self.delete_key(x)).pack(side="right", padx=(5, 10))
                
                ctk.CTkButton(row, text="複製", width=60, height=28, 
                              fg_color=THEME["accent"], hover_color=THEME["accent_hover"],
                              text_color="white", font=("Microsoft JhengHei UI", 12, "bold"),
                              command=lambda x=k: [self.clipboard_clear(), self.clipboard_append(x)]).pack(side="right", padx=5)

            except: continue

    def delete_key(self, key):
        if messagebox.askyesno("確認", "確定刪除此金鑰？\n\n注意：用戶將在幾分鐘內被系統強制登出。"):
            # 這裡使用線程防止卡頓
            threading.Thread(target=self._delete_key_thread, args=(key,), daemon=True).start()

    def _delete_key_thread(self, key):
        gist = GitHubManager.get_gist()
        if gist:
            data = json.loads(gist['files']['keys.json']['content'])
            if key in data:
                del data[key]
                if GitHubManager.update_file("keys.json", data):
                    # 完成後在主線程刷新 UI
                    self.after(0, lambda: self.refresh_keys(local_data=data))
                    self.after(0, lambda: messagebox.showinfo("成功", "金鑰已刪除"))

    def setup_msgs_frame(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent"); self.frames["msgs"] = f
        f.grid_columnconfigure(0, weight=1); f.grid_rowconfigure(1, weight=1)
        
        h = ctk.CTkFrame(f, fg_color="transparent", height=40)
        h.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(h, text="訊息中心", font=("Microsoft JhengHei UI", 16, "bold")).pack(side="left")
        ctk.CTkButton(h, text="↻ 刷新列表", width=100, height=30, fg_color=THEME["bg_card"], command=self.refresh_msgs).pack(side="right")
        
        self.msg_scroll = ctk.CTkScrollableFrame(f, fg_color="transparent")
        self.msg_scroll.grid(row=1, column=0, sticky="nsew", pady=10)

    def refresh_msgs(self):
        for w in self.msg_scroll.winfo_children(): w.destroy()
        
        # 顯示讀取中...
        loading_lbl = ctk.CTkLabel(self.msg_scroll, text="正在載入訊息...", text_color="gray")
        loading_lbl.pack(pady=20)
        
        # 開啟線程讀取訊息
        threading.Thread(target=self._load_msgs_thread, args=(loading_lbl,), daemon=True).start()

    def _load_msgs_thread(self, loading_lbl):
        gist = GitHubManager.get_gist()
        
        # UI 更新必須回到主線程
        self.after(0, lambda: self._render_msgs(gist, loading_lbl))

    def _render_msgs(self, gist, loading_lbl):
        loading_lbl.destroy()
        if not gist: return
        
        try:
            msgs = json.loads(gist['files']['messages.json']['content']) if gist['files']['messages.json']['content'] else []
            if not msgs:
                ctk.CTkLabel(self.msg_scroll, text="目前沒有新訊息", text_color="gray").pack(pady=20)
                return

            # 使用 enumerate 獲取原始索引，列表反轉顯示
            for original_index, m in reversed(list(enumerate(msgs))):
                card = ctk.CTkFrame(self.msg_scroll, fg_color=THEME["bg_sidebar"], corner_radius=8)
                card.pack(fill="x", pady=5, padx=5)
                
                # 上半部：資訊列
                top = ctk.CTkFrame(card, fg_color="transparent", height=30)
                top.pack(fill="x", padx=12, pady=(8,0))
                
                ctk.CTkLabel(top, text=f"{m.get('contact','?')}", font=("Microsoft JhengHei UI", 13, "bold"), text_color="#fff").pack(side="left")
                ctk.CTkLabel(top, text=f"  [{m.get('method','?')}]", font=("Arial", 11), text_color=THEME["accent"]).pack(side="left")
                ctk.CTkLabel(top, text=m.get('time',''), text_color="gray", font=("Arial", 11)).pack(side="right", padx=(0, 10))

                # 內容區
                content_box = ctk.CTkFrame(card, fg_color=THEME["bg_main"], corner_radius=6)
                content_box.pack(fill="x", padx=12, pady=8)
                ctk.CTkLabel(content_box, text=m.get('content',''), justify="left", anchor="w", text_color="#ddd", font=("Microsoft JhengHei UI", 12), wraplength=600).pack(padx=10, pady=8, fill="x")

                # 底部：刪除按鈕 (優化版)
                # 使用紅色按鈕，不僅僅是圖示，增加可點擊區域和視覺回饋
                btn_del = ctk.CTkButton(top, text="🗑️ 刪除訊息", width=90, height=24, 
                                      fg_color=THEME["danger"], hover_color=THEME["danger_hover"],
                                      font=("Microsoft JhengHei UI", 11, "bold"),
                                      command=lambda idx=original_index, f=card: self.delete_msg(idx, f))
                btn_del.pack(side="right", padx=5)

        except Exception as e:
            print(e)

    def delete_msg(self, index, card_frame):
        if not messagebox.askyesno("刪除確認", "確定要永久刪除這則訊息嗎？"):
            return

        # 1. 優化體驗：先在 UI 上隱藏該卡片 (Optimistic UI Update)
        # 讓使用者感覺是「秒刪」，實際上後台在處理
        card_frame.destroy()

        # 2. 開啟線程處理網絡請求，避免卡頓
        threading.Thread(target=self._delete_msg_thread, args=(index,), daemon=True).start()

    def _delete_msg_thread(self, index):
        gist = GitHubManager.get_gist()
        if gist:
            try:
                msgs = json.loads(gist['files']['messages.json']['content'])
                # 再次確認索引有效，因為 Gist 可能變動
                if 0 <= index < len(msgs):
                    del msgs[index]
                    if not GitHubManager.update_file("messages.json", msgs):
                        # 如果失敗，彈窗提示（極少發生）
                        self.after(0, lambda: messagebox.showerror("錯誤", "同步失敗，請刷新列表"))
                else:
                    self.after(0, lambda: messagebox.showerror("錯誤", "訊息索引過期，請刷新列表"))
            except: 
                self.after(0, lambda: messagebox.showerror("錯誤", "系統錯誤"))

    def setup_settings_frame(self):
        f = ctk.CTkFrame(self.content_area, fg_color="transparent"); self.frames["settings"] = f
        ctk.CTkLabel(f, text="參數配置", font=("Microsoft JhengHei UI", 16, "bold")).pack(anchor="w", pady=(0, 15))
        card = ctk.CTkFrame(f, fg_color=THEME["bg_sidebar"], corner_radius=8)
        card.pack(fill="x")

        self.add_setting(card, 0, "版本號 (Version):", "ver_ent")
        self.add_setting(card, 1, "下載連結 (URL):", "url_ent")
        self.add_setting(card, 2, "Discord 連結:", "dc_ent")
        # 保留修正後的變數名
        self.add_setting(card, 3, "客服文字:", "cfg_contact_ent")

        ctk.CTkButton(f, text="儲存設定", height=40, fg_color=THEME["accent"], font=("", 13, "bold"), command=self.save_settings).pack(fill="x", pady=15)
        self.load_settings_ui()

    def add_setting(self, parent, row, label, attr):
        ctk.CTkLabel(parent, text=label, anchor="e").grid(row=row, column=0, padx=15, pady=10, sticky="e")
        ent = ctk.CTkEntry(parent, height=32, fg_color=THEME["bg_main"], border_color=THEME["bg_card"])
        ent.grid(row=row, column=1, padx=(0, 15), pady=10, sticky="ew")
        parent.grid_columnconfigure(1, weight=1)
        setattr(self, attr, ent)

    def load_settings_ui(self):
        gist = GitHubManager.get_gist()
        if gist:
            try:
                cfg = json.loads(gist['files']['config.json']['content'])
                self.ver_ent.insert(0, cfg.get("version", "1.0"))
                self.url_ent.insert(0, cfg.get("download_url", ""))
                self.dc_ent.insert(0, cfg.get("discord_link", ""))
                self.cfg_contact_ent.insert(0, cfg.get("contact_info", ""))
            except: pass

    def save_settings(self):
        cfg = {"version": self.ver_ent.get(), "download_url": self.url_ent.get(), "discord_link": self.dc_ent.get(), "contact_info": self.cfg_contact_ent.get()}
        if GitHubManager.update_file("config.json", cfg): messagebox.showinfo("成功", "已儲存")
        else: messagebox.showerror("錯誤", "儲存失敗")

if __name__ == "__main__":
    AdminApp().mainloop()