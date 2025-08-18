import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser
import json
import os

# ------------------------------
# CONFIG HANDLING
# ------------------------------
CONFIG_FILE = "settings.json"

default_settings = {
    "sound": True,
    "dash": True
}

def load_settings():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return default_settings.copy()
    else:
        return default_settings.copy()

def save_settings():
    settings = {
        "sound": sound_var.get(),
        "dash": dash_var.get()
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(settings, f, indent=4)

# ------------------------------
# GAME LAUNCH FUNCTION
# ------------------------------
def launch_game():
    game_path = "path/to/your/RPG_Maker_Game.exe"  # Replace with your game's actual path
    try:
        subprocess.Popen([game_path])
        # root.destroy()  # Uncomment if you want launcher to close after game starts
    except FileNotFoundError:
        messagebox.showerror("Error", f"Game executable not found at: {game_path}")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# ------------------------------
# LINKS
# ------------------------------
def open_link(url):
    webbrowser.open(url)

# ------------------------------
# ANNOUNCEMENTS
# ------------------------------
def show_announcements():
    for widget in content_frame.winfo_children():
        widget.destroy()

    ann_title = tk.Label(content_frame, text="Game Announcements", font=("Arial", 14, "bold"))
    ann_title.pack(pady=10)

    ann_text = tk.Text(content_frame, wrap="word", font=("Arial", 10), width=50, height=10)
    ann_text.insert("1.0", 
        "📢 Latest News:\n\n"
        "- Version 0.1 Launcher released!\n"
        "- Added basic features.\n"
        "- Updating colors.\n\n"
        "- Future Plans:\n"
        "- More customization options.\n\n"

        "Stay tuned for more updates!\n"
        "Follow us on BlueSky and Itch for the latest news!"
    )
    ann_text.config(state="disabled")  # Read-only
    ann_text.pack(pady=10)

# ------------------------------
# MAIN MENU (HOME SCREEN)
# ------------------------------
def show_home():
    for widget in content_frame.winfo_children():
        widget.destroy()

    title_label = tk.Label(content_frame, text="Potions Panic!", font=("Arial", 16))
    title_label.pack(pady=20)

    launch_button = tk.Button(content_frame, text="Launch Game", command=launch_game, font=("Arial", 12), bg="#4CAF50", fg="white")
    launch_button.pack(pady=10)

    info_label = tk.Label(content_frame, text="A cute RPG game about potions, love, and frogs", font=("Arial", 10))
    info_label.pack(pady=5)

    # ------------------------------
    # SETTINGS (Saved to File)
    # ------------------------------
    settings_label = tk.Label(content_frame, text="Game Settings", font=("Arial", 12, "bold"))
    settings_label.pack(pady=10)

    sound_check = tk.Checkbutton(content_frame, text="Enable Sound", variable=sound_var, font=("Arial", 10), command=save_settings)
    dash_check = tk.Checkbutton(content_frame, text="Enable Dash", variable=dash_var, font=("Arial", 10), command=save_settings)

    sound_check.pack(anchor="w", padx=20)
    dash_check.pack(anchor="w", padx=20)

# ------------------------------
# MAIN WINDOW
# ------------------------------
root = tk.Tk()
root.title("15 Gay Launcher")
root.geometry("600x400")

# Create main layout: Sidebar + Content
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

# Sidebar
sidebar = tk.Frame(main_frame, bg="#2c3e50", width=150)
sidebar.pack(side="left", fill="y")

# Content area
content_frame = tk.Frame(main_frame, bg="#ecf0f1")
content_frame.pack(side="right", fill="both", expand=True)

# Load saved settings
loaded_settings = load_settings()
sound_var = tk.BooleanVar(value=loaded_settings.get("sound", True))
dash_var = tk.BooleanVar(value=loaded_settings.get("dash", True))

# Sidebar Buttons
home_btn = tk.Button(sidebar, text="🏠 Home", command=show_home, bg="#34495e", fg="white", relief="flat")
home_btn.pack(fill="x", pady=5)

ann_btn = tk.Button(sidebar, text="📰 Announcements", command=show_announcements, bg="#34495e", fg="white", relief="flat")
ann_btn.pack(fill="x", pady=5)

web_btn = tk.Button(sidebar, text="🌐 Studio Website", command=lambda: open_link("https://15.gay/"), bg="#34495e", fg="white", relief="flat")
web_btn.pack(fill="x", pady=5)

social_btn = tk.Button(sidebar, text="☁️ BlueSky", command=lambda: open_link("https://bsky.app/profile/15gay.itch.io"), bg="#34495e", fg="white", relief="flat")
social_btn.pack(fill="x", pady=5)

social_btn = tk.Button(sidebar, text="👾 Itch", command=lambda: open_link("https://15gay.itch.io/"), bg="#34495e", fg="white", relief="flat")
social_btn.pack(fill="x", pady=5)

# Start on home screen
show_home()

# Save settings when closing launcher
root.protocol("WM_DELETE_WINDOW", lambda: (save_settings(), root.destroy()))

root.mainloop()
