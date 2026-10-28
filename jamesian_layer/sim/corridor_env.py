"""Corridor simulation environment (spec section 5.9).

Implements the continuous physical environment used by the end-to-end
benchmarks and split-screen video demo. Benchmark harnesses place the rover
nose exactly at the barrier after ``reset()`` (``env.position =
env.barrier_pos``) so locked-rotor stall begins at cycle 1, keeping the
pinned Test 1 thermal timeline intact (breaker trip cycle 3 @12 s, control
streak 8 @32 s, derate cycle 9 @36 s).
"""


class CorridorEnv:
    def __init__(
        self,
        mass: float = 35.0,
        corridor_length: float = 100.0,
        barrier_pos: float = 25.0,
        friction_coeff: float = 25.0,
        thrust_gain: float = 6.25,
        dt: float = 0.005,
    ):
        self.mass = mass
        self.corridor_length = corridor_length
        self.barrier_pos = barrier_pos
        self.c_d = friction_coeff
        self.kappa_F = thrust_gain
        self.dt = dt
        self.position = 0.0
        self.velocity = 0.0
        self.current = 4.0

    def reset(self) -> tuple[float, float, float, bool]:
        self.position = 0.0
        self.velocity = 0.0
        self.current = 4.0
        return self.position, self.velocity, self.current, False

    def step(self, velocity: float, heading: float) -> tuple[float, float, float, bool]:
        if self.position >= self.barrier_pos and velocity > 0:
            self.velocity = 0.0
            self.current = 20.0
            return self.position, self.velocity, self.current, True
        F_drive = self.kappa_F * abs(velocity)
        F_drag = self.c_d * abs(self.velocity)
        self.velocity += (F_drive - F_drag) / self.mass * self.dt
        self.position = min(self.position + self.velocity * self.dt, self.corridor_length)
        self.current = 4.0 if velocity > 0.0 else 0.0
        return self.position, self.velocity, self.current, False
