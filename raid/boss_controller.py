"""团本BOSS阶段转换"""
from dataclasses import dataclass, field

PHASE_SKILLS = {
    1: ["smash"],
    2: ["smash", "fireball"],
    3: ["smash", "fireball", "enrage"],
}

PHASE_ARENA_EFFECTS = {
    1: ["fire_zone"],
    2: ["fire_zone", "ice_zone"],
    3: ["fire_zone", "ice_zone", "void_zone"],
}

BERSERK_ELAPSED = 600

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
        # 狂暴后阶段锁定，不再进行任何转换
        if self.boss.berserked:
            return False
        # 同阶段调用视为无操作
        if new_phase == self.boss.phase:
            return False
        # 技能链始终对齐目标阶段，保证低阶段绝不会残留高阶段技能
        self.boss.skill_chain = list(PHASE_SKILLS.get(new_phase, []))
        # 阶段只能前进，不能回退
        if new_phase < self.boss.phase:
            return False
        self.boss.phase = new_phase
        # 转换时清理上一阶段的场地效果与团队减益
        self.boss.arena_effects = []
        self.boss.raid_debuffs = []
        return True

    def trigger_skill_chain(self, phase: int) -> list:
        skills = list(PHASE_SKILLS.get(phase, []))
        self.boss.skill_chain = skills
        return list(skills)

    def update_arena_effect(self, phase: int) -> None:
        self.boss.arena_effects = list(PHASE_ARENA_EFFECTS.get(phase, []))

    def apply_raid_debuff(self, debuff: str) -> None:
        self.boss.raid_debuffs.append(debuff)

    def check_berserk(self, elapsed: int) -> bool:
        if not self.boss.berserked and elapsed >= BERSERK_ELAPSED:
            self.boss.berserked = True
            self.boss.berserk_timer = elapsed
        return self.boss.berserked
