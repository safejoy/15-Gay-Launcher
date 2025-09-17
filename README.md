# 15 Gay Launcher

![Launcher Screen Shot](https://github.com/safejoy/15-Gay-Launcher/blob/master/Images/Screenshot_233.png)

> *"15 Gay" - It's leet speak for "Is Gay"*

A simple, retro-styled game launcher specifically designed for RPG Maker games. Inspired by both classic and modern Minecraft launchers, this launcher provides a nostalgic gaming experience with modern features.

## 🎮 Features

- **🎨 Dual Themes**: Light and dark theme options
- **🎵 Background Music**: Retro-styled background music reminiscent of the cracker.exe era
- **📢 Announcements**: Stay updated with the latest news and updates
- **🔗 Social Integration**: Direct links to our websites and social media
- **📊 Time Tracking**: Optional gameplay time tracking (configurable in settings)
- **🎯 Studio Banners**: Promotional banners for our games and services
- **⏳ Authentic Launch Experience**: 35-second loading bar for that classic launcher feel
- **🌸 Hidden Easter Egg**: Discover the secret flower game for special unlocks
- **🎲 Built-in Games**: Three playable games included in the launcher
- **🎪 RPG Maker Focus**: Specialized for RPG Maker MV and newer games

## 🖥️ System Requirements

- **OS**: Windows 7/8/10 or Mac OSX 10.10 or later
- **Processor**: Intel Core 2 Duo or better
- **Memory**: 2GB RAM or more
- **Graphics**: DirectX 9/OpenGL 4.1 capable GPU
- **Storage**: 2-4GB free space (current: ~2GB, may expand to 4GB with future updates)
- **Display**: 1280x768 resolution or higher
- **Python**: Python 3.7+ (for development/building from source)
- **RPG Maker**: Compatible with RPG Maker MV and newer versions

## 📥 Installation

### Option 1: Download Release
1. Go to the [Releases](https://github.com/safejoy/15-Gay-Launcher/releases) page
2. Download the latest version
3. Extract the files to your desired location
4. Run `15 Gay Launcher.exe`

### Option 2: Build from Source

#### Prerequisites
- Python 3.7 or newer
- pip (Python package manager)
- Git

#### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/safejoy/15-Gay-Launcher.git
   cd 15-Gay-Launcher
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv launcher-env
   
   # On Windows:
   launcher-env\Scripts\activate
   
   # On macOS/Linux:
   source launcher-env/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python src/main.py
   ```

#### Building an Executable
To create a standalone executable:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller --onefile --windowed src/main.py --name "15 Gay Launcher"
   ```

3. The executable will be in the `dist/` folder

## 🚀 Usage

1. **Launch the Application**: Run the executable
2. **Select a Game**: Browse through available RPG Maker games
3. **Customize Settings**: 
   - Choose your preferred theme (light/dark)
   - Enable/disable time tracking
   - Adjust audio settings
4. **Launch and Play**: Click the launch button and enjoy the authentic loading experience
5. **Discover Secrets**: Explore the launcher to find the hidden flower game

## 🎵 Audio Features

The launcher includes background music styled after classic cracker scene music. Audio can be controlled through the settings menu.

## 📊 Time Tracking

Optional feature that tracks how long you play each game. Data is stored locally and can be viewed in the launcher interface. This feature can be disabled in settings for privacy.

## 🔧 Configuration

Settings are stored in JSON format and include:
- Theme preferences
- Audio settings
- Time tracking preferences
- Game library paths

## 🎮 Included Games

The launcher comes with three built-in games plus a hidden easter egg game. All games are compatible with the RPG Maker engine.

## 🚧 Development Status

This is an active project with planned features including:
- Per-game background music themes
- Additional color themes
- More RPG Maker game integrations
- Enhanced UI features

## 🤝 Contributing

We welcome contributions! Please feel free to:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

- **Launcher**: Open source under [MIT License](LICENSE) - free to use, modify, and distribute
- **Included Games**: Individual games retain their original licenses and are not open source
- **Assets**: Some assets may have separate licensing terms

## 🔗 Related Projects

- [Potions Panic!](https://github.com/safejoy/potions-panic) - Our main commercial RPG Maker game (standalone release)

## ⚠️ Important Notes

- **Free Forever**: This launcher and its included games will always be free
- **Cross-Platform**: Supports Windows and macOS (see system requirements)
- **RPG Maker Focus**: Specifically designed for RPG Maker MV and newer games
- **Standalone Games**: Our commercial projects like Potions Panic! are separate releases
- **Game Licensing**: While the launcher is open source, included RPG Maker games maintain their individual licensing

## 📞 Support

For support, bug reports, or feature requests:
- Open an issue on this repository
- Visit our website [link]
- Follow us on social media [links]

## 🏗️ Project Structure

```
15-Gay-Launcher/
├── src/                    # Source code
├── assets/                 # Images, audio, themes
├── games/                  # Game files and metadata
├── data/                   # Configuration and data files
└── docs/                   # Documentation
```

---

*Built with ❤️ for the RPG Maker community*
