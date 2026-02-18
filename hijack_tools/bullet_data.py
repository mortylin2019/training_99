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

    @property
    def x(self) -> int:
        return (self.raw_x >> 6) - 4

    @property
    def y(self) -> int:
        return (self.raw_y >> 6) - 4

    def __repr__(self):
        # Type 2 uses simple vx/vy, others use angle_index to look up vectors
        move_info = f"v={self.vx},{self.vy}" if self.type == 2 else f"angle={self.angle_index}"
        return f"({self.x},{self.y},T{self.type},{move_info})"
