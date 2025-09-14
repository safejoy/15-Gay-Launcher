(() => {
  const _Scene_Message_createGoldWindow = Scene_Message.prototype.createGoldWindow;
  Scene_Message.prototype.createGoldWindow = function() {
    _Scene_Message_createGoldWindow.call(this);
    this._goldWindow.openness = 255;
  }

  Window_Message.prototype.terminateMessage = function() {
    this.close();
    $gameMessage.clear();
  };
})();

