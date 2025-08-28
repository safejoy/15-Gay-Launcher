import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
import json
import os
import threading
import time
from pathlib import Path
from PIL import Image, ImageTk
import pygame
import requests

class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, corner_radius, padding, color, bg, command=None, text="", font=("Arial", 9)):
        tk.Canvas.__init__(self, parent, borderwidth=0, relief="flat", highlightthickness=0, width=width, height=height, bg=bg)
        self.command = command
        self.padding = padding
        self.color = color
        self.bg = bg
        self.corner_radius = corner_radius
        self.text = text
        self.font = font
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self.create_rounded_rect()
        
    def create_rounded_rect(self, fill_color=None):
        self.delete("all")
        if fill_color is None:
            fill_color = self.color
            
        # Create rounded rectangle
        x1, y1 = 0, 0
        x2, y2 = self.winfo_reqwidth(), self.winfo_reqheight()
        
        # Draw corners
        self.create_arc(x1, y1, x1 + 2*self.corner_radius, y1 + 2*self.corner_radius, 
                       start=90, extent=90, fill=fill_color, outline=fill_color)
        self.create_arc(x2 - 2*self.corner_radius, y1, x2, y1 + 2*self.corner_radius,
                       start=0, extent=90, fill=fill_color, outline=fill_color)
        self.create_arc(x1, y2 - 2*self.corner_radius, x1 + 2*self.corner_radius, y2,
                       start=180, extent=90, fill=fill_color, outline=fill_color)
        self.create_arc(x2 - 2*self.corner_radius, y2 - 2*self.corner_radius, x2, y2,
                       start=270, extent=90, fill=fill_color, outline=fill_color)
        
        # Draw rectangles
        self.create_rectangle(x1 + self.corner_radius, y1, x2 - self.corner_radius, y2, 
                            fill=fill_color, outline=fill_color)
        self.create_rectangle(x1, y1 + self.corner_radius, x2, y2 - self.corner_radius,
                            fill=fill_color, outline=fill_color)
        
        # Add text
        if self.text:
            self.create_text(self.winfo_reqwidth()//2, self.winfo_reqheight()//2,
                           text=self.text, fill="white", font=self.font, anchor="center")
        
    def _on_click(self, event):
        if self.command:
            self.command()
    
    def _on_enter(self, event):
        self.create_rounded_rect("#5a7751")
        
    def _on_leave(self, event):
        self.create_rounded_rect()

class GameLauncher:
    def __init__(self):
        self.config_file = "settings.json"
        self.games_file = "games.json"
        self.ads_file = "ads.json"
        self.ads_folder = "ads"
        self.game_art_folder = "game_art"
        self.music_file = "launcher_music.mp3"
        self.discord_api_url = "https://discord.com/api/guilds/YOUR_GUILD_ID/widget.json"  # Replace with your Discord server ID
        self.current_game = None
        self.is_loading = False
        self.play_start_time = None
        self.current_ad_index = 0
        self.ad_images = []
        self.ad_links = []
        self.discord_members = "0"
        
        # Initialize pygame for music
        pygame.mixer.init()
        
        # Color schemes
        self.themes = {
            "dark": {
                "bg_primary": "#2c3e50",
                "bg_secondary": "#34495e", 
                "bg_content": "#ecf0f1",
                "fg_primary": "#ffffff",
                "fg_secondary": "#2c3e50",
                "accent": "#3498db",
                "success": "#27ae60",
                "danger": "#e74c3c",
                "hover": "#5a7751"
            },
            "light": {
                "bg_primary": "#f8f9fa",
                "bg_secondary": "#e9ecef",
                "bg_content": "#ffffff", 
                "fg_primary": "#2c3e50",
                "fg_secondary": "#495057",
                "accent": "#007bff",
                "success": "#28a745",
                "danger": "#dc3545",
                "hover": "#0056b3"
            }
        }
        
        # Initialize settings
        self.default_settings = {
            "sound": True,
            "theme": "dark",
            "play_time_tracking": True,
            "last_selected_game": None,
            "total_play_times": {}
        }
        
        # Default games configuration
        self.default_games = {
            "ace": {
                "name": "Ace Adventure",
                "description": "A thrilling adventure RPG with stunning visuals and engaging storyline.",
                "path": "Games/Ace/Game.exe",
                "version": "1.0.0",
                "enabled": True,
                "art": "ace.png"
            },
            "puzzle": {
                "name": "Puzzle Master", 
                "description": "Challenge your mind with increasingly difficult puzzles.",
                "path": "Games/Puzzle/Game.exe",
                "version": "0.8.5",
                "enabled": True,
                "art": "puzzle.png"
            },
            "platformer": {
                "name": "Jump Quest",
                "description": "A classic platformer with modern gameplay mechanics.",
                "path": "Games/Platformer/Game.exe",
                "version": "2.1.0",
                "enabled": True,
                "art": "platformer.png"
            }
        }
        
        self.setup_ui()
        self.load_settings()
        self.load_games()
        self.load_ads()
        self.apply_theme()
        self.start_music()
        self.start_ad_rotation()
        self.update_discord_count()
        self.show_home()
        
        # Select last played game or first available
        if self.settings.get("last_selected_game") and self.settings["last_selected_game"] in self.games:
            self.select_game(self.settings["last_selected_game"])
        else:
            # Select first enabled game
            for game_id, game_info in self.games.items():
                if game_info.get("enabled", True):
                    self.select_game(game_id)
                    break

    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("15 Gay Game Launcher")
        self.root.geometry("1920x1080")
        self.root.resizable(True, True)
        
        # Create main layout
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Ad banner area (320x50) - centered
        self.ad_frame = tk.Frame(self.main_frame, height=60)
        self.ad_frame.pack(fill="x", pady=(0, 15))
        self.ad_frame.pack_propagate(False)
        
        self.ad_label = tk.Label(self.ad_frame, text="Loading ads...", font=("Arial", 10), cursor="hand2")
        self.ad_label.pack(expand=True)
        self.ad_label.bind("<Button-1>", self.on_ad_click)
        
        # Content area frame
        self.content_wrapper = tk.Frame(self.main_frame)
        self.content_wrapper.pack(fill="both", expand=True)
        
        # Left sidebar for navigation
        self.nav_sidebar = tk.Frame(self.content_wrapper, width=200)
        self.nav_sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.nav_sidebar.pack_propagate(False)
        
        # Right sidebar for game selection  
        self.game_sidebar = tk.Frame(self.content_wrapper, width=300)
        self.game_sidebar.pack(side="right", fill="y", padx=(10, 0))
        self.game_sidebar.pack_propagate(False)
        
        # Content area
        self.content_frame = tk.Frame(self.content_wrapper)
        self.content_frame.pack(side="left", fill="both", expand=True, padx=10)
        
        # Loading bar frame (initially hidden)
        self.loading_frame = tk.Frame(self.main_frame)
        self.loading_label = tk.Label(self.loading_frame, text="Launching game...", font=("Arial", 12))
        self.loading_label.pack()
        self.loading_progress = ttk.Progressbar(self.loading_frame, mode='determinate', length=400)
        self.loading_progress.pack(pady=8)
        
        self.setup_navigation_sidebar()
        self.setup_game_sidebar()

    def setup_navigation_sidebar(self):
        # Settings cog at top
        settings_frame = tk.Frame(self.nav_sidebar)
        settings_frame.pack(pady=(0, 20))
        
        settings_btn = RoundedButton(settings_frame, 40, 40, 20, 5, "#6c757d", 
                                   self.themes[self.settings.get("theme", "dark")]["bg_secondary"],
                                   command=self.show_settings, text="⚙️", font=("Arial", 16))
        settings_btn.pack()
        
        # Navigation title
        self.nav_title = tk.Label(self.nav_sidebar, text="Navigation", font=("Arial", 14, "bold"))
        self.nav_title.pack(pady=(0, 15))
        
        # Navigation buttons frame
        nav_buttons_frame = tk.Frame(self.nav_sidebar)
        nav_buttons_frame.pack(fill="both", expand=True)
        
        self.nav_buttons = []
        buttons = [
            ("🏠 Home", self.show_home),
            ("📰 Announcements", self.show_announcements), 
            ("💝 Support Us", self.show_support),
            ("🌐 Studio Website", lambda: self.open_link("https://15.gay/")),
            ("☁️ BlueSky", lambda: self.open_link("https://bsky.app/profile/15gay.itch.io")),
            ("👾 Itch", lambda: self.open_link("https://15gay.itch.io/"))
        ]
        
        for text, command in buttons:
            btn_frame = tk.Frame(nav_buttons_frame)
            btn_frame.pack(fill="x", pady=3)
            
            btn = RoundedButton(btn_frame, 180, 35, 10, 5, "#4a6741", 
                              self.themes[self.settings.get("theme", "dark")]["bg_secondary"],
                              command=command, text=text, font=("Arial", 10))
            btn.pack()
            self.nav_buttons.append(btn)
        
        # Spacer to push exit button to bottom
        spacer = tk.Frame(nav_buttons_frame)
        spacer.pack(expand=True, fill="y")
        
        # Exit button at bottom
        exit_frame = tk.Frame(nav_buttons_frame)
        exit_frame.pack(pady=10)
        
        self.exit_btn = RoundedButton(exit_frame, 180, 40, 10, 5, "#dc3545", 
                                    self.themes[self.settings.get("theme", "dark")]["bg_secondary"],
                                    command=self.on_closing, text="🚪 Exit Launcher", font=("Arial", 10, "bold"))
        self.exit_btn.pack()

    def setup_game_sidebar(self):
        # Discord and games header
        header_frame = tk.Frame(self.game_sidebar)
        header_frame.pack(pady=(0, 15), fill="x")
        
        # Discord info
        discord_frame = tk.Frame(header_frame)
        discord_frame.pack()
        
        discord_btn = RoundedButton(discord_frame, 35, 35, 17, 3, "#7289da", 
                                  self.themes[self.settings.get("theme", "dark")]["bg_secondary"],
                                  command=lambda: self.open_link("https://discord.gg/YOUR_INVITE_CODE"), 
                                  text="💬", font=("Arial", 14))
        discord_btn.pack(side="left")
        
        self.discord_label = tk.Label(discord_frame, text=f"{self.discord_members} online", 
                                    font=("Arial", 10), fg="#7289da")
        self.discord_label.pack(side="left", padx=(8, 0), pady=8)
        
        # Games title
        self.games_title = tk.Label(self.game_sidebar, text="Available Games", font=("Arial", 14, "bold"))
        self.games_title.pack(pady=(10, 15))
        
        # Games grid container with scrollbar
        self.games_container = tk.Frame(self.game_sidebar)
        self.games_container.pack(fill="both", expand=True)
        
        self.games_canvas = tk.Canvas(self.games_container, highlightthickness=0)
        self.games_scrollbar = ttk.Scrollbar(self.games_container, orient="vertical", command=self.games_canvas.yview)
        self.games_scrollable_frame = tk.Frame(self.games_canvas)
        
        self.games_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.games_canvas.configure(scrollregion=self.games_canvas.bbox("all"))
        )
        
        self.games_canvas.create_window((0, 0), window=self.games_scrollable_frame, anchor="nw")
        self.games_canvas.configure(yscrollcommand=self.games_scrollbar.set)
        
        self.games_canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.games_scrollbar.pack(side="right", fill="y")

    def update_discord_count(self):
        """Update Discord member count"""
        def fetch_count():
            try:
                # Replace with your actual Discord server widget URL
                # For now, we'll use a placeholder
                self.discord_members = "42"  # Placeholder
                if hasattr(self, 'discord_label'):
                    self.discord_label.config(text=f"{self.discord_members} online")
            except:
                self.discord_members = "0"
        
        # Update every 5 minutes
        threading.Timer(300, self.update_discord_count).start()
        fetch_thread = threading.Thread(target=fetch_count, daemon=True)
        fetch_thread.start()

    def load_ads(self):
        """Load banner ad images and links from ads folder and JSON"""
        self.ad_images = []
        self.ad_links = []
        
        # Create directories if they don't exist
        if not os.path.exists(self.ads_folder):
            os.makedirs(self.ads_folder)
        
        # Load ad links from JSON
        ad_data = {}
        if os.path.exists(self.ads_file):
            try:
                with open(self.ads_file, "r") as f:
                    ad_data = json.load(f)
            except:
                pass
        
        # Default ad data if file doesn't exist
        if not ad_data:
            ad_data = {
                "default_ad.png": "https://15.gay/",
                "support_ad.png": "https://ko-fi.com/15gay"
            }
            with open(self.ads_file, "w") as f:
                json.dump(ad_data, f, indent=4)
        
        # Load images
        for filename in os.listdir(self.ads_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    image_path = os.path.join(self.ads_folder, filename)
                    img = Image.open(image_path)
                    # Resize to 320x50
                    img = img.resize((320, 50), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.ad_images.append(photo)
                    self.ad_links.append(ad_data.get(filename, "https://15.gay/"))
                except Exception as e:
                    print(f"Error loading ad image {filename}: {e}")
        
        if not self.ad_images:
            self.create_default_ad()

    def create_default_ad(self):
        """Create a default ad if no images are found"""
        img = Image.new('RGB', (320, 50), color='#3498db')
        photo = ImageTk.PhotoImage(img)
        self.ad_images.append(photo)
        self.ad_links.append("https://15.gay/")

    def on_ad_click(self, event):
        """Handle ad click to open link"""
        if self.ad_links and len(self.ad_links) > self.current_ad_index:
            self.open_link(self.ad_links[self.current_ad_index])

    def start_ad_rotation(self):
        """Start rotating ads every 5 seconds"""
        def rotate_ads():
            while True:
                if self.ad_images:
                    try:
                        self.ad_label.configure(image=self.ad_images[self.current_ad_index], text="")
                        self.current_ad_index = (self.current_ad_index + 1) % len(self.ad_images)
                    except:
                        pass
                time.sleep(5)
        
        ad_thread = threading.Thread(target=rotate_ads, daemon=True)
        ad_thread.start()

    def start_music(self):
        """Start playing background music if enabled"""
        if self.settings.get("sound", True) and os.path.exists(self.music_file):
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(0.3)
            except Exception as e:
                print(f"Could not play music: {e}")

    def stop_music(self):
        """Stop background music"""
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def apply_theme(self):
        """Apply the selected theme colors to all UI elements"""
        theme = self.themes[self.settings.get("theme", "dark")]
        
        # Main window and frames
        self.root.configure(bg=theme["bg_primary"])
        self.main_frame.configure(bg=theme["bg_primary"])
        self.content_wrapper.configure(bg=theme["bg_primary"])
        self.nav_sidebar.configure(bg=theme["bg_secondary"])
        self.game_sidebar.configure(bg=theme["bg_secondary"])
        self.content_frame.configure(bg=theme["bg_content"])
        self.ad_frame.configure(bg=theme["bg_primary"])
        self.loading_frame.configure(bg=theme["bg_primary"])
        
        # Labels
        if hasattr(self, 'nav_title'):
            self.nav_title.configure(bg=theme["bg_secondary"], fg=theme["fg_primary"])
        if hasattr(self, 'games_title'):
            self.games_title.configure(bg=theme["bg_secondary"], fg=theme["fg_primary"])
        if hasattr(self, 'games_canvas'):
            self.games_canvas.configure(bg=theme["bg_secondary"])
        if hasattr(self, 'games_scrollable_frame'):
            self.games_scrollable_frame.configure(bg=theme["bg_secondary"])
        if hasattr(self, 'ad_label'):
            self.ad_label.configure(bg=theme["bg_primary"], fg=theme["fg_primary"])
        if hasattr(self, 'loading_label'):
            self.loading_label.configure(bg=theme["bg_primary"], fg=theme["fg_primary"])
        if hasattr(self, 'discord_label'):
            self.discord_label.configure(bg=theme["bg_secondary"])

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    self.settings = json.load(f)
            except Exception:
                self.settings = self.default_settings.copy()
        else:
            self.settings = self.default_settings.copy()
        
        # Initialize tkinter variables
        self.sound_var = tk.BooleanVar(value=self.settings.get("sound", True))
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        self.play_time_var = tk.BooleanVar(value=self.settings.get("play_time_tracking", True))

    def load_games(self):
        if os.path.exists(self.games_file):
            try:
                with open(self.games_file, "r") as f:
                    self.games = json.load(f)
            except Exception:
                self.games = self.default_games.copy()
                self.save_games()
        else:
            self.games = self.default_games.copy()
            self.save_games()
        
        # Create game art folder if it doesn't exist
        if not os.path.exists(self.game_art_folder):
            os.makedirs(self.game_art_folder)
        
        self.update_game_sidebar()

    def save_settings(self):
        self.settings["sound"] = self.sound_var.get()
        self.settings["theme"] = self.theme_var.get()
        self.settings["play_time_tracking"] = self.play_time_var.get()
        if self.current_game:
            self.settings["last_selected_game"] = self.current_game
        
        with open(self.config_file, "w") as f:
            json.dump(self.settings, f, indent=4)
        
        # Apply theme changes immediately
        self.apply_theme()
        
        # Handle music based on sound setting
        if self.sound_var.get():
            self.start_music()
        else:
            self.stop_music()

    def save_games(self):
        with open(self.games_file, "w") as f:
            json.dump(self.games, f, indent=4)

    def load_game_art(self, game_id):
        """Load game art image"""
        game_info = self.games.get(game_id, {})
        art_filename = game_info.get("art", f"{game_id}.png")
        art_path = os.path.join(self.game_art_folder, art_filename)
        
        try:
            if os.path.exists(art_path):
                img = Image.open(art_path)
                img = img.resize((75, 75), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading game art for {game_id}: {e}")
        
        # Create default art
        img = Image.new('RGB', (75, 75), color='#95a5a6')
        return ImageTk.PhotoImage(img)

    def update_game_sidebar(self):
        # Clear existing game buttons
        for widget in self.games_scrollable_frame.winfo_children():
            widget.destroy()
        
        theme = self.themes[self.settings.get("theme", "dark")]
        
        # Create grid
        row = 0
        col = 0
        max_cols = 3
        
        for game_id, game_info in self.games.items():
            if not game_info.get("enabled", True):
                continue
            
            # Load game art
            game_art = self.load_game_art(game_id)
            
            # Create game button frame
            game_frame = tk.Frame(self.games_scrollable_frame, bg=theme["bg_secondary"])
            game_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            # Game art button
            game_btn = tk.Button(game_frame, image=game_art, 
                               command=lambda gid=game_id: self.select_game(gid),
                               bg=theme["bg_secondary"], relief="flat", bd=2,
                               activebackground=theme["hover"], cursor="hand2")
            game_btn.pack(pady=2)
            game_btn.image = game_art  # Keep a reference
            
            # Tooltip on hover
            self.create_tooltip(game_btn, game_info["name"])
            
            # Version label
            version_label = tk.Label(game_frame, text=f"v{game_info.get('version', '1.0.0')}", 
                                   font=("Arial", 8), bg=theme["bg_secondary"], fg=theme["fg_primary"])
            version_label.pack()
            
            # Play time if tracking enabled
            if self.settings.get("play_time_tracking", True):
                playtime = self.settings.get("total_play_times", {}).get(game_id, 0)
                hours = int(playtime // 3600)
                minutes = int((playtime % 3600) // 60)
                if hours > 0 or minutes > 0:
                    time_text = f"{hours}h {minutes}m"
                    time_label = tk.Label(game_frame, text=time_text, font=("Arial", 7), 
                                        bg=theme["bg_secondary"], fg=theme["fg_primary"])
                    time_label.pack()
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(max_cols):
            self.games_scrollable_frame.columnconfigure(i, weight=1)

    def create_tooltip(self, widget, text):
        """Create tooltip for widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#333333", foreground="white", 
                           relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def select_game(self, game_id):
        if game_id in self.games:
            self.current_game = game_id
            self.save_settings()
            if hasattr(self, 'content_frame'):
                self.show_home()

    def show_fake_loading(self, callback):
        """Show fake loading bar for 35 seconds then execute callback"""
        self.is_loading = True
        self.loading_frame.pack(side="bottom", fill="x", pady=8)
        self.loading_progress['value'] = 0
        
        def update_progress():
            for i in range(351):
                if not self.is_loading:
                    break
                    
                progress = (i / 350) * 100
                self.loading_progress['value'] = progress
                self.root.update_idletasks()
                time.sleep(0.1)
            
            if self.is_loading:
                self.loading_frame.pack_forget()
                self.is_loading = False
                callback()
        
        loading_thread = threading.Thread(target=update_progress)
        loading_thread.start()

    def launch_game(self):
        if not self.current_game or self.current_game not in self.games:
            messagebox.showerror("Error", "No game selected!")
            return
        
        if self.is_loading:
            return
        
        game_info = self.games[self.current_game]
        game_path = game_info["path"]
        
        if not os.path.exists(game_path):
            messagebox.showerror("Error", f"Game executable not found at: {game_path}")
            return
        
        def actually_launch():
            try:
                if self.settings.get("play_time_tracking", True):
                    self.play_start_time = time.time()
                
                process = subprocess.Popen([game_path])
                
                if self.settings.get("play_time_tracking", True):
                    self.monitor_game_process(process)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch game: {e}")
        
        self.show_fake_loading(actually_launch)

    def monitor_game_process(self, process):
        """Monitor game process to track play time"""
        def track_time():
            process.wait()
            if self.play_start_time:
                play_duration = time.time() - self.play_start_time
                
                if "total_play_times" not in self.settings:
                    self.settings["total_play_times"] = {}
                
                current_time = self.settings["total_play_times"].get(self.current_game, 0)
                self.settings["total_play_times"][self.current_game] = current_time + play_duration
                
                self.save_settings()
                self.update_game_sidebar()
                self.play_start_time = None
        
        track_thread = threading.Thread(target=track_time, daemon=True)
        track_thread.start()

    def open_link(self, url):
        webbrowser.open(url)

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_content()
        theme = self.themes[self.settings.get("theme", "dark")]
        
        if not self.current_game:
            no_game_label = tk.Label(self.content_frame, text="No Game Selected", 
                                   font=("Arial", 24, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
            no_game_label.pack(pady=100)
            
            select_label = tk.Label(self.content_frame, text="Please select a game from the sidebar", 
                                  font=("Arial", 14), bg=theme["bg_content"], fg=theme["fg_secondary"])
            select_label.pack()
            return
        
        game_info = self.games[self.current_game]
        
        # Game title
        title_label = tk.Label(self.content_frame, text=game_info["name"], 
                             font=("Arial", 28, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        title_label.pack(pady=30)
        
        # Game version
        version_label = tk.Label(self.content_frame, text=f"Version {game_info.get('version', '1.0.0')}", 
                               font=("Arial", 12), bg=theme["bg_content"], fg=theme["fg_secondary"])
        version_label.pack()
        
        # Launch button - rounded
        launch_frame = tk.Frame(self.content_frame, bg=theme["bg_content"])
        launch_frame.pack(pady=30)
        
        launch_button = RoundedButton(launch_frame, 200, 60, 15, 10, theme["success"], 
                                    theme["bg_content"], command=self.launch_game, 
                                    text="🎮 Launch Game", font=("Arial", 16, "bold"))
        launch_button.pack()
        
        # Game description
        desc_label = tk.Label(self.content_frame, text="Description:", 
                            font=("Arial", 14, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        desc_label.pack(anchor="w", padx=30, pady=(30, 10))
        
        # Description frame with rounded corners
        desc_frame = tk.Frame(self.content_frame, bg=theme["bg_content"])
        desc_frame.pack(pady=10, padx=30, fill="x")
        
        desc_text = tk.Text(desc_frame, wrap="word", font=("Arial", 12), 
                          width=80, height=8, bg="white", relief="solid", bd=1,
                          borderwidth=2)
        desc_text.insert("1.0", game_info["description"])
        desc_text.config(state="disabled")
        desc_text.pack(fill="x")
        
        # Game status and play time
        info_frame = tk.Frame(self.content_frame, bg=theme["bg_content"])
        info_frame.pack(pady=20, padx=30, fill="x")
        
        # Status
        status_frame = tk.Frame(info_frame, bg=theme["bg_content"])
        status_frame.pack(fill="x", pady=5)
        
        status_label = tk.Label(status_frame, text="Status:", font=("Arial", 12, "bold"), 
                              bg=theme["bg_content"], fg=theme["fg_secondary"])
        status_label.pack(side="left")
        
        if os.path.exists(game_info["path"]):
            status_value = tk.Label(status_frame, text="✅ Ready to Play", 
                                  font=("Arial", 12), bg=theme["bg_content"], fg=theme["success"])
        else:
            status_value = tk.Label(status_frame, text="❌ Game Not Found", 
                                  font=("Arial", 12), bg=theme["bg_content"], fg=theme["danger"])
        status_value.pack(side="left", padx=(15, 0))
        
        # Show play time if tracking is enabled
        if self.settings.get("play_time_tracking", True):
            playtime = self.settings.get("total_play_times", {}).get(self.current_game, 0)
            hours = int(playtime // 3600)
            minutes = int((playtime % 3600) // 60)
            
            time_frame = tk.Frame(info_frame, bg=theme["bg_content"])
            time_frame.pack(fill="x", pady=5)
            
            time_label = tk.Label(time_frame, text=f"Total Play Time: {hours}h {minutes}m", 
                                font=("Arial", 12, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
            time_label.pack(side="left")

    def show_announcements(self):
        self.clear_content()
        theme = self.themes[self.settings.get("theme", "dark")]
        
        title = tk.Label(self.content_frame, text="📢 Game Announcements", 
                        font=("Arial", 20, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        title.pack(pady=30)
        
        ann_text = tk.Text(self.content_frame, wrap="word", font=("Arial", 13), 
                         width=90, height=20, bg="white", relief="solid", bd=2)
        
        announcements = """🎉 Welcome to the Enhanced Game Launcher v3.0!

🔥 What's New in Version 3.0:
• Full 1920x1080 resolution support for modern displays
• Clickable banner ads with rotation system
• Game grid layout with beautiful 75x75 box art
• Hover tooltips showing game titles
• Rounded corners throughout the interface for modern look
• Discord integration showing online member count
• Dedicated support page with multiple donation options
• Enhanced settings with gear icon placement
• Improved navigation with better visual hierarchy

🎮 Game Features:
• Visual game library with custom artwork
• Play time tracking with detailed statistics
• Fake loading screens for authentic retro experience
• Background music support (keygen-style)
• Dark/Light theme switching

💝 Support Options:
Visit our new Support page to help fund development:
• Ko-fi for one-time donations
• Patreon for monthly support
• PayPal for direct contributions
• Website for merchandise and more

🎵 Music System:
Add your favorite keygen-style music as 'launcher_music.mp3' for that nostalgic experience!

📱 Discord Community:
Join our Discord server to connect with other players and get the latest updates!

📋 File Structure:
• /ads/ - Place 320x50 banner images here
• /game_art/ - Add 75x75 game artwork here
• ads.json - Configure ad links
• games.json - Game library configuration

Happy Gaming! 🎮
"""
        
        ann_text.insert("1.0", announcements)
        ann_text.config(state="disabled")
        ann_text.pack(pady=20, padx=40, fill="both", expand=True)

    def show_support(self):
        """Show support/donation page"""
        self.clear_content()
        theme = self.themes[self.settings.get("theme", "dark")]
        
        title = tk.Label(self.content_frame, text="💝 Support Our Development", 
                        font=("Arial", 20, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        title.pack(pady=30)
        
        subtitle = tk.Label(self.content_frame, text="Help us create amazing games and tools!", 
                          font=("Arial", 14), bg=theme["bg_content"], fg=theme["fg_secondary"])
        subtitle.pack(pady=10)
        
        # Support options frame
        support_frame = tk.Frame(self.content_frame, bg=theme["bg_content"])
        support_frame.pack(pady=30)
        
        # Ko-fi button
        kofi_frame = tk.Frame(support_frame, bg=theme["bg_content"])
        kofi_frame.pack(pady=10)
        
        kofi_btn = RoundedButton(kofi_frame, 250, 50, 15, 10, "#ff5f5f", theme["bg_content"],
                               command=lambda: self.open_link("https://ko-fi.com/15gay"),
                               text="☕ Support on Ko-fi", font=("Arial", 14, "bold"))
        kofi_btn.pack()
        
        kofi_desc = tk.Label(kofi_frame, text="One-time donations to fuel our creativity", 
                           font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
        kofi_desc.pack(pady=(5, 0))
        
        # Patreon button
        patreon_frame = tk.Frame(support_frame, bg=theme["bg_content"])
        patreon_frame.pack(pady=10)
        
        patreon_btn = RoundedButton(patreon_frame, 250, 50, 15, 10, "#ff424d", theme["bg_content"],
                                  command=lambda: self.open_link("https://patreon.com/15gay"),
                                  text="🎯 Join our Patreon", font=("Arial", 14, "bold"))
        patreon_btn.pack()
        
        patreon_desc = tk.Label(patreon_frame, text="Monthly support with exclusive perks", 
                              font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
        patreon_desc.pack(pady=(5, 0))
        
        # PayPal button
        paypal_frame = tk.Frame(support_frame, bg=theme["bg_content"])
        paypal_frame.pack(pady=10)
        
        paypal_btn = RoundedButton(paypal_frame, 250, 50, 15, 10, "#0070ba", theme["bg_content"],
                                 command=lambda: self.open_link("https://paypal.me/15gay"),
                                 text="💳 Donate via PayPal", font=("Arial", 14, "bold"))
        paypal_btn.pack()
        
        paypal_desc = tk.Label(paypal_frame, text="Direct and secure payments", 
                             font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
        paypal_desc.pack(pady=(5, 0))
        
        # Website button
        website_frame = tk.Frame(support_frame, bg=theme["bg_content"])
        website_frame.pack(pady=10)
        
        website_btn = RoundedButton(website_frame, 250, 50, 15, 10, "#6f42c1", theme["bg_content"],
                                  command=lambda: self.open_link("https://15.gay/"),
                                  text="🌐 Visit Our Website", font=("Arial", 14, "bold"))
        website_btn.pack()
        
        website_desc = tk.Label(website_frame, text="Merchandise, news, and more ways to help", 
                              font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
        website_desc.pack(pady=(5, 0))
        
        # Thank you message
        thanks_frame = tk.Frame(self.content_frame, bg=theme["bg_content"])
        thanks_frame.pack(pady=40)
        
        thanks_msg = tk.Label(thanks_frame, 
                            text="Every contribution helps us create better games and tools!\nThank you for being part of our community! ❤️", 
                            font=("Arial", 12), bg=theme["bg_content"], fg=theme["fg_secondary"],
                            justify="center")
        thanks_msg.pack()

    def show_settings(self):
        self.clear_content()
        theme = self.themes[self.settings.get("theme", "dark")]
        
        title = tk.Label(self.content_frame, text="⚙️ Launcher Settings", 
                        font=("Arial", 20, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        title.pack(pady=30)
        
        # Settings container
        settings_container = tk.Frame(self.content_frame, bg=theme["bg_content"])
        settings_container.pack(pady=20, padx=50, fill="both", expand=True)
        
        # Audio settings frame
        audio_frame = tk.LabelFrame(settings_container, text="Audio Settings", 
                                  font=("Arial", 14, "bold"), bg=theme["bg_content"], 
                                  fg=theme["fg_secondary"], padx=20, pady=15)
        audio_frame.pack(fill="x", pady=10)
        
        sound_check = tk.Checkbutton(audio_frame, text="🔊 Enable Background Music", 
                                   variable=self.sound_var, font=("Arial", 12),
                                   bg=theme["bg_content"], fg=theme["fg_secondary"], 
                                   activebackground=theme["bg_content"],
                                   command=self.save_settings)
        sound_check.pack(anchor="w", pady=5)
        
        music_info = tk.Label(audio_frame, text="Place your music file as 'launcher_music.mp3' in the launcher folder", 
                            font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
        music_info.pack(anchor="w", padx=20)
        
        # Appearance settings frame
        appearance_frame = tk.LabelFrame(settings_container, text="Appearance", 
                                       font=("Arial", 14, "bold"), bg=theme["bg_content"], 
                                       fg=theme["fg_secondary"], padx=20, pady=15)
        appearance_frame.pack(fill="x", pady=10)
        
        theme_frame = tk.Frame(appearance_frame, bg=theme["bg_content"])
        theme_frame.pack(anchor="w", pady=5, fill="x")
        
        theme_label = tk.Label(theme_frame, text="🎨 Theme:", font=("Arial", 12),
                             bg=theme["bg_content"], fg=theme["fg_secondary"])
        theme_label.pack(side="left")
        
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                 values=["dark", "light"], state="readonly", width=12,
                                 font=("Arial", 11))
        theme_combo.pack(side="left", padx=(15, 0))
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.save_settings())
        
        # Tracking settings frame
        tracking_frame = tk.LabelFrame(settings_container, text="Tracking & Statistics", 
                                     font=("Arial", 14, "bold"), bg=theme["bg_content"], 
                                     fg=theme["fg_secondary"], padx=20, pady=15)
        tracking_frame.pack(fill="x", pady=10)
        
        playtime_check = tk.Checkbutton(tracking_frame, text="⏱️ Enable Play Time Tracking", 
                                      variable=self.play_time_var, font=("Arial", 12),
                                      bg=theme["bg_content"], fg=theme["fg_secondary"], 
                                      activebackground=theme["bg_content"],
                                      command=self.save_settings)
        playtime_check.pack(anchor="w", pady=5)
        
        tracking_info = tk.Label(tracking_frame, text="Tracks how long you play each game for statistics", 
                               font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
        tracking_info.pack(anchor="w", padx=20)
        
        # Current game info
        if self.current_game:
            current_frame = tk.LabelFrame(settings_container, text="Currently Selected Game", 
                                        font=("Arial", 14, "bold"), bg=theme["bg_content"], 
                                        fg=theme["fg_secondary"], padx=20, pady=15)
            current_frame.pack(fill="x", pady=10)
            
            game_info = self.games[self.current_game]
            current_label = tk.Label(current_frame, text=f"🎮 {game_info['name']}", 
                                   font=("Arial", 12), bg=theme["bg_content"], fg=theme["fg_secondary"])
            current_label.pack(anchor="w", pady=5)
            
            # Show total play time for current game
            if self.settings.get("play_time_tracking", True):
                playtime = self.settings.get("total_play_times", {}).get(self.current_game, 0)
                hours = int(playtime // 3600)
                minutes = int((playtime % 3600) // 60)
                time_label = tk.Label(current_frame, text=f"⏰ Total Play Time: {hours}h {minutes}m", 
                                    font=("Arial", 11), bg=theme["bg_content"], fg=theme["fg_secondary"])
                time_label.pack(anchor="w", pady=2)

    def run(self):
        # Save settings when closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        self.is_loading = False  # Stop any loading processes
        self.stop_music()
        self.save_settings()
        self.root.destroy()

# Run the launcher
if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()