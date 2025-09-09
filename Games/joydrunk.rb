#==============================================================================
# ** Drunk System Script for RPG Maker VX Ace
# Version: 1.0
# 
# Description: Adds a drunk system where consuming alcohol makes the player
# drunk with visual effects, stumbling movement, and hiccup sounds.
# Water and coffee can cure the drunk state.
#==============================================================================

#==============================================================================
# ** Configuration
#==============================================================================
module DrunkSystem
  # IDs of items that cause drunkenness (alcohol)
  ALCOHOL_ITEMS = [1, 2, 3]  # Change these to your alcohol item IDs
  
  # IDs of items that cure drunkenness (water, coffee, etc.)
  SOBER_ITEMS = [4, 5]       # Change these to your water/coffee item IDs
  
  # Drunk level required to start being drunk (1-100)
  DRUNK_THRESHOLD = 20
  
  # How much each alcohol item increases drunk level
  ALCOHOL_POWER = 25
  
  # How much drunk level decreases per second when drunk
  NATURAL_RECOVERY = 0.5
  
  # How much sober items reduce drunk level
  SOBER_POWER = 50
  
  # Chance of stumbling when moving (1-100)
  STUMBLE_CHANCE = 30
  
  # Frames between possible hiccups
  HICCUP_INTERVAL = 180
  
  # Hiccup messages (random selection)
  HICCUP_MESSAGES = ["Hic!", "*hic*", "Hiccup!", "*burp*", "Hic... hic..."]
  
  # Screen tint when drunk [red, green, blue, gray]
  DRUNK_TINT = [30, -30, -30, 30]
end

#==============================================================================
# ** Game_Player
#==============================================================================
class Game_Player < Game_Character
  attr_accessor :drunk_level
  
  alias drunk_initialize initialize
  def initialize
    drunk_initialize
    @drunk_level = 0
    @hiccup_timer = 0
    @stumble_delay = 0
  end
  
  alias drunk_update update
  def update
    drunk_update
    update_drunk_effects
  end
  
  def update_drunk_effects
    # Natural recovery over time
    if @drunk_level > 0
      @drunk_level -= DrunkSystem::NATURAL_RECOVERY / 60.0
      @drunk_level = [@drunk_level, 0].max
    end
    
    # Update screen tint
    if drunk?
      intensity = (@drunk_level / 100.0).clamp(0, 1)
      tint = DrunkSystem::DRUNK_TINT.map { |c| (c * intensity).to_i }
      $game_map.screen.start_tint(tint, 30)
    else
##      $game_map.screen.start_tint([0, 0, 0, 0], 30)
    end
    
    # Hiccup timer
    if drunk?
      @hiccup_timer += 1
      if @hiccup_timer >= DrunkSystem::HICCUP_INTERVAL
        @hiccup_timer = 0
        if rand(100) < 40  # 40% chance of hiccup
          show_hiccup
        end
      end
    else
      @hiccup_timer = 0
    end
    
    # Stumble delay
    @stumble_delay -= 1 if @stumble_delay > 0
  end
  
  def drunk?
    @drunk_level >= DrunkSystem::DRUNK_THRESHOLD
  end
  
  def add_alcohol(power = DrunkSystem::ALCOHOL_POWER)
    @drunk_level += power
    @drunk_level = [@drunk_level, 100].min
    
    # Show message when getting drunk
    if !drunk? && @drunk_level >= DrunkSystem::DRUNK_THRESHOLD
      $game_message.add("You feel dizzy...")
    end
  end
  
  def sober_up(power = DrunkSystem::SOBER_POWER)
    was_drunk = drunk?
    @drunk_level -= power
    @drunk_level = [@drunk_level, 0].max
    
    # Show message when sobering up
    if was_drunk && !drunk?
      $game_message.add("You feel much better now.")
    end
  end
  
  def show_hiccup
    message = DrunkSystem::HICCUP_MESSAGES.sample
    $game_map.screen.start_flash([255, 255, 255, 30], 10)
    
    # Show hiccup message above player
    balloon_id = 1  # Exclamation balloon, you can change this
    $game_player.balloon_id = balloon_id
    
    # You could also show it as a message
    # $game_message.add(message) if !$game_message.busy?
    
    # Or create a damage popup if you have that system
    show_hiccup_popup(message)
  end
  
  def show_hiccup_popup(text)
    # This creates a simple popup. You might need to adjust based on your setup
    if SceneManager.scene.is_a?(Scene_Map)
      sprite = Sprite.new
      sprite.bitmap = Bitmap.new(100, 32)
      sprite.bitmap.font.size = 16
      sprite.bitmap.font.color = Color.new(255, 255, 255)
      sprite.bitmap.draw_text(0, 0, 100, 32, text, 1)
      sprite.x = Graphics.width / 2 - 50
      sprite.y = Graphics.height / 2 - 100
      sprite.z = 1000
      
      # Fade out effect
      sprite.opacity = 255
      30.times do |i|
        sprite.opacity = 255 - (i * 8)
        sprite.y -= 1
        Graphics.update
      end
      sprite.dispose
    end
  end
  
  # Override movement to add stumbling
  alias drunk_move_straight move_straight
  def move_straight(d, turn_ok = true)
    if drunk? && @stumble_delay <= 0 && rand(100) < DrunkSystem::STUMBLE_CHANCE
      # Stumble in random direction
      stumble_direction = [2, 4, 6, 8].sample
      drunk_move_straight(stumble_direction, turn_ok)
      @stumble_delay = 30  # Prevent immediate stumbling again
      $game_map.screen.start_shake(2, 2, 10)  # Screen shake
    else
      drunk_move_straight(d, turn_ok)
    end
  end
end

#==============================================================================
# ** Game_Interpreter
#==============================================================================
class Game_Interpreter
  # Add script calls for easy use in events
  def make_drunk(level = DrunkSystem::ALCOHOL_POWER)
    $game_player.add_alcohol(level)
  end
  
  def make_sober(level = DrunkSystem::SOBER_POWER)
    $game_player.sober_up(level)
  end
  
  def drunk_level
    $game_player.drunk_level
  end
  
  def is_drunk?
    $game_player.drunk?
  end
end

#==============================================================================
# ** Game_Actor
#==============================================================================
class Game_Actor < Game_Battler
  alias drunk_use_item use_item
  def use_item(item)
    drunk_use_item(item)
    
    # Check if item is alcohol
    if DrunkSystem::ALCOHOL_ITEMS.include?(item.id)
      $game_player.add_alcohol
    end
    
    # Check if item sobers up
    if DrunkSystem::SOBER_ITEMS.include?(item.id)
      $game_player.sober_up
    end
  end
end

#==============================================================================
# ** DataManager
#==============================================================================
class << DataManager
  alias drunk_make_save_contents make_save_contents
  def make_save_contents
    contents = drunk_make_save_contents
    contents[:drunk_level] = $game_player.drunk_level
    contents
  end
  
  alias drunk_extract_save_contents extract_save_contents  
  def extract_save_contents(contents)
    drunk_extract_save_contents(contents)
    $game_player.drunk_level = contents[:drunk_level] || 0
  end
end

#==============================================================================
# Instructions for Use:
#==============================================================================
# 1. Change the ALCOHOL_ITEMS array to include your alcohol item IDs
# 2. Change the SOBER_ITEMS array to include your water/coffee item IDs  
# 3. Adjust other settings in the Configuration section as needed
#
# Script Calls you can use in events:
# - make_drunk(amount)     # Make player drunk with specified amount
# - make_sober(amount)     # Sober up player by specified amount
# - drunk_level            # Get current drunk level (0-100)
# - is_drunk?              # Check if player is currently drunk
#
# The system automatically handles:
# - Screen tinting when drunk
# - Random stumbling movement
# - Periodic hiccup messages/effects
# - Natural recovery over time
# - Saving/loading drunk state