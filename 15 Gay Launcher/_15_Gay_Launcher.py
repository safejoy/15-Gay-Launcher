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

class GameLauncher:
    def __init__(self):
        self.config_file = "settings.json"
        self.games_file = "games.json"
        self.ads_folder = "ads"
        self.music_file = "Games/bgm.mp3"  # Place your music file here
        self.current_game = None
        self.is_loading = False
        self.play_start_time = None
        self.current_ad_index = 0
        self.ad_images = []
        
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
                "danger": "#e74c3c"
            },
            "light": {
                "bg_primary": "#f8f9fa",
                "bg_secondary": "#e9ecef",
                "bg_content": "#ffffff", 
                "fg_primary": "#2c3e50",
                "fg_secondary": "#495057",
                "accent": "#007bff",
                "success": "#28a745",
                "danger": "#dc3545"
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
                "enabled": True
            },
            "puzzle": {
                "name": "Puzzle Master", 
                "description": "Challenge your mind with increasingly difficult puzzles.",
                "path": "Games/Puzzle/Game.exe",
                "version": "0.8.5",
                "enabled": True
            },
            "platformer": {
                "name": "Jump Quest",
                "description": "A classic platformer with modern gameplay mechanics.",
                "path": "Games/Platformer/Game.exe",
                "version": "2.1.0",
                "enabled": False
            }
        }
        
        self.setup_ui()
        self.load_settings()
        self.load_games()
        self.load_ads()
        self.apply_theme()
        self.start_music()
        self.start_ad_rotation()
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
        self.root.geometry("800x650")
        
        # Create main layout
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Ad banner area (320x50)
        self.ad_frame = tk.Frame(self.main_frame, height=50)
        self.ad_frame.pack(fill="x", pady=(0, 10))
        self.ad_frame.pack_propagate(False)
        
        self.ad_label = tk.Label(self.ad_frame, text="Loading ads...", font=("Arial", 10))
        self.ad_label.pack(expand=True)
        
        # Content area frame
        self.content_wrapper = tk.Frame(self.main_frame)
        self.content_wrapper.pack(fill="both", expand=True)
        
        # Left sidebar for navigation
        self.nav_sidebar = tk.Frame(self.content_wrapper, width=150)
        self.nav_sidebar.pack(side="left", fill="y", padx=(0, 5))
        self.nav_sidebar.pack_propagate(False)
        
        # Right sidebar for game selection  
        self.game_sidebar = tk.Frame(self.content_wrapper, width=180)
        self.game_sidebar.pack(side="right", fill="y", padx=(5, 0))
        self.game_sidebar.pack_propagate(False)
        
        # Content area
        self.content_frame = tk.Frame(self.content_wrapper)
        self.content_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Loading bar frame (initially hidden)
        self.loading_frame = tk.Frame(self.main_frame)
        self.loading_label = tk.Label(self.loading_frame, text="Launching game...", font=("Arial", 10))
        self.loading_label.pack()
        self.loading_progress = ttk.Progressbar(self.loading_frame, mode='determinate', length=300)
        self.loading_progress.pack(pady=5)
        
        self.setup_navigation_sidebar()
        self.setup_game_sidebar()

    def setup_navigation_sidebar(self):
        # Navigation title
        self.nav_title = tk.Label(self.nav_sidebar, text="Navigation", font=("Arial", 12, "bold"))
        self.nav_title.pack(pady=10)
        
        # Navigation buttons
        self.nav_buttons = []
        buttons = [
            ("🏠 Home", self.show_home),
            ("📰 Announcements", self.show_announcements),
            ("⚙️ Settings", self.show_settings),
            ("🌐 Studio Website", lambda: self.open_link("https://15.gay/")),
            ("☁️ BlueSky", lambda: self.open_link("https://bsky.app/profile/15gay.itch.io")),
            ("👾 Itch", lambda: self.open_link("https://15gay.itch.io/"))
        ]
        
        for text, command in buttons:
            btn = tk.Button(self.nav_sidebar, text=text, command=command, relief="flat", font=("Arial", 9))
            btn.pack(fill="x", pady=2, padx=5)
            self.nav_buttons.append(btn)
        
        # Spacer to push exit button to bottom
        spacer = tk.Frame(self.nav_sidebar)
        spacer.pack(expand=True, fill="y")
        
        # Exit button at bottom
        self.exit_btn = tk.Button(self.nav_sidebar, text="🚪 Exit Launcher", command=self.on_closing, 
                                 relief="flat", font=("Arial", 9))
        self.exit_btn.pack(fill="x", pady=5, padx=5)
        self.nav_buttons.append(self.exit_btn)

    def setup_game_sidebar(self):
        # Games title
        self.games_title = tk.Label(self.game_sidebar, text="Available Games", font=("Arial", 12, "bold"))
        self.games_title.pack(pady=10)
        
        # Scrollable frame for games
        self.games_canvas = tk.Canvas(self.game_sidebar, highlightthickness=0)
        self.games_scrollbar = ttk.Scrollbar(self.game_sidebar, orient="vertical", command=self.games_canvas.yview)
        self.games_scrollable_frame = tk.Frame(self.games_canvas)
        
        self.games_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.games_canvas.configure(scrollregion=self.games_canvas.bbox("all"))
        )
        
        self.games_canvas.create_window((0, 0), window=self.games_scrollable_frame, anchor="nw")
        self.games_canvas.configure(yscrollcommand=self.games_scrollbar.set)
        
        self.games_canvas.pack(side="left", fill="both", expand=True, padx=5)
        self.games_scrollbar.pack(side="right", fill="y")

    def load_ads(self):
        """Load banner ad images from ads folder"""
        self.ad_images = []
        if not os.path.exists(self.ads_folder):
            os.makedirs(self.ads_folder)
            # Create a default ad image if folder is empty
            self.create_default_ad()
            return
            
        for filename in os.listdir(self.ads_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    image_path = os.path.join(self.ads_folder, filename)
                    img = Image.open(image_path)
                    # Resize to 320x50
                    img = img.resize((320, 50), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.ad_images.append(photo)
                except Exception as e:
                    print(f"Error loading ad image {filename}: {e}")
        
        if not self.ad_images:
            self.create_default_ad()

    def create_default_ad(self):
        """Create a default ad if no images are found"""
        # Create a simple default ad
        img = Image.new('RGB', (320, 50), color='#3498db')
        photo = ImageTk.PhotoImage(img)
        self.ad_images.append(photo)

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
                time.sleep(5)  # Rotate every 5 seconds
        
        ad_thread = threading.Thread(target=rotate_ads, daemon=True)
        ad_thread.start()

    def start_music(self):
        """Start playing background music if enabled"""
        if self.settings.get("sound", True) and os.path.exists(self.music_file):
            try:
                pygame.mixer.music.load(self.music_file)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                pygame.mixer.music.set_volume(0.3)  # Set to 30% volume
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
        
        # Navigation elements
        self.nav_title.configure(bg=theme["bg_secondary"], fg=theme["fg_primary"])
        self.games_title.configure(bg=theme["bg_secondary"], fg=theme["fg_primary"])
        self.games_canvas.configure(bg=theme["bg_secondary"])
        self.games_scrollable_frame.configure(bg=theme["bg_secondary"])
        self.ad_label.configure(bg=theme["bg_primary"], fg=theme["fg_primary"])
        self.loading_label.configure(bg=theme["bg_primary"], fg=theme["fg_primary"])
        
        # Navigation buttons
        for btn in self.nav_buttons:
            btn.configure(bg=theme["accent"], fg=theme["fg_primary"], 
                         activebackground=theme["success"], activeforeground=theme["fg_primary"])

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

    def update_game_sidebar(self):
        # Clear existing game buttons
        for widget in self.games_scrollable_frame.winfo_children():
            widget.destroy()
        
        theme = self.themes[self.settings.get("theme", "dark")]
        
        for game_id, game_info in self.games.items():
            if not game_info.get("enabled", True):
                continue
                
            # Create game button frame
            game_frame = tk.Frame(self.games_scrollable_frame, bg=theme["bg_secondary"])
            game_frame.pack(fill="x", pady=2, padx=5)
            
            # Game button
            game_btn = tk.Button(game_frame, text=game_info["name"], 
                               command=lambda gid=game_id: self.select_game(gid),
                               bg=theme["accent"], fg=theme["fg_primary"], relief="flat", font=("Arial", 9, "bold"),
                               activebackground=theme["success"], activeforeground=theme["fg_primary"])
            game_btn.pack(fill="x", pady=1)
            
            # Version and playtime labels
            version_label = tk.Label(game_frame, text=f"v{game_info.get('version', '1.0.0')}", 
                                   font=("Arial", 7), bg=theme["bg_secondary"], fg=theme["fg_primary"])
            version_label.pack()
            
            # Show playtime if tracking is enabled
            if self.settings.get("play_time_tracking", True):
                playtime = self.settings.get("total_play_times", {}).get(game_id, 0)
                hours = int(playtime // 3600)
                minutes = int((playtime % 3600) // 60)
                time_text = f"Played: {hours}h {minutes}m"
                time_label = tk.Label(game_frame, text=time_text, font=("Arial", 6), 
                                    bg=theme["bg_secondary"], fg=theme["fg_primary"])
                time_label.pack()

    def select_game(self, game_id):
        if game_id in self.games:
            self.current_game = game_id
            self.save_settings()
            if hasattr(self, 'content_frame'):
                self.show_home()

    def show_fake_loading(self, callback):
        """Show fake loading bar for 35 seconds then execute callback"""
        self.is_loading = True
        self.loading_frame.pack(side="bottom", fill="x", pady=5)
        self.loading_progress['value'] = 0
        
        def update_progress():
            for i in range(351):  # 35.1 seconds with 0.1s intervals
                if not self.is_loading:  # Allow cancellation
                    break
                    
                progress = (i / 350) * 100
                self.loading_progress['value'] = progress
                self.root.update_idletasks()
                time.sleep(0.1)
            
            if self.is_loading:
                self.loading_frame.pack_forget()
                self.is_loading = False
                callback()
        
        # Run in separate thread to not block UI
        loading_thread = threading.Thread(target=update_progress)
        loading_thread.start()

    def launch_game(self):
        if not self.current_game or self.current_game not in self.games:
            messagebox.showerror("Error", "No game selected!")
            return
        
        if self.is_loading:
            return  # Prevent multiple launches
        
        game_info = self.games[self.current_game]
        game_path = game_info["path"]
        
        if not os.path.exists(game_path):
            messagebox.showerror("Error", f"Game executable not found at: {game_path}")
            return
        
        def actually_launch():
            try:
                # Start play time tracking
                if self.settings.get("play_time_tracking", True):
                    self.play_start_time = time.time()
                
                # Launch the game
                process = subprocess.Popen([game_path])
                
                # Monitor the game process for play time tracking
                if self.settings.get("play_time_tracking", True):
                    self.monitor_game_process(process)
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch game: {e}")
        
        # Show fake loading bar
        self.show_fake_loading(actually_launch)

    def monitor_game_process(self, process):
        """Monitor game process to track play time"""
        def track_time():
            process.wait()  # Wait for game to close
            if self.play_start_time:
                play_duration = time.time() - self.play_start_time
                
                # Update total play time
                if "total_play_times" not in self.settings:
                    self.settings["total_play_times"] = {}
                
                current_time = self.settings["total_play_times"].get(self.current_game, 0)
                self.settings["total_play_times"][self.current_game] = current_time + play_duration
                
                self.save_settings()
                self.update_game_sidebar()  # Refresh to show updated play time
                self.play_start_time = None
        
        # Run in separate thread
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
            # No game selected
            no_game_label = tk.Label(self.content_frame, text="No Game Selected", 
                                   font=("Arial", 18, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
            no_game_label.pack(pady=50)
            
            select_label = tk.Label(self.content_frame, text="Please select a game from the sidebar", 
                                  font=("Arial", 12), bg=theme["bg_content"], fg=theme["fg_secondary"])
            select_label.pack()
            return
        
        game_info = self.games[self.current_game]
        
        # Game title
        title_label = tk.Label(self.content_frame, text=game_info["name"], 
                             font=("Arial", 20, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        title_label.pack(pady=20)
        
        # Game version
        version_label = tk.Label(self.content_frame, text=f"Version {game_info.get('version', '1.0.0')}", 
                               font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
        version_label.pack()
        
        # Launch button
        launch_button = tk.Button(self.content_frame, text="🎮 Launch Game", 
                                command=self.launch_game, font=("Arial", 14, "bold"),
                                bg=theme["success"], fg=theme["fg_primary"], activebackground=theme["success"],
                                relief="flat", padx=30, pady=10)
        launch_button.pack(pady=20)
        
        # Game description
        desc_label = tk.Label(self.content_frame, text="Description:", 
                            font=("Arial", 12, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        desc_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        desc_text = tk.Text(self.content_frame, wrap="word", font=("Arial", 10), 
                          width=60, height=6, bg="white", relief="solid", bd=1)
        desc_text.insert("1.0", game_info["description"])
        desc_text.config(state="disabled")
        desc_text.pack(pady=5, padx=20, fill="x")
        
        # Game status and play time
        status_frame = tk.Frame(self.content_frame, bg=theme["bg_content"])
        status_frame.pack(pady=10, padx=20, fill="x")
        
        status_label = tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold"), 
                              bg=theme["bg_content"], fg=theme["fg_secondary"])
        status_label.pack(side="left")
        
        if os.path.exists(game_info["path"]):
            status_value = tk.Label(status_frame, text="✅ Ready to Play", 
                                  font=("Arial", 10), bg=theme["bg_content"], fg=theme["success"])
        else:
            status_value = tk.Label(status_frame, text="❌ Game Not Found", 
                                  font=("Arial", 10), bg=theme["bg_content"], fg=theme["danger"])
        status_value.pack(side="left", padx=(10, 0))
        
        # Show play time if tracking is enabled
        if self.settings.get("play_time_tracking", True):
            playtime = self.settings.get("total_play_times", {}).get(self.current_game, 0)
            hours = int(playtime // 3600)
            minutes = int((playtime % 3600) // 60)
            
            time_frame = tk.Frame(self.content_frame, bg=theme["bg_content"])
            time_frame.pack(pady=5, padx=20, fill="x")
            
            time_label = tk.Label(time_frame, text=f"Total Play Time: {hours}h {minutes}m", 
                                font=("Arial", 10, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
            time_label.pack(side="left")

    def show_announcements(self):
        self.clear_content()
        theme = self.themes[self.settings.get("theme", "dark")]
        
        title = tk.Label(self.content_frame, text="📢 Game Announcements", 
                        font=("Arial", 16, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        title.pack(pady=20)
        
        ann_text = tk.Text(self.content_frame, wrap="word", font=("Arial", 11), 
                         width=70, height=15, bg="white", relief="solid", bd=1)
        
        announcements = """🎉 Welcome to the Enhanced Game Launcher v2.0!

🔥 What's New in Version 2.0:
• Dark/Light theme support for personalized experience
• Play time tracking to monitor your gaming habits
• Background music system (place your music as 'launcher_music.mp3')
• Custom banner ad rotation system (add 320x50 images to 'ads' folder)
• Fake loading screen for that authentic retro feel
• Enhanced UI with better navigation and exit button

🎮 Available Games:
• Ace Adventure - Our flagship RPG experience
• Puzzle Master - Brain-teasing puzzle challenges  
• Jump Quest - Classic platforming action

⏱️ Play Time Tracking:
Track how long you spend in each game! Stats are saved and displayed in the game selection sidebar.

🎵 Music System:
Add your favorite keygen-style music as 'launcher_music.mp3' in the launcher folder for that nostalgic experience!

📋 Upcoming Features:
• Achievement tracking
• Cloud save synchronization
• More theme options
• Advanced statistics

💬 Stay Connected:
Follow us on BlueSky and check out our games on Itch.io for the latest updates!

Happy Gaming! 🎮
"""
        
        ann_text.insert("1.0", announcements)
        ann_text.config(state="disabled")
        ann_text.pack(pady=10, padx=20, fill="both", expand=True)

    def show_settings(self):
        self.clear_content()
        theme = self.themes[self.settings.get("theme", "dark")]
        
        title = tk.Label(self.content_frame, text="⚙️ Launcher Settings", 
                        font=("Arial", 16, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        title.pack(pady=20)
        
        # Settings frame
        settings_frame = tk.LabelFrame(self.content_frame, text="Launcher Settings", 
                                     font=("Arial", 12, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
        settings_frame.pack(pady=10, padx=20, fill="x")
        
        # Sound setting
        sound_check = tk.Checkbutton(settings_frame, text="🔊 Enable Background Music", 
                                   variable=self.sound_var, font=("Arial", 11),
                                   bg=theme["bg_content"], fg=theme["fg_secondary"], activebackground=theme["bg_content"],
                                   command=self.save_settings)
        sound_check.pack(anchor="w", padx=10, pady=5)
        
        # Theme setting
        theme_frame = tk.Frame(settings_frame, bg=theme["bg_content"])
        theme_frame.pack(anchor="w", padx=10, pady=5, fill="x")
        
        theme_label = tk.Label(theme_frame, text="🎨 Theme:", font=("Arial", 11),
                             bg=theme["bg_content"], fg=theme["fg_secondary"])
        theme_label.pack(side="left")
        
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                 values=["dark", "light"], state="readonly", width=10)
        theme_combo.pack(side="left", padx=(10, 0))
        theme_combo.bind("<<ComboboxSelected>>", lambda e: self.save_settings())
        
        # Play time tracking
        playtime_check = tk.Checkbutton(settings_frame, text="⏱️ Enable Play Time Tracking", 
                                      variable=self.play_time_var, font=("Arial", 11),
                                      bg=theme["bg_content"], fg=theme["fg_secondary"], activebackground=theme["bg_content"],
                                      command=self.save_settings)
        playtime_check.pack(anchor="w", padx=10, pady=5)
        
        # Current game info
        if self.current_game:
            current_frame = tk.LabelFrame(self.content_frame, text="Currently Selected", 
                                        font=("Arial", 12, "bold"), bg=theme["bg_content"], fg=theme["fg_secondary"])
            current_frame.pack(pady=10, padx=20, fill="x")
            
            game_info = self.games[self.current_game]
            current_label = tk.Label(current_frame, text=f"🎮 {game_info['name']}", 
                                   font=("Arial", 11), bg=theme["bg_content"], fg=theme["fg_secondary"])
            current_label.pack(anchor="w", padx=10, pady=5)
            
            # Show total play time for current game
            if self.settings.get("play_time_tracking", True):
                playtime = self.settings.get("total_play_times", {}).get(self.current_game, 0)
                hours = int(playtime // 3600)
                minutes = int((playtime % 3600) // 60)
                time_label = tk.Label(current_frame, text=f"⏰ Total Play Time: {hours}h {minutes}m", 
                                    font=("Arial", 10), bg=theme["bg_content"], fg=theme["fg_secondary"])
                time_label.pack(anchor="w", padx=10, pady=2)

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