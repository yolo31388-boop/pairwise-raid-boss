"""团本BOSS机制系统"""
import math
from dataclasses import dataclass, field
from typing import Optional

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
    angle: float = 0  # 扇形朝向
    width: float = 0  # 矩形
    height: float = 0

@dataclass
class Add:
    aid: str
    hp: float
    threat: list = field(default_factory=list)  # (player_id, threat_value)

class Boss:
    MAX_THREAT_ENTRIES = 20          # 召唤物仇恨列表上限
    MIN_DAMAGE_MULTIPLIER = 0.1      # 减伤叠加后至少保留10%伤害

    def __init__(self):
        self.hp: float = 1000.0
        self.max_hp: float = 1000.0
        self.phase: int = 1
        self.phase_thresholds: list = [0.7, 0.4]  # 血量百分比
        self.phase_events: list[int] = [1]        # 依次经过的阶段记录
        self.casting: Optional[str] = None
        self.interrupt_immune: bool = False
        self.enrage_timer: float = 0.0
        self.enraged: bool = False
        self.adds: list[Add] = []
        self.active_aoes: list[AOE] = []
        self.damage_reduction: float = 0.0  # 减伤百分比

    def take_damage(self, dmg: float):
        self.hp -= dmg
        pct = self.hp / self.max_hp
        # 血量区间 + 事件触发：跳变时依次经过每个中间阶段
        while (self.phase - 1) < len(self.phase_thresholds) \
                and pct <= self.phase_thresholds[self.phase - 1]:
            self.transition_phase(self.phase + 1)

    def is_in_aoe(self, player: Player, aoe: AOE) -> bool:
        dx = player.x - aoe.x
        dy = player.y - aoe.y
        dist = math.sqrt(dx*dx + dy*dy)
        if aoe.shape == "circle":
            return dist <= aoe.radius
        if aoe.shape == "sector":
            if dist > aoe.radius:
                return False
            if dist == 0:
                return True
            # width 为扇形张角（弧度），angle 为朝向
            diff = (math.atan2(dy, dx) - aoe.angle + math.pi) % (2 * math.pi) - math.pi
            return abs(diff) <= aoe.width / 2
        if aoe.shape == "rect":
            # 以 (x, y) 为中心、按 angle 旋转的矩形
            cos_a = math.cos(-aoe.angle)
            sin_a = math.sin(-aoe.angle)
            lx = dx * cos_a - dy * sin_a
            ly = dx * sin_a + dy * cos_a
            return abs(lx) <= aoe.width / 2 and abs(ly) <= aoe.height / 2
        return False

    def spawn_add(self, add: Add):
        # 仇恨列表设上限，超出时淘汰（有距离信息淘汰最远的，否则淘汰仇恨最低的）
        if len(add.threat) > self.MAX_THREAT_ENTRIES:
            add.threat = self._trim_threat(add.threat)
        self.adds.append(add)

    def _trim_threat(self, threat: list) -> list:
        def eviction_key(entry):
            # 条目可为 (pid, value) 或 (pid, value, distance)
            if len(entry) >= 3:
                return -entry[2]   # 距离越远越先淘汰
            return entry[1]        # 无距离信息时仇恨越低越先淘汰
        kept = sorted(threat, key=eviction_key, reverse=True)
        return kept[:self.MAX_THREAT_ENTRIES]

    def can_interrupt(self) -> bool:
        return self.casting is not None and not self.interrupt_immune

    def reset_encounter(self):
        # 团灭后重置狂暴计时和所有阶段状态
        self.hp = self.max_hp
        self.phase = 1
        self.phase_events = [1]
        self.casting = None
        self.interrupt_immune = False
        self.enrage_timer = 0.0
        self.enraged = False
        self.adds = []
        self.active_aoes = []
        self.damage_reduction = 0.0

    def create_safe_zone(self, aoe: AOE) -> tuple[float, float]:
        # 与伤害区域同一套坐标：取伤害区域边缘点，无偏移
        if aoe.shape == "circle":
            return (aoe.x + aoe.radius, aoe.y)
        if aoe.shape == "sector":
            return (aoe.x + aoe.radius * math.cos(aoe.angle),
                    aoe.y + aoe.radius * math.sin(aoe.angle))
        if aoe.shape == "rect":
            cos_a = math.cos(aoe.angle)
            sin_a = math.sin(aoe.angle)
            return (aoe.x + (aoe.width / 2) * cos_a,
                    aoe.y + (aoe.width / 2) * sin_a)
        return (aoe.x, aoe.y)

    def transition_phase(self, new_phase: int):
        # 转阶段时取消所有进行中的施法和飞行道具
        self.phase = new_phase
        self.phase_events.append(new_phase)
        self.casting = None
        self.active_aoes = []

    def add_damage_reduction(self, pct: float):
        # 减伤乘法叠加：total = 1 - (1-a)(1-b)
        self.damage_reduction = 1.0 - (1.0 - self.damage_reduction) * (1.0 - pct)

    def apply_damage_reduction(self, dmg: float) -> float:
        # 乘法叠加并设下限：至少保留10%伤害，不会无敌
        multiplier = max(1.0 - self.damage_reduction, self.MIN_DAMAGE_MULTIPLIER)
        return dmg * multiplier
