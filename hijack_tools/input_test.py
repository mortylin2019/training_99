import time
import sys
from loguru import logger
from game_control import GameControl

def test_inputs():
    game = GameControl()
    if not game.launch_game():
        return

    logger.info("Starting Input Test...")
    
    # Ensure game is in play state (simple check)
    if game.get_game_state() == 0:
        game.press_enter()
        time.sleep(1)

    # Center roughly
    start_x, start_y = game.get_player_pos()
    logger.info(f"Start Pos: {start_x}, {start_y}")

    # Test bits 1, 2, 4, 8 individually
    test_bits = [
        (1, "Bit 1"),
        (2, "Bit 2"),
        (4, "Bit 4"),
        (8, "Bit 8"),
        (16, "Bit 16"),
        (32, "Bit 32")
    ]

    for bit, name in test_bits:
        logger.info(f"Testing {name}...")
        
        # Read before
        x1, y1 = game.get_player_pos()
        
        # Hold button for 0.5s
        game.write_int(0x00406d7c, bit)
        time.sleep(0.5)
        game.write_int(0x00406d7c, 0) # Stop
        time.sleep(0.1)
        
        # Read after
        x2, y2 = game.get_player_pos()
        
        dx = x2 - x1
        dy = y2 - y1
        
        result = "NO MOVE"
        if dy < 0: result = "MOVED UP"
        if dy > 0: result = "MOVED DOWN"
        if dx < 0: result = "MOVED LEFT"
        if dx > 0: result = "MOVED RIGHT"
        
        logger.info(f"Result {name}: Delta({dx}, {dy}) -> {result}")

if __name__ == "__main__":
    test_inputs()
