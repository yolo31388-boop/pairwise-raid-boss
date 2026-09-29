"""团本BOSS机制系统"""
import math
from dataclasses import dataclass, field
from typing import Optional

MAX_THREAT_ENTRIES = 20      # 召唤物仇恨列表上限
MIN_DAMAGE_FRACTION = 0.1    # 减伤后至少保留10%伤害

@dataclass
class Player:
    pid: str
    x: float
    y: float
    hp: float = 100.0

@dataclass
class AOE:
    shape: str  # circle/sector/rect
    x: float
    y: float
    radius: float = 0
    angle: float = 0  # 扇形朝向/矩形旋转角
    width: float = 0  # 扇形张角(弧度)/矩形宽
    height: float = 0

@dataclass
class Add:
    aid: str
    hp: float
    threat: list = field(default_factory=list)  # (player_id, threat_value)

class Boss:
    def __init__(self):
        self.hp: float = 1000.0
        self.max_hp: float = 1000.0
        self.phase: int = 1
        self.phase_thresholds: list = [0.7, 0.4]  # 血量百分比区间边界
        self.casting: Optional[str] = None
        self.interrupt_immune: bool = False
        self.enrage_timer: float = 0.0
        self.enraged: bool = False
        self.adds: list[Add] = []
        self.active_aoes: list[AOE] = []
        self.projectiles: list = []  # 飞行道具
        self.damage_reduction: float = 0.0  # 减伤比例(乘法叠加后的等效值)

    def take_damage(self, dmg: float):
        # 阶段转换按血量区间依次触发，跳变时逐个经过中间阶段
        self.hp -= dmg
        pct = self.hp / self.max_hp
        while self.phase - 1 < len(self.phase_thresholds) and \
                pct <= self.phase_thresholds[self.phase - 1]:
            self.transition_phase(self.phase + 1)

    def is_in_aoe(self, player: Player, aoe: AOE) -> bool:
        # 按实际形状做几何判定
        dx = player.x - aoe.x
        dy = player.y - aoe.y
        if aoe.shape == "circle":
            return math.hypot(dx, dy) <= aoe.radius
        if aoe.shape == "sector":
            if math.hypot(dx, dy) > aoe.radius:
                return False
            if dx == 0 and dy == 0:
                return True
            diff = (math.atan2(dy, dx) - aoe.angle + math.pi) % (2 * math.pi) - math.pi
            return abs(diff) <= aoe.width / 2
        if aoe.shape == "rect":
            # 以(x, y)为中心、按angle旋转的矩形
            cos_a = math.cos(-aoe.angle)
            sin_a = math.sin(-aoe.angle)
            lx = dx * cos_a - dy * sin_a
            ly = dx * sin_a + dy * cos_a
            return abs(lx) <= aoe.width / 2 and abs(ly) <= aoe.height / 2
        return False

    def spawn_add(self, add: Add):
        # 仇恨列表超出上限时按威胁值淘汰最低的
        if len(add.threat) > MAX_THREAT_ENTRIES:
            add.threat = sorted(add.threat, key=lambda t: t[1],
                                reverse=True)[:MAX_THREAT_ENTRIES]
        self.adds.append(add)

    def can_interrupt(self) -> bool:
        # 免疫阶段不可打断
        return self.casting is not None and not self.interrupt_immune

    def reset_encounter(self):
        # 团灭重置：狂暴计时与所有阶段状态一并复位
        self.hp = self.max_hp
        self.phase = 1
        self.casting = None
        self.interrupt_immune = False
        self.enrage_timer = 0.0
        self.enraged = False
        self.adds = []
        self.active_aoes = []
        self.projectiles = []
        self.damage_reduction = 0.0

    def create_safe_zone(self, aoe: AOE) -> tuple[float, float]:
        # 与伤害区域共用同一套坐标：取伤害区域边缘点，无额外偏移
        if aoe.shape == "circle":
            return (aoe.x + aoe.radius, aoe.y)
        if aoe.shape == "sector":
            return (aoe.x + aoe.radius * math.cos(aoe.angle),
                    aoe.y + aoe.radius * math.sin(aoe.angle))
        return (aoe.x, aoe.y)

    def transition_phase(self, new_phase: int):
        # 转阶段时取消所有进行中的施法和飞行道具
        self.phase = new_phase
        self.casting = None
        self.active_aoes = []
        self.projectiles = []

    def add_damage_reduction(self, r: float):
        # 乘法叠加：1-(1-a)(1-b)
        self.damage_reduction = 1.0 - (1.0 - self.damage_reduction) * (1.0 - r)

    def apply_damage_reduction(self, dmg: float) -> float:
        # 减伤后伤害下限为10%，不会叠成无敌
        factor = max(1.0 - self.damage_reduction, MIN_DAMAGE_FRACTION)
        return dmg * factor
