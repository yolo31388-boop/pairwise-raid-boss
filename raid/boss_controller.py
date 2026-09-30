"""团本BOSS阶段转换 - 含5个bug"""
from dataclasses import dataclass, field

@dataclass
class BossState:
    bid: str
    phase: int = 1
    hp: int = 1000
    max_hp: int = 1000
    skill_chain: list = field(default_factory=list)
    arena_effects: list = field(default_factory=list)
    raid_debuffs: list = field(default_factory=list)
    berserk_timer: int = 0
    berserked: bool = False

class RaidBossController:
    def __init__(self):
        self.boss = BossState("boss1")

    def transition_phase(self, new_phase: int) -> bool:
        # bug1: 阶段可以回退
        self.boss.phase = new_phase
        return True

    def trigger_skill_chain(self, phase: int) -> list:
        # bug2: 阶段回退后技能链不重置
        skills = {1: ["smash"], 2: ["smash", "fireball"], 3: ["smash", "fireball", "enrage"]}
        return skills.get(phase, [])

    def update_arena_effect(self, phase: int) -> None:
        # bug3: 阶段转换不清理旧效果
        effects = {1: ["fire_zone"], 2: ["fire_zone", "ice_zone"], 3: ["fire_zone", "ice_zone", "void_zone"]}
        self.boss.arena_effects = effects.get(phase, [])

    def apply_raid_debuff(self, debuff: str) -> None:
        # bug4: 减益不随阶段过期
        self.boss.raid_debuffs.append(debuff)

    def check_berserk(self, elapsed: int) -> bool:
        # bug5: 狂暴后还在转换阶段
        if elapsed >= 600:
            self.boss.berserked = True
        return self.boss.berserked
