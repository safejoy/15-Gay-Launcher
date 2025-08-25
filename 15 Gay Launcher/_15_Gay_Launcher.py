import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
import json
import os
from pathlib import Path

class GameLauncher:
    def __init__(self):
        self.config_file = "settings.json"
        self.games_file = "games.json"
        self.current_game = None
        
        # Initialize settings
        self.default_settings = {
            "sound": True,
            "dash": True,
            "last_selected_game": None
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
        self.root.geometry("800x600")
        self.root.configure(bg="#2c3e50")
        
        # Create main layout
        self.main_frame = tk.Frame(self.root, bg="#2c3e50")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left sidebar for navigation
        self.nav_sidebar = tk.Frame(self.main_frame, bg="#34495e", width=150)
        self.nav_sidebar.pack(side="left", fill="y", padx=(0, 5))
        self.nav_sidebar.pack_propagate(False)
        
        # Right sidebar for game selection
        self.game_sidebar = tk.Frame(self.main_frame, bg="#34495e", width=180)
        self.game_sidebar.pack(side="right", fill="y", padx=(5, 0))
        self.game_sidebar.pack_propagate(False)
        
        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg="#ecf0f1")
        self.content_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        self.setup_navigation_sidebar()
        self.setup_game_sidebar()

    def setup_navigation_sidebar(self):
        # Navigation title
        nav_title = tk.Label(self.nav_sidebar, text="Navigation", font=("Arial", 12, "bold"), 
                           bg="#34495e", fg="white")
        nav_title.pack(pady=10)
        
        # Navigation buttons
        buttons = [
            ("🏠 Home", self.show_home),
            ("📰 Announcements", self.show_announcements),
            ("⚙️ Settings", self.show_settings),
            ("🌐 Studio Website", lambda: self.open_link("https://15.gay/")),
            ("☁️ BlueSky", lambda: self.open_link("https://bsky.app/profile/15gay.itch.io")),
            ("👾 Itch", lambda: self.open_link("https://15gay.itch.io/"))
        ]
        
        for text, command in buttons:
            btn = tk.Button(self.nav_sidebar, text=text, command=command, 
                          bg="#4a6741", fg="white", relief="flat", font=("Arial", 9),
                          activebackground="#5a7751", activeforeground="white")
            btn.pack(fill="x", pady=2, padx=5)

    def setup_game_sidebar(self):
        # Games title
        games_title = tk.Label(self.game_sidebar, text="Available Games", 
                             font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        games_title.pack(pady=10)
        
        # Scrollable frame for games
        self.games_canvas = tk.Canvas(self.game_sidebar, bg="#34495e", highlightthickness=0)
        self.games_scrollbar = ttk.Scrollbar(self.game_sidebar, orient="vertical", command=self.games_canvas.yview)
        self.games_scrollable_frame = tk.Frame(self.games_canvas, bg="#34495e")
        
        self.games_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.games_canvas.configure(scrollregion=self.games_canvas.bbox("all"))
        )
        
        self.games_canvas.create_window((0, 0), window=self.games_scrollable_frame, anchor="nw")
        self.games_canvas.configure(yscrollcommand=self.games_scrollbar.set)
        
        self.games_canvas.pack(side="left", fill="both", expand=True, padx=5)
        self.games_scrollbar.pack(side="right", fill="y")

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
        self.dash_var = tk.BooleanVar(value=self.settings.get("dash", True))

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
        self.settings["dash"] = self.dash_var.get()
        if self.current_game:
            self.settings["last_selected_game"] = self.current_game
        
        with open(self.config_file, "w") as f:
            json.dump(self.settings, f, indent=4)

    def save_games(self):
        with open(self.games_file, "w") as f:
            json.dump(self.games, f, indent=4)

    def update_game_sidebar(self):
        # Clear existing game buttons
        for widget in self.games_scrollable_frame.winfo_children():
            widget.destroy()
        
        for game_id, game_info in self.games.items():
            if not game_info.get("enabled", True):
                continue
                
            # Create game button frame
            game_frame = tk.Frame(self.games_scrollable_frame, bg="#34495e")
            game_frame.pack(fill="x", pady=2, padx=5)
            
            # Game button
            game_btn = tk.Button(game_frame, text=game_info["name"], 
                               command=lambda gid=game_id: self.select_game(gid),
                               bg="#3498db", fg="white", relief="flat", font=("Arial", 9, "bold"),
                               activebackground="#2980b9", activeforeground="white")
            game_btn.pack(fill="x", pady=1)
            
            # Version label
            version_label = tk.Label(game_frame, text=f"v{game_info.get('version', '1.0.0')}", 
                                   font=("Arial", 7), bg="#34495e", fg="#bdc3c7")
            version_label.pack()

    def select_game(self, game_id):
        if game_id in self.games:
            self.current_game = game_id
            self.save_settings()
            if hasattr(self, 'content_frame'):
                self.show_home()

    def launch_game(self):
        if not self.current_game or self.current_game not in self.games:
            messagebox.showerror("Error", "No game selected!")
            return
        
        game_info = self.games[self.current_game]
        game_path = game_info["path"]
        
        if not os.path.exists(game_path):
            messagebox.showerror("Error", f"Game executable not found at: {game_path}")
            return
        
        try:
            subprocess.Popen([game_path])
            # Optionally minimize or close launcher
            # self.root.iconify()  # Minimize
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch game: {e}")

    def open_link(self, url):
        webbrowser.open(url)

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_content()
        
        if not self.current_game:
            # No game selected
            no_game_label = tk.Label(self.content_frame, text="No Game Selected", 
                                   font=("Arial", 18, "bold"), bg="#ecf0f1", fg="#7f8c8d")
            no_game_label.pack(pady=50)
            
            select_label = tk.Label(self.content_frame, text="Please select a game from the sidebar", 
                                  font=("Arial", 12), bg="#ecf0f1", fg="#95a5a6")
            select_label.pack()
            return
        
        game_info = self.games[self.current_game]
        
        # Game title
        title_label = tk.Label(self.content_frame, text=game_info["name"], 
                             font=("Arial", 20, "bold"), bg="#ecf0f1", fg="#2c3e50")
        title_label.pack(pady=20)
        
        # Game version
        version_label = tk.Label(self.content_frame, text=f"Version {game_info.get('version', '1.0.0')}", 
                               font=("Arial", 10), bg="#ecf0f1", fg="#7f8c8d")
        version_label.pack()
        
        # Launch button
        launch_button = tk.Button(self.content_frame, text="🎮 Launch Game", 
                                command=self.launch_game, font=("Arial", 14, "bold"),
                                bg="#27ae60", fg="white", activebackground="#229954",
                                relief="flat", padx=30, pady=10)
        launch_button.pack(pady=20)
        
        # Game description
        desc_label = tk.Label(self.content_frame, text="Description:", 
                            font=("Arial", 12, "bold"), bg="#ecf0f1", fg="#2c3e50")
        desc_label.pack(anchor="w", padx=20, pady=(20, 5))
        
        desc_text = tk.Text(self.content_frame, wrap="word", font=("Arial", 10), 
                          width=60, height=6, bg="white", relief="solid", bd=1)
        desc_text.insert("1.0", game_info["description"])
        desc_text.config(state="disabled")
        desc_text.pack(pady=5, padx=20, fill="x")
        
        # Game status
        status_frame = tk.Frame(self.content_frame, bg="#ecf0f1")
        status_frame.pack(pady=10, padx=20, fill="x")
        
        status_label = tk.Label(status_frame, text="Status:", font=("Arial", 10, "bold"), 
                              bg="#ecf0f1", fg="#2c3e50")
        status_label.pack(side="left")
        
        if os.path.exists(game_info["path"]):
            status_value = tk.Label(status_frame, text="✅ Ready to Play", 
                                  font=("Arial", 10), bg="#ecf0f1", fg="#27ae60")
        else:
            status_value = tk.Label(status_frame, text="❌ Game Not Found", 
                                  font=("Arial", 10), bg="#ecf0f1", fg="#e74c3c")
        status_value.pack(side="left", padx=(10, 0))

    def show_announcements(self):
        self.clear_content()
        
        title = tk.Label(self.content_frame, text="📢 Game Announcements", 
                        font=("Arial", 16, "bold"), bg="#ecf0f1", fg="#2c3e50")
        title.pack(pady=20)
        
        ann_text = tk.Text(self.content_frame, wrap="word", font=("Arial", 11), 
                         width=70, height=15, bg="white", relief="solid", bd=1)
        
        announcements = """🎉 Welcome to the Enhanced Game Launcher!

🔥 What's New in Version 0.2:
• Multiple game support with easy switching
• Improved user interface with better navigation
• Game version tracking and status indicators
• Enhanced settings management
• Better error handling and user feedback

🎮 Available Games:
• Ace Adventure - Our flagship RPG experience
• Puzzle Master - Brain-teasing puzzle challenges
• Jump Quest - Classic platforming action

📋 Upcoming Features:
• Automatic game updates
• Achievement tracking
• Cloud save synchronization
• Mod support integration
• Community features

💬 Stay Connected:
Follow us on BlueSky and check out our games on Itch.io for the latest updates and community discussions!

🐛 Found a bug? Have suggestions? 
Visit our website at 15.gay to report issues or share feedback.

Happy Gaming! 🎮
"""
        
        ann_text.insert("1.0", announcements)
        ann_text.config(state="disabled")
        ann_text.pack(pady=10, padx=20, fill="both", expand=True)

    def show_settings(self):
        self.clear_content()
        
        title = tk.Label(self.content_frame, text="⚙️ Launcher Settings", 
                        font=("Arial", 16, "bold"), bg="#ecf0f1", fg="#2c3e50")
        title.pack(pady=20)
        
        # Settings frame
        settings_frame = tk.LabelFrame(self.content_frame, text="Game Settings", 
                                     font=("Arial", 12, "bold"), bg="#ecf0f1", fg="#2c3e50")
        settings_frame.pack(pady=10, padx=20, fill="x")
        
        sound_check = tk.Checkbutton(settings_frame, text="🔊 Enable Sound Effects", 
                                   variable=self.sound_var, font=("Arial", 11),
                                   bg="#ecf0f1", fg="#2c3e50", activebackground="#ecf0f1",
                                   command=self.save_settings)
        sound_check.pack(anchor="w", padx=10, pady=5)
        
        dash_check = tk.Checkbutton(settings_frame, text="💨 Enable Dash Ability", 
                                  variable=self.dash_var, font=("Arial", 11),
                                  bg="#ecf0f1", fg="#2c3e50", activebackground="#ecf0f1",
                                  command=self.save_settings)
        dash_check.pack(anchor="w", padx=10, pady=5)
        
        # Current game info
        if self.current_game:
            current_frame = tk.LabelFrame(self.content_frame, text="Currently Selected", 
                                        font=("Arial", 12, "bold"), bg="#ecf0f1", fg="#2c3e50")
            current_frame.pack(pady=10, padx=20, fill="x")
            
            game_info = self.games[self.current_game]
            current_label = tk.Label(current_frame, text=f"🎮 {game_info['name']}", 
                                   font=("Arial", 11), bg="#ecf0f1", fg="#2c3e50")
            current_label.pack(anchor="w", padx=10, pady=5)

    def run(self):
        # Save settings when closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

# Run the launcher
if __name__ == "__main__":
    launcher = GameLauncher()
    launcher.run()