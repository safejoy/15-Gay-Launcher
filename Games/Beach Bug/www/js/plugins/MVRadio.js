//=============================================================================
// ★ MVRadio.js
//=============================================================================
/*:
 * @plugindesc ♫ Dynamic Radio System v2.0 - Listen to music anywhere! ♪
 * @author AnnaMisa
 * 
 * @help
 * ╔════════════════════════════════════════╗
 * ║  MVRadio - Your Game's Music Station!  ║
 * ╚════════════════════════════════════════╝
 * 
 * Features:
 * ♪ Stations play in background
 * ♪ Radio menu integration
 * 
 * @param RadioSetup
 * @text ♫ Radio Configuration
 * 
 * @param Stations
 * @parent RadioSetup
 * @type struct<Radio>[]
 * @text ♪ Radio Stations
 * @desc Configure your radio stations
 * @default ["{\"Name\":\"Hits FM\",\"Volume\":\"0.5\",\"Playlist\":\"[\\\"Battle1\\\"]\"}","{\"Name\":\"Chill FM\",\"Volume\":\"0.5\",\"Playlist\":\"[\\\"Theme1\\\"]\"}"]
 * 
 * @param GeneralSettings
 * @parent RadioSetup
 * @text ♫ General Settings
 * 
 * @param AutoplayRadio
 * @parent GeneralSettings
 * @text 🎵 Autoplay on Start
 * @type boolean
 * @default true
 * 
 * @param AllowInMenu
 * @parent GeneralSettings
 * @text 🎵 Enable in Menu
 * @type boolean
 * @default true
 * 
 * @param MuteOnMapChange
 * @parent GeneralSettings
 * @text 🔇 Mute on Map Change
 * @type boolean
 * @default true
 * 
 * @param RadioIcon
 * @text 📻 Radio Icon
 * @type number
 * @default 188
 * 
 * @param StationIcon
 * @text 🎵 Station Icon
 * @type number
 * @default 189
 * 
 * @param RadioSwitch
 * @parent GeneralSettings
 * @text 🔊 Radio Override Switch
 * @type switch
 * @desc When ON, radio plays regardless of map changes or menu closes (0 = OFF)
 * @default 0
 */
/*~struct~Radio:
 * @param Name
 * @text Station Name
 * @type string
 * 
 * @param Volume
 * @text Volume Level
 * @type number
 * @decimals 2
 * @min 0
 * @max 1
 * @default 0.5
 * 
 * @param Playlist
 * @text Music List
 * @type file[]
 * @dir audio/bgm
 */

var Imported = Imported || {};
Imported.MVRadio = true;

const MVRadio = {
    name: 'MVRadio',
    version: 2.0,
    params: PluginManager.parameters('MVRadio'),
    stations: [],
    currentStation: 1,
    isPlaying: false,
    initialized: false
};

// Initialize radio system
MVRadio.initialize = function() {
    if (this.initialized) return;
    
    // Initialize audio buffers if they don't exist
    AudioManager._bgmBuffers = AudioManager._bgmBuffers || [];
    
    const stationsData = JSON.parse(this.params['Stations'] || '[]');
    this.stations = stationsData.map(station => {
        const data = JSON.parse(station);
        return {
            name: data.Name,
            volume: Number(data.Volume),
            playlist: JSON.parse(data.Playlist),
            currentSong: 0,
            muted: false
        };
    });

    this.radioSwitch = Number(this.params['RadioSwitch']);

    if (this.stations.length === 0) return;

    this.stations.forEach((station, index) => {
        AudioManager._bgmBuffers[index + 1] = this.createAudioBuffer(station);
    });

    this.initialized = true;
};

// Core audio functions
MVRadio.createAudioBuffer = function(station) {
    const buffer = AudioManager.createBuffer('bgm', station.playlist[0]);
    buffer.volume = 0;
    buffer.play(true, 0);
    return buffer;
};

MVRadio.toggleRadio = function() {
    if (!this.initialized) return;
    
    this.isPlaying = !this.isPlaying;
    const station = this.stations[this.currentStation - 1];
    if (AudioManager._bgmBuffers[this.currentStation]) {
        AudioManager._bgmBuffers[this.currentStation].volume = 
            this.isPlaying ? station.volume : 0;
    }
};

MVRadio.changeStation = function(direction) {
    if (!this.initialized) return;
    
    const oldStation = this.currentStation;
    this.currentStation = this.currentStation + direction;
    
    if (this.currentStation > this.stations.length) {
        this.currentStation = 1;
    } else if (this.currentStation < 1) {
        this.currentStation = this.stations.length;
    }
    
    if (this.isPlaying) {
        AudioManager._bgmBuffers[oldStation].volume = 0;
        AudioManager._bgmBuffers[this.currentStation].volume = 
            this.stations[this.currentStation - 1].volume;
    }
};

// Window class
function Window_Radio() {
    this.initialize.apply(this, arguments);
}

Window_Radio.prototype = Object.create(Window_Selectable.prototype);
Window_Radio.prototype.constructor = Window_Radio;

Window_Radio.prototype.initialize = function() {
    const width = Graphics.boxWidth;
    const height = Graphics.boxHeight;
    Window_Selectable.prototype.initialize.call(this, 0, 0, width, height);
    this._iconRotation = 0;
    this._animationCount = 0;
    this.refresh();
};

Window_Radio.prototype.update = function() {
    Window_Selectable.prototype.update.call(this);
    
    if (Input.isTriggered('ok')) {
        SoundManager.playOk();
        MVRadio.toggleRadio();
        this.refresh();
    }
    
    if (Input.isTriggered('cancel') || TouchInput.isCancelled()) {
        this.processCancel();
    }
    
    if (Input.isTriggered('left')) {
        SoundManager.playCursor();
        MVRadio.changeStation(-1);
        this.refresh();
    }
    
    if (Input.isTriggered('right')) {
        SoundManager.playCursor();
        MVRadio.changeStation(1);
        this.refresh();
    }

    if (MVRadio.isPlaying) {
        this._iconRotation = (this._iconRotation + 2) % 360;
        if (this._animationCount++ % 5 === 0) this.refresh();
    }
};

Window_Radio.prototype.processCancel = function() {
    SoundManager.playCancel();
    if (!$gameSwitches.value(MVRadio.radioSwitch)) {
        MVRadio.isPlaying = false;
        if (AudioManager._bgmBuffers[MVRadio.currentStation]) {
            AudioManager._bgmBuffers[MVRadio.currentStation].volume = 0;
        }
    }
    SceneManager.pop();
};

Window_Radio.prototype.refresh = function() {
    this.contents.clear();
    const station = MVRadio.stations[MVRadio.currentStation - 1];
    
    // Draw radio icon
    this.drawRotatedIcon(Number(MVRadio.params['RadioIcon']), 100, 50, this._iconRotation);
    
    // Draw station info
    this.drawIcon(Number(MVRadio.params['StationIcon']), 60, 120);
    this.drawText(`${station.name}`, 100, 120, 200);
    this.drawText(`Status: ${MVRadio.isPlaying ? 'Playing' : 'Stopped'}`, 100, 160);
    
    // Draw navigation
    this.drawText('◄', 20, 120);
    this.drawText('►', 300, 120);
    
    // Draw controls
    this.drawText('Controls:', 60, 200);
    this.drawText('OK - Toggle Radio', 80, 230);
    this.drawText('←/→ - Change Station', 80, 260);
    this.drawText('Cancel - Exit', 80, 290);
};

Window_Radio.prototype.drawRotatedIcon = function(iconIndex, x, y, rotation) {
    const bitmap = ImageManager.loadSystem('IconSet');
    const pw = Window_Base._iconWidth;
    const ph = Window_Base._iconHeight;
    const sx = iconIndex % 16 * pw;
    const sy = Math.floor(iconIndex / 16) * ph;
    
    this.contents.context.save();
    this.contents.context.translate(x + pw/2, y + ph/2);
    this.contents.context.rotate(rotation * Math.PI / 180);
    this.contents.blt(bitmap, sx, sy, pw, ph, -pw/2, -ph/2);
    this.contents.context.restore();
};

// Scene integration
function Scene_Radio() {
    this.initialize.apply(this, arguments);
}

Scene_Radio.prototype = Object.create(Scene_MenuBase.prototype);
Scene_Radio.prototype.constructor = Scene_Radio;

Scene_Radio.prototype.initialize = function() {
    Scene_MenuBase.prototype.initialize.call(this);
};

Scene_Radio.prototype.create = function() {
    Scene_MenuBase.prototype.create.call(this);
    this._radioWindow = new Window_Radio();
    this.addWindow(this._radioWindow);
};

// Plugin initialization
MVRadio.initialize();

// Add radio command to menu
const _Window_MenuCommand_addMainCommands = Window_MenuCommand.prototype.addMainCommands;
Window_MenuCommand.prototype.addMainCommands = function() {
    _Window_MenuCommand_addMainCommands.call(this);
    if (MVRadio.params['AllowInMenu'] === 'true') {
        this.addCommand('Radio', 'radio', true);
    }
};

// Handle radio command selection
const _Scene_Menu_createCommandWindow = Scene_Menu.prototype.createCommandWindow;
Scene_Menu.prototype.createCommandWindow = function() {
    _Scene_Menu_createCommandWindow.call(this);
    this._commandWindow.setHandler('radio', this.commandRadio.bind(this));
};

Scene_Menu.prototype.commandRadio = function() {
    SceneManager.push(Scene_Radio);
};

const _Scene_Base_terminate = Scene_Base.prototype.terminate;
Scene_Base.prototype.terminate = function() {
    _Scene_Base_terminate.call(this);
    if (MVRadio.isPlaying && !$gameSwitches.value(MVRadio.radioSwitch)) {
        MVRadio.isPlaying = false;
        if (AudioManager._bgmBuffers[MVRadio.currentStation]) {
            AudioManager._bgmBuffers[MVRadio.currentStation].volume = 0;
        }
    }
};
