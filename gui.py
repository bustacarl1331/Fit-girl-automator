import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
import threading
import time
import os
from downloader import FitGirlDownloader
from history_manager import HistoryManager

# --- Windows 7 Style Constants ---
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 9)
BG_COLOR = "#F0F0F0"
WHITE_BG = "#FFFFFF"

def create_context_menu(widget):
    menu = Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    
    def do_popup(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    widget.bind("<Button-3>", do_popup)


class WizardApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FitGirl Repack Automator")
        self.geometry("600x480")
        self.resizable(False, False)
        
        # Set Icon if available (skip for now)
        
        self.downloader = None
        self.files_to_download = [] # List of dicts
        self.download_path = ""
        self.cancel_flag = False
        self.history_mgr = HistoryManager()
        self.current_url_key = None # To track which history item we are modifying
        
        # Main Container
        self.container = tk.Frame(self)

        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        for F in (InputPage, SelectionPage, ProgressPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
            
        self.show_frame("InputPage")
        
        # Check for browsers after loading UI to show status? 
        # Or just do it silently in background? 
        # Better: Do it on a thread so UI doesn't freeze.
        threading.Thread(target=self.ensure_browser_installed, daemon=True).start()
        
    def ensure_browser_installed(self):
        # We only really need chromium
        # Using programmatic install because subprocess fails in frozen EXE
        from playwright.__main__ import main as playwright_main
        import sys
        
        try:
             print("Checking/Installing Chromium...")
             # playwright_main will try to exit system processing, we must catch it
             try:
                 # Backup argv
                 old_argv = sys.argv
                 sys.argv = ["playwright", "install", "chromium"]
                 playwright_main()
             except SystemExit:
                 pass
             finally:
                 sys.argv = old_argv
                 print("Browser check complete.")
                 
        except Exception as e:
             print(f"Browser check failed: {e}")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()
        if hasattr(frame, "on_show"):
            frame.on_show()

class InputPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=WHITE_BG)
        
        # Header Image Area (Left Side) - Mocking the installer look
        # Use Canvas for a styled vertical banner
        self.side_bar = tk.Canvas(self, bg="#4A90E2", width=160, highlightthickness=0)
        self.side_bar.pack(side="left", fill="y")
        
        # Add decorative text to sidebar
        self.side_bar.create_text(80, 50, text="FitGirl", fill="white", font=("Segoe UI", 24, "bold"))
        self.side_bar.create_text(80, 85, text="Repack", fill="white", font=("Segoe UI", 24, "bold"))
        self.side_bar.create_text(80, 120, text="Automator", fill="#AED6F1", font=("Segoe UI", 16, "italic"))
        
        # User Guide Prompt
        self.side_bar.create_text(80, 280, text="Created by:\nAlbert Shony", fill="#AED6F1", font=("Segoe UI", 7, "bold"), justify="center")
        self.side_bar.create_text(80, 310, text="albertshony@gmail.com", fill="#AED6F1", font=("Segoe UI", 7), justify="center")
        
        self.side_bar.create_text(80, 380, text="First time users?\nPlease read the Guide!", fill="#E0E0E0", font=("Segoe UI", 9, "italic"), justify="center")
        
        # User Guide Button (Bottom of Sidebar)
        self.help_btn = tk.Button(self.side_bar, text="User Guide", command=self.open_help, bg="#4A90E2", fg="white", activebackground="#357ABD", activeforeground="white", relief="flat", font=("Segoe UI", 9, "underline"), cursor="hand2")
        self.side_bar.create_window(80, 420, window=self.help_btn, anchor="center") # Position near bottom

        
        # Content Area
        self.content = tk.Frame(self, bg=WHITE_BG)
        self.content.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        tk.Label(self.content, text="Welcome to the Automator", font=("Segoe UI", 16, "bold"), bg=WHITE_BG).pack(anchor="w", pady=(0, 2))
        tk.Label(self.content, text="(Exclusive for 'FuckingFast.co' mirrors)", font=("Segoe UI", 8, "italic"), fg="#555555", bg=WHITE_BG).pack(anchor="w", pady=(0, 10))
        tk.Label(self.content, text="Please enter the FitGirl Repack Game URL below.", font=FONT_NORMAL, bg=WHITE_BG).pack(anchor="w")
        
        tk.Label(self.content, text="Game URL:", font=("Segoe UI", 9, "bold"), bg=WHITE_BG).pack(anchor="w", pady=(20, 5))


        self.url_entry = tk.Entry(self.content, width=45, font=FONT_NORMAL)
        self.url_entry.pack(anchor="w")
        # self.url_entry.insert(0, "") # Blank by default
        create_context_menu(self.url_entry)

        
        self.status_lbl = tk.Label(self.content, text="", fg="blue", bg=WHITE_BG, font=FONT_NORMAL)
        self.status_lbl.pack(anchor="w", pady=10)

        # History / Resume Section
        tk.Label(self.content, text="Resume / History:", font=("Segoe UI", 9, "bold"), bg=WHITE_BG).pack(anchor="w", pady=(10, 5))
        
        hist_frame = tk.Frame(self.content, bg=WHITE_BG)
        hist_frame.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(hist_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.history_list = tk.Listbox(hist_frame, height=5, font=("Segoe UI", 8), yscrollcommand=scrollbar.set)
        self.history_list.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_list.yview)
        self.history_list.bind('<<ListboxSelect>>', self.on_history_select)
        
        # History Buttons
        h_btn_frame = tk.Frame(self.content, bg=WHITE_BG)
        h_btn_frame.pack(fill="x", pady=5)
        ttk.Button(h_btn_frame, text="Delete Entry", command=self.delete_history).pack(side="right")
        
        # Bottom Buttons
        self.btn_frame = tk.Frame(self.content, bg=WHITE_BG)
        self.btn_frame.pack(side="bottom", fill="x", pady=10)
        
        self.next_btn = ttk.Button(self.btn_frame, text="Next >", command=self.fetch_info)
        self.next_btn.pack(side="right")

    def on_show(self):
        self.refresh_history()

    def refresh_history(self):
        self.history_list.delete(0, tk.END)
        self.history_items = self.controller.history_mgr.get_all_sorted() # List of (url, data)
        for url, data in self.history_items:
            # Show game name if possible, else URL
            name = url.split('/')[-2] if url.split('/')[-2] else url
            self.history_list.insert(tk.END, f"{name}  [{data.get('path')}]")

    def on_history_select(self, event):
        sel = self.history_list.curselection()
        if sel:
            idx = sel[0]
            url, _ = self.history_items[idx]
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

    def delete_history(self):
        sel = self.history_list.curselection()
        if sel:
            idx = sel[0]
            url, _ = self.history_items[idx]
            if self.controller.history_mgr.delete_entry(url):
                self.refresh_history()
                self.url_entry.delete(0, tk.END)

    def open_help(self):
        UserGuideWindow(self)

    def fetch_info(self):
        url = self.url_entry.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        self.status_lbl.config(text="Fetching file information... Please wait.")
        self.next_btn.config(state="disabled")
        self.update()
        
        def run_fetch():
            try:
                self.controller.downloader = FitGirlDownloader(url)
                files = self.controller.downloader.fetch_files_info()
                
                if not files:
                     self.controller.after(0, lambda: messagebox.showerror("Error", "No 'FuckingFast' links found."))
                     self.controller.after(0, lambda: self.reset_ui())
                     return
                
                self.controller.files_info = files
                self.controller.after(0, lambda: self.controller.show_frame("SelectionPage"))
                self.controller.after(0, lambda: self.reset_ui())
                
            except Exception as e:
                print(e)
                self.controller.after(0, lambda: messagebox.showerror("Error", str(e)))
                self.controller.after(0, lambda: self.reset_ui())

        threading.Thread(target=run_fetch, daemon=True).start()

    def reset_ui(self):
        self.status_lbl.config(text="")
        self.next_btn.config(state="normal")


class SelectionPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=BG_COLOR)
        
        # Top Header
        header_frame = tk.Frame(self, bg=WHITE_BG, height=60)
        header_frame.pack(side="top", fill="x")
        tk.Label(header_frame, text="Select Components", font=FONT_HEADER, bg=WHITE_BG).pack(anchor="w", padx=20, pady=5)
        tk.Label(header_frame, text="Which parts of the game do you want to download?", font=FONT_NORMAL, bg=WHITE_BG).pack(anchor="w", padx=20)
        
        # Content Container (Middle)
        content_frame = tk.Frame(self, bg=BG_COLOR)
        content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # Bottom Buttons (Pack FIRST at bottom to ensure visibility)
        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        ttk.Button(btn_frame, text="< Back", command=lambda: controller.show_frame("InputPage")).pack(side="left")
        ttk.Button(btn_frame, text="Download >", command=self.start_download).pack(side="right")
        
        # --- Now fill Content Frame ---
        
        # Path Selector
        path_frame = tk.Frame(content_frame, bg=BG_COLOR)
        path_frame.pack(fill="x", pady=(0, 5))
        tk.Label(path_frame, text="Destination Folder:", bg=BG_COLOR).pack(side="left")
        self.path_entry = tk.Entry(path_frame)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.path_entry.insert(0, os.getcwd())
        ttk.Button(path_frame, text="Browse...", command=self.browse_path).pack(side="left")
        
        # Subfolder Option
        self.subfolder_var = tk.BooleanVar(value=True)
        tk.Checkbutton(content_frame, text="Create new subfolder for game", variable=self.subfolder_var, bg=BG_COLOR).pack(anchor="w", pady=(0, 10))
        
        # Checkbox List
        tk.Label(content_frame, text="Files:", bg=BG_COLOR).pack(anchor="w")
        
        list_frame = tk.Frame(content_frame, bg="white", relief="sunken", bd=1)
        list_frame.pack(fill="both", expand=True) # This will take remaining space
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas = tk.Canvas(list_frame, bg="white", yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.canvas.yview)
        
        self.check_frame = tk.Frame(self.canvas, bg="white")
        self.canvas.create_window((0,0), window=self.check_frame, anchor="nw")
        
        # Scroll binding
        self.check_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.check_vars = []

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def on_show(self):
        # Clear old checkboxes
        for widget in self.check_frame.winfo_children():
            widget.destroy()

        self.check_vars = []
        
        files = getattr(self.controller, 'files_info', [])
        
        # Check history for this URL
        current_url = self.controller.downloader.game_url
        history_entry = self.controller.history_mgr.get_entry(current_url)
        previously_selected = history_entry.get('selected_files', []) if history_entry else []
        
        # If we have history, update path
        if history_entry and history_entry.get('path'):
             self.path_entry.delete(0, tk.END)
             self.path_entry.insert(0, history_entry['path'])
        
        # Categorize

        core_files = [f for f in files if f['type'] == 'core']
        selective_files = [f for f in files if f['type'] == 'selective']
        optional_files = [f for f in files if f['type'] == 'optional']
        
        # 1. Core Files
        # 1. Core Files
        if core_files:
            tk.Label(self.check_frame, text="Core Files:", font=("Segoe UI", 9, "bold"), bg="white", anchor="w").pack(fill="x", pady=(5, 2))
            for f in core_files:
                # Check history if previously selected, otherwise default True
                is_selected = True
                if previously_selected:
                     is_selected = f['name'] in previously_selected
                     
                var = tk.BooleanVar(value=is_selected)
                cb = tk.Checkbutton(self.check_frame, text=f['name'], variable=var, bg="white", anchor="w")
                cb.pack(fill="x", padx=10)
                self.check_vars.append((var, f))
                
        # 2. Selective Files
        if selective_files:
            tk.Label(self.check_frame, text="Selective Components (Pick at least one):", font=("Segoe UI", 9, "bold"), bg="white", anchor="w").pack(fill="x", pady=(10, 2))
            for f in selective_files:
                # Pre-select if in history, or default false
                is_selected = f['name'] in previously_selected if previously_selected else False
                var = tk.BooleanVar(value=is_selected)
                cb = tk.Checkbutton(self.check_frame, text=f['name'], variable=var, bg="white", anchor="w")
                cb.pack(fill="x", padx=10)
                self.check_vars.append((var, f))

        # 3. Optional Files
        if optional_files:
            tk.Label(self.check_frame, text="Optional Files:", font=("Segoe UI", 9, "bold"), bg="white", anchor="w").pack(fill="x", pady=(10, 2))
            for f in optional_files:
                # Pre-select if in history, or default false
                is_selected = f['name'] in previously_selected if previously_selected else False
                var = tk.BooleanVar(value=is_selected)
                cb = tk.Checkbutton(self.check_frame, text=f['name'], variable=var, bg="white", anchor="w", fg="gray")
                cb.pack(fill="x", padx=10)
                self.check_vars.append((var, f))

            
    def browse_path(self):
        d = filedialog.askdirectory()
        if d:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, d)
            
    def start_download(self):
        selected_files = [f for var, f in self.check_vars if var.get()]
        
        # Validation
        files = getattr(self.controller, 'files_info', [])
        selective_available = any(f['type'] == 'selective' for f in files)
        
        if selective_available:
            selected_selective = [f for f in selected_files if f['type'] == 'selective']
            if not selected_selective:
                messagebox.showwarning("Selection Error", "This game has selective components (e.g. language files).\nPlease select at least one.")
                return

        if not selected_files:
            messagebox.showwarning("Warning", "No files selected!")
            return
        
        self.controller.files_to_download = selected_files
        self.controller.download_path = self.path_entry.get()
        self.controller.create_subfolder = self.subfolder_var.get()
        
        # Save to History
        selected_names = [f['name'] for f in selected_files]
        self.controller.history_mgr.add_or_update(
             self.controller.downloader.game_url,
             self.controller.download_path,
             selected_names
        )
        
        self.controller.show_frame("ProgressPage")




class ProgressPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=BG_COLOR)
        
        # Top Header (Like Installing...)
        header_frame = tk.Frame(self, bg=WHITE_BG, height=60)
        header_frame.pack(side="top", fill="x")
        # Optional: Add an image here like the meme/girl one if user wants
        
        tk.Label(header_frame, text="Installing", font=FONT_HEADER, bg=WHITE_BG).pack(anchor="w", padx=20, pady=5)
        self.sub_header = tk.Label(header_frame, text="Please wait while the automator downloads files...", font=FONT_NORMAL, bg=WHITE_BG)
        self.sub_header.pack(anchor="w", padx=20)
        
        # Content
        content_frame = tk.Frame(self, bg=BG_COLOR)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.status_action = tk.Label(content_frame, text="Preparing...", font=("Segoe UI", 9), bg=BG_COLOR)
        self.status_action.pack(anchor="w")
        
        self.current_file_lbl = tk.Label(content_frame, text="", font=("Segoe UI", 9, "bold"), bg=BG_COLOR)
        self.current_file_lbl.pack(anchor="w", pady=(0, 10))
        
        # Download Progress Bar (Green)
        self.progress_var = tk.DoubleVar()
        style = ttk.Style()
        style.theme_use('default')
        style.configure("green.Horizontal.TProgressbar", background="#00AA00")
        self.pbar = ttk.Progressbar(content_frame, style="green.Horizontal.TProgressbar", variable=self.progress_var, maximum=100)
        
        # Resolution Progress Bar (Indeterminate Blue)
        self.resolve_pbar = ttk.Progressbar(content_frame, mode='indeterminate')
        
        # Initial pack
        self.resolve_pbar.pack(fill="x", pady=5)
        
        # Stats (Time, etc) - Container to hide/show easily
        self.stats_frame = tk.Frame(content_frame, bg=BG_COLOR)
        self.percent_lbl = tk.Label(self.stats_frame, text="0.0%", bg=BG_COLOR, font=FONT_NORMAL)
        self.percent_lbl.pack(side="right")
        self.time_lbl = tk.Label(self.stats_frame, text="Elapsed: 00:00:00", bg=BG_COLOR, font=FONT_NORMAL)
        self.time_lbl.pack(anchor="w", pady=10)
        
        # Tip Label
        tk.Label(content_frame, text="Tip: If download gets stuck -> Click Cancel, then Start Again. It will Resume!", fg="gray", font=("Segoe UI", 8, "italic"), bg=BG_COLOR).pack(anchor="w", pady=(5,0))

        # Overall Progress
        tk.Label(content_frame, text="Total Progress:", bg=BG_COLOR, font=("Segoe UI", 8)).pack(anchor="w", pady=(20, 0))


        self.total_var = tk.DoubleVar()
        self.total_pbar = ttk.Progressbar(content_frame, variable=self.total_var, maximum=100)
        self.total_pbar.pack(fill="x")
        
        # Bottom Buttons
        btn_frame = tk.Frame(self, bg=BG_COLOR)
        btn_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        self.cancel_btn = ttk.Button(btn_frame, text="Cancel", command=self.cancel_download)
        self.cancel_btn.pack(side="right")

    def on_show(self):
        self.start_download_thread()
        
    def cancel_download(self):
        if messagebox.askyesno("Cancel", "Are you sure you want to cancel?"):
            self.controller.cancel_flag = True
            self.controller.show_frame("InputPage")

    def start_download_thread(self):
        self.controller.cancel_flag = False
        threading.Thread(target=self.run_download, daemon=True).start()
        # Timer state
        self.is_downloading_active = False
        self.elapsed_seconds = 0
        self.update_timer()

    def update_timer(self):
        if self.controller.cancel_flag:
            return
        
        if self.is_downloading_active:
            self.elapsed_seconds += 1
            el_str = time.strftime('%H:%M:%S', time.gmtime(self.elapsed_seconds))
            self.time_lbl.config(text=f"Elapsed: {el_str}")
            
        self.after(1000, self.update_timer)

    def set_ui_resolving(self):
        self.pbar.pack_forget()
        self.stats_frame.pack_forget()
        self.resolve_pbar.pack(fill="x", pady=5)
        self.resolve_pbar.start(10)
        self.is_downloading_active = False

    def set_ui_downloading(self):
        self.resolve_pbar.stop()
        self.resolve_pbar.pack_forget()
        self.pbar.pack(fill="x", pady=5)
        self.stats_frame.pack(fill="x")
        self.is_downloading_active = True

    def run_download(self):
        files = self.controller.files_to_download

        base_path = self.controller.download_path
        
        # Create Game Folder
        # Get game name from URL or use default
        try:
            if getattr(self.controller, 'create_subfolder', True):
                game_name = self.controller.downloader.game_url.rstrip('/').split('/')[-1]
                full_path = os.path.join(base_path, game_name)
                if not os.path.exists(full_path):
                    os.makedirs(full_path)
            else:
                full_path = base_path
                # Still ensure base path exists
                if not os.path.exists(full_path):
                    os.makedirs(full_path)
            
            # Switch to that dir? Or just write to absolute path
            # Let's use absolute paths
        except:
             full_path = base_path
        
        total_files = len(files)
        failed_files = []
        
        for i, file_info in enumerate(files):
            if self.controller.cancel_flag:
                break
                
            file_url = file_info['url']
            original_name = file_info['name']
            
            save_path = os.path.join(full_path, original_name)
            
            # UI Update
            self.total_var.set((i / total_files) * 100)
            self.status_action.config(text=f"Resolving link ({i+1}/{total_files})...")
            self.current_file_lbl.config(text=original_name)
            self.progress_var.set(0)
            
            # 1. Resolve Link (UI Mode: Resolving)
            self.set_ui_resolving()
            direct_url = self.controller.downloader.resolve_single_link_playwright(file_url)
            
            if not direct_url:
                print(f"Failed to resolve {original_name}")
                failed_files.append(original_name)
                continue
                
            # 2. Download (UI Mode: Downloading)
            self.set_ui_downloading()
            self.status_action.config(text="Downloading...")
            
            success = self.controller.downloader.download_file(
                direct_url, 
                save_path, 
                progress_callback=self.progress_update,
                check_cancel=lambda: self.controller.cancel_flag
            )
            
            if not success:
                print(f"Failed to download {original_name}")
                failed_files.append(original_name)
        
        if not self.controller.cancel_flag:
            self.total_var.set(100)
            self.set_ui_resolving() # Stop green bar
            self.resolve_pbar.stop()
            
            if failed_files:
                self.status_action.config(text="Completed with Errors", fg="red")
                self.current_file_lbl.config(text=f"Failed: {len(failed_files)} files. Check log.")
                messagebox.showwarning("Download Issues", f"The following files failed to download:\n\n" + "\n".join(failed_files[:5]) + ("\n..." if len(failed_files)>5 else ""))
            else:
                self.status_action.config(text="Done!", fg="green")
                self.current_file_lbl.config(text="All files downloaded successfully.")
                
            self.cancel_btn.config(text="Close", command=self.controller.destroy)
        else:
             self.resolve_pbar.stop()


    def progress_update(self, current, total):
        # Update progress bar
        if total > 0:
            pct = (current / total) * 100
            self.progress_var.set(pct)
            self.percent_lbl.config(text=f"{pct:.1f}%")

class UserGuideWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("User Guide")
        self.geometry("500x500")
        self.configure(bg=WHITE_BG)
        
        # Scrollable Text
        frame = tk.Frame(self, bg=WHITE_BG)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")
        
        text_area = tk.Text(frame, font=("Segoe UI", 10), wrap="word", yscrollcommand=scrollbar.set, relief="flat", padx=10, pady=10)
        text_area.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_area.yview)
        
        guide_text = """FITGIRL AUTOMATOR - USER GUIDE

*IMPORTANT*: This tool automates the "FuckingFast" mirror links ONLY. 
Please ensure the game page you are using has this mirror option available.

1. QUICK START
------------------
- Copy the Game URL from FitGirl's site.
- Paste it into the "Game URL" box.
- Click "Next".
- Select your files (Core files are required).
- Click "Download".

2. FEATURES
------------------
- Smart History: Your downloads are saved. Click an entry in the "Resume / History" list to restore your settings.
- Selective Audio: You must pick at least one "Selective" file (like English Audio) if the game demands it.
- Auto-Repair: If a download stops, just run the app again with the same settings. It will verify existing files and only download missing parts.

3. TROUBLESHOOTING
------------------
- "Resolving Links" Freeze: The app opens a hidden browser to bypass ads. First time run might be slow as it installs browsers.
- Network Errors: The app automatically retries failed chunks.
- Stopping: You can click Cancel anytime. It is safe to resume later.

4. TIPS
------------------
- Use Right-Click to Paste URLs.
- Use your Mouse Wheel to scroll the file list.
- Check "Optional" files only if you really want them (credits, bonus OSTs, etc).
"""
        text_area.insert(tk.END, guide_text)
        text_area.config(state="disabled") # Read-only
        
        ttk.Button(self, text="Close", command=self.destroy).pack(pady=10)

if __name__ == "__main__":
    app = WizardApp()
    app.mainloop()

