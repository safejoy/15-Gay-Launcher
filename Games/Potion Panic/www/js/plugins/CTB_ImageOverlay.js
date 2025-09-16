/*=============================================================================*\
 * CTB ImageOverlay
 * By CT_Bolt
 * CTB_ImageOverlay.js
 * Version: 1.00
 * Terms of Use:
 *  Free for commercial or non-commercial use
 *
/*=============================================================================*/
var CTB = CTB || {}; CTB.ImageOverlay  = CTB.ImageOverlay || {};
var Imported = Imported || {}; Imported["CT_Bolt ImageOverlay"] = 1.00;
//=============================================================================//

/*:
 * @plugindesc v1.00 CT_Bolt's ImageOverlay Plugin
 * @author CT_Bolt
 *
 * @param Overlay Image
 * @text Overlay Image
 * @desc The image used as an overlay
 * @type file
 * @dir img/pictures/
 * @default 
 *
 * @param Show Overlay
 * @text Show Overlay
 * @desc Is the overlay shown by default
 * You can also use Javascript. Leave blank to hide by default.
 * @default true
 *
 * @help
 * CT_Bolt's ImageOverlay
 * Version 1.00
 * CT_Bolt
 *
 * Script Calls:
 *  Show/Hide the overlay:
 *     CTB.ImageOverlay.Visible(value)
 *  Examples:
 *     CTB.ImageOverlay.Visible(true)
 *     CTB.ImageOverlay.Visible(false)
 *
 *  Change overlay filename:
 *     CTB.ImageOverlay.Change(filename)
 *  Example:
 *     CTB.ImageOverlay.Change('Grid')
 *
 *  Revert to previous overlay filename:
 *     CTB.ImageOverlay.Revert()
 *
 */
//=============================================================================
//=============================================================================

"use strict";
(function ($_$) {
    function getPluginParameters() {var a = document.currentScript || (function() { var b = document.getElementsByTagName('script'); return b[b.length - 1]; })(); return PluginManager.parameters(a.src.substring((a.src.lastIndexOf('/') + 1), a.src.indexOf('.js')));} $_$.params = getPluginParameters();
	
	const sceneFunctionCombos = [
		{sceneName: 'Scene_Map', functionName: 'createDisplayObjects'},
		{sceneName: 'Scene_Battle', functionName: 'create'},
		{sceneName: 'Scene_Title', functionName: 'create'},
		{sceneName: 'Scene_Menu', functionName: 'create'},
		{sceneName: 'Scene_Item', functionName: 'create'},
		{sceneName: 'Scene_Skill', functionName: 'create'},
		{sceneName: 'Scene_Equip', functionName: 'create'},
		{sceneName: 'Scene_Status', functionName: 'create'},
		{sceneName: 'Scene_Options', functionName: 'create'},
		{sceneName: 'Scene_File', functionName: 'create'},
		{sceneName: 'Scene_GameEnd', functionName: 'create'},
		{sceneName: 'Scene_Shop', functionName: 'create'},
		{sceneName: 'Scene_Name', functionName: 'create'},
		{sceneName: 'Scene_Gameover', functionName: 'create'}
	];
	
	sceneFunctionCombos.forEach(function(v){		
		$_$[v.sceneName+'.prototype.'+v.functionName] = window[v.sceneName].prototype[v.functionName];
		window[v.sceneName].prototype[v.functionName] = function() {
			$_$[v.sceneName+'.prototype.'+v.functionName].apply(this, arguments);
			this.createOverlayWindow();
		};
	});
	
	Scene_Base.prototype.createOverlayWindow = function() {
		this.createWindowLayerEx('imageOverlay');
		this._imageOverlayWindow = new Window_ImageOverlay(0, 0);
		if ($gameSystem.showOverlay === undefined) {$gameSystem.showOverlay = $_$.params['Show Overlay'];};
		if ($gameSystem.showOverlay === ""){$gameSystem.showOverlay = false;};
		CTB.ImageOverlay.Visible($gameSystem.showOverlay);
		this._windowLayerEx['imageOverlay'].addChild(this._imageOverlayWindow);
	};
	
	Scene_Base.prototype.createWindowLayerEx = function(layerName) {
		this._windowLayerEx = this._windowLayerEx || [];
		var width = Graphics.boxWidth;
		var height = Graphics.boxHeight;
		var x = (Graphics.width - width) / 2;
		var y = (Graphics.height - height) / 2;
		this._windowLayerEx[layerName] = new WindowLayer();
		this._windowLayerEx[layerName].move(x, y, width, height);
		this.addChild(this._windowLayerEx[layerName]);
	};
	
	//-----------------------------------------------------------------------------
	// Window_ImageOverlay
	//-----------------------------------------------------------------------------

	function Window_ImageOverlay() {
		this.initialize.apply(this, arguments);
	}

	Window_ImageOverlay.prototype = Object.create(Window_Base.prototype);
	Window_ImageOverlay.prototype.constructor = Window_ImageOverlay;

	Window_ImageOverlay.prototype.initialize = function(x, y) {
		var width = this.windowWidth();
		var height = this.windowHeight();
		Window_Base.prototype.initialize.call(this, x, y, width, height);
		this.refresh();
	};

	Window_ImageOverlay.prototype.windowWidth = function() {		
		return Graphics.width;
	};

	Window_ImageOverlay.prototype.windowHeight = function() {
		return Graphics.height;
	};

	Window_ImageOverlay.prototype.refresh = function() {
		this.contents.clear();
	};

	Window_ImageOverlay.prototype.open = function() {
		this.refresh();
		Window_Base.prototype.open.call(this);
	};
	
	Window_ImageOverlay.prototype._refreshBack = function() {
		var m = 0;
		var w = this._width;
		var h = this._height;
		var bitmap = new Bitmap(w, h);
		this._windowBackSprite.bitmap = bitmap;
		this._windowBackSprite.setFrame(0, 0, w, h);
		this._windowBackSprite.move(m, m);
		if (w > 0 && h > 0 && this._windowskin) {
			bitmap.blt(this._windowskin, 0, 0, this._windowskin.width, this._windowskin.height, 0, 0, w, h);
			var tone = this._colorTone;
			bitmap.adjustTone(tone[0], tone[1], tone[2]);
		}
	};

	Window_ImageOverlay.prototype._refreshFrame = function() {};
	
	Window_ImageOverlay.prototype.loadWindowskin = function() {
		$gameSystem.overlayImage = $gameSystem.overlayImage || $_$.params['Overlay Image']
		this.windowskin = ImageManager.loadPicture($gameSystem.overlayImage);
	};
	
	CTB.ImageOverlay.Visible = function(value){
		SceneManager._scene._imageOverlayWindow.visible = eval(value);
		$gameSystem.showOverlay = SceneManager._scene._imageOverlayWindow.visible;
	};
	
	CTB.ImageOverlay.Change = function(filename){
		$gameSystem.overlayImage_original = $gameSystem.overlayImage;
		$gameSystem.overlayImage = filename;
		SceneManager._scene._imageOverlayWindow.loadWindowskin();
	};
		
	CTB.ImageOverlay.Revert = function(){
		if ($gameSystem.overlayImage_original){
			const temp = $gameSystem.overlayImage;
			$gameSystem.overlayImage = $gameSystem.overlayImage_original
			$gameSystem.overlayImage_original = temp;
			SceneManager._scene._imageOverlayWindow.loadWindowskin();
		};
	};
	
})(CTB.ImageOverlay);