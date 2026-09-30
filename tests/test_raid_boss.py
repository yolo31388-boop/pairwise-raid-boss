"""团本BOSS阶段转换 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from raid.boss_controller import RaidBossController, BossState

class TestPhaseNoRollback:
    def test_cannot_go_from_phase3_to_phase1(self):
        rbc = RaidBossController()
        rbc.boss.phase = 3
        result = rbc.transition_phase(1)
        assert result == False
        assert rbc.boss.phase == 3

class TestSkillChainReset:
    def test_skill_chain_resets_on_phase_transition(self):
        rbc = RaidBossController()
        rbc.boss.phase = 3
        rbc.boss.skill_chain = ["enrage"]
        rbc.transition_phase(2)
        assert "enrage" not in rbc.boss.skill_chain

class TestArenaCleanup:
    def test_old_arena_effects_cleared_on_phase_change(self):
        rbc = RaidBossController()
        rbc.boss.phase = 3
        rbc.boss.arena_effects = ["void_zone"]
        rbc.transition_phase(2)
        rbc.update_arena_effect(2)
        assert "void_zone" not in rbc.boss.arena_effects

class TestDebuffExpiry:
    def test_debuffs_expire_on_phase_change(self):
        rbc = RaidBossController()
        rbc.apply_raid_debuff("phase1_debuff")
        rbc.transition_phase(2)
        assert "phase1_debuff" not in rbc.boss.raid_debuffs

class TestBerserkLock:
    def test_berserked_boss_does_not_change_phase(self):
        rbc = RaidBossController()
        rbc.check_berserk(700)
        result = rbc.transition_phase(2)
        assert result == False
