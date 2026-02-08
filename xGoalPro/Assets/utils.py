# Window and game constants
WINDOW_W = 480
WINDOW_H = 800
LANES = 3
LANE_PADDING = 60
PLAYER_Y = WINDOW_H - 140  # baseline where ball sits


def lane_to_x(lane: int) -> float:
    """Convert lane index (0 - LANES-1) to X position in pixels."""
    usable_w = WINDOW_W - 2 * LANE_PADDING
    lane_w = usable_w / (LANES - 1) if LANES > 1 else usable_w
    return LANE_PADDING + lane * lane_w
