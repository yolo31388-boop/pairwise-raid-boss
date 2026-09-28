"""团本BOSS机制系统 - 含8个bug"""
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
    def __init__(self):
        self.hp: float = 1000.0
        self.max_hp: float = 1000.0
        self.phase: int = 1
        self.phase_thresholds: list = [0.7, 0.4]  # 血量百分比
        self.casting: Optional[str] = None
        self.interrupt_immune: bool = False
        self.enrage_timer: float = 0.0
        self.enraged: bool = False
        self.adds: list[Add] = []
        self.active_aoes: list[AOE] = []
        self.damage_reduction: float = 0.0  # 减伤百分比

    def take_damage(self, dmg: float):
        # bug1: 阶段转换只检查当前百分比，跳变直接跳过
        self.hp -= dmg
        pct = self.hp / self.max_hp
        if self.phase == 1 and pct <= self.phase_thresholds[0]:
            self.phase = 2
        elif self.phase == 2 and pct <= self.phase_thresholds[1]:
            self.phase = 3
        # bug1续: 从100%一下打到30%应该经过phase2

    def is_in_aoe(self, player: Player, aoe: AOE) -> bool:
        # bug2: 所有AOE都按圆形判定
        dx = player.x - aoe.x
        dy = player.y - aoe.y
        dist = math.sqrt(dx*dx + dy*dy)
        return dist <= aoe.radius

    def spawn_add(self, add: Add):
        # bug3: 召唤物仇恨列表无上限
        self.adds.append(add)

    def can_interrupt(self) -> bool:
        # bug4: 不检查免疫打断阶段
        return self.casting is not None

    def reset_encounter(self):
        # bug5: 团灭后不重置狂暴计时
        self.hp = self.max_hp
        self.phase = 1
        self.casting = None
        self.adds = []
        self.active_aoes = []
        # enrage_timer没重置

    def create_safe_zone(self, aoe: AOE) -> tuple[float, float]:
        # bug6: 安全区标记与伤害区域偏移
        return (aoe.x + 2.0, aoe.y + 2.0)  # 偏移2码

    def transition_phase(self, new_phase: int):
        # bug7: 转阶段不取消已施放的技能
        self.phase = new_phase
        # casting没取消

    def apply_damage_reduction(self, dmg: float) -> float:
        # bug8: 减伤加法叠加可到无敌
        return dmg * (1.0 - self.damage_reduction)
