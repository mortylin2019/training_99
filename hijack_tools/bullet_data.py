from dataclasses import dataclass

@dataclass
class Bullet:
    raw_x: int
    raw_y: int
    angle_index: int  # Offset 0x08 - Direction for Type 0/1/3
    active: int       # Offset 0x09
    type: int         # Offset 0x0A (0: Normal, 1: Homing, 2: Bounce, 3: Accel)
    timer: int        # Offset 0x0B
    index: int        # Offset 0x0C
    vx: int           # Offset 0x0D - Direct speed for Type 2
    vy: int           # Offset 0x0E - Direct speed for Type 2
    dist_to_player: float = 0.0 # Distance to player in pixels

    @property
    def x(self) -> int:
        return (self.raw_x >> 6) - 4

    @property
    def y(self) -> int:
        return (self.raw_y >> 6) - 4

    def update_dist(self, px, py):
        """Update distance to player using pixel coordinates."""
        dx = self.x - px
        dy = self.y - py
        self.dist_to_player = (dx*dx + dy*dy)**0.5

    def __repr__(self):
        # Type 2 uses simple vx/vy, others use angle_index to look up vectors
        move_info = f"v={self.vx},{self.vy}" if self.type == 2 else f"angle={self.angle_index}"
        return f"({self.x},{self.y},T{self.type},D{self.dist_to_player:.1f},{move_info})"
