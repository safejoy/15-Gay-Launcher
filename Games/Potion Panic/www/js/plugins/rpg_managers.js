//=============================================================================
// Enemy Health Bars Plugin
//=============================================================================

/*:
 * @plugindesc Adds health bars to enemies in side view battle based on their position.
 * @author Axial Escape
 *
 * @param Bar Width
 * @desc The width of the health bars in pixels.
 * @default 100
 *
 * @param Bar Height
 * @desc The height of the health bars in pixels.
 * @default 10
 *
 * @param Display Condition
 * @desc The JavaScript condition that determines whether the health bar should be displayed.
 * @default true
 * 
 * @param Gradient Start Color
 * @desc The start color of the health bar gradient in hex code format.
 * @default #AA1818
 *
 * @param Gradient End Color
 * @desc The end color of the health bar gradient in hex code format.
 * @default #79CF16
 *
 * @help
 * This plugin adds health bars to enemies in side view battle. The position of
 * the health bars is dynamically adjusted based on the position of the enemy in
 * battle. The Display Condition parameter should be a JavaScript condition that
 * determines whether the health bar should be displayed for a given enemy.
 * To use this plugin, simply install it and the health bars will appear
 * automatically in battle.
 */

(function() {

    var parameters = PluginManager.parameters('Enemy_Health_Bars');
    var barWidth = Number(parameters['Bar Width'] || 100);
    var barHeight = Number(parameters['Bar Height'] || 10);
    var displayCondition = parameters['Display Condition'];
    var gradientStartColor = parameters['Gradient Start Color'] || '#00FF00';
    var gradientEndColor = parameters['Gradient End Color'] || '#FF0000';

    var _Spriteset_Battle_createEnemies = Spriteset_Battle.prototype.createEnemies;
    Spriteset_Battle.prototype.createEnemies = function() {
        _Spriteset_Battle_createEnemies.call(this);
        this._enemyHealthBars = [];
        for (var i = 0; i < this._enemySprites.length; i++) {
            var sprite = this._enemySprites[i];
            var x = sprite.x - (barWidth / 2);
            var y = sprite.y - sprite.height - barHeight;
            var healthBar = new Sprite(new Bitmap(barWidth, barHeight));
            healthBar.x = x;
            healthBar.y = y;
            healthBar.bitmap.fillAll('#000000');
            healthBar.bitmap.gradientFillRect(1, 1, barWidth - 2, barHeight - 2, gradientStartColor, gradientEndColor);
            // healthBar.bitmap.drawText('some text', 1, 1, barWidth, barHeight, 'left');
            this._enemyHealthBars.push(healthBar);
            this.addChild(healthBar);
        }
    };

    var _Spriteset_Battle_update = Spriteset_Battle.prototype.update;
    Spriteset_Battle.prototype.update = function() {
        _Spriteset_Battle_update.call(this);
        for (var i = 0; i < this._enemySprites.length; i++) {
            var sprite = this._enemySprites[i];
            var healthBar = this._enemyHealthBars[i];
            var display = eval(displayCondition);
            if (display) {
                healthBar.visible = true;
                healthBar.x = sprite.x - (barWidth / 2);
                healthBar.y = sprite.y - sprite.height - barHeight;
                var currentHp = sprite._enemy.hp;
                var maxHp = sprite._enemy.mhp;
                // this old method does not update when enemies gain health
                /*if (currentHp <  maxHp){
                    var fillLength = Math.floor((currentHp / maxHp) * (barWidth - 2));
                    healthBar.bitmap.fillRect(fillLength, 1, barWidth, barHeight - 2, '#000000');
                }*/
                // new method
                if(currentHp != maxHp){
                    var fillLength = Math.floor((currentHp / maxHp) * (barWidth - 2));
                    healthBar.bitmap.fillRect(fillLength, 1, barWidth, barHeight - 2, '#000000');
                }
            }
            else {
                healthBar.visible = false;
            }
        }
    };

})();
