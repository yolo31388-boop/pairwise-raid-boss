"""团本BOSS机制系统 - 红态测试"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from raid.boss import Boss, Player, AOE, Add

class TestPhaseTransition:
    def test_phase_skips_when_burst_damage(self):
        boss = Boss()
        boss.take_damage(700)  # 从100%打到30%
        assert boss.phase == 3  # bug1: 可能直接到3跳过2，应该依次经过
        # 正确行为：应该经过phase2再到phase3（或至少触发phase2事件）

    def test_phase_transition_triggers_all_phases(self):
        boss = Boss()
        phases_seen = []
        # 模拟逐步掉血
        boss.take_damage(200)  # 80%
        phases_seen.append(boss.phase)
        boss.take_damage(200)  # 60% -> phase2
        phases_seen.append(boss.phase)
        boss.take_damage(300)  # 30% -> phase3
        phases_seen.append(boss.phase)
        assert 2 in phases_seen and 3 in phases_seen

class TestAOEShape:
    def test_sector_aoe_not_circle(self):
        boss = Boss()
        aoe = AOE("sector", 0, 0, radius=5, angle=0, width=math.pi/2)
        p = Player("p1", 10, 0)  # 在扇形范围外（角度不对）
        assert boss.is_in_aoe(p, aoe) == False  # bug2: 按圆形判定返回True

    def test_rect_aoe(self):
        boss = Boss()
        aoe = AOE("rect", 0, 0, width=10, height=2)
        p = Player("p1", 5, 5)  # 在矩形外
        assert boss.is_in_aoe(p, aoe) == False  # bug2: 圆形radius=0返回False但逻辑错

class TestAddThreatCap:
    def test_add_threat_list_has_cap(self):
        boss = Boss()
        add = Add("add1", 100)
        for i in range(25):
            add.threat.append((f"p{i}", i))
        boss.spawn_add(add)
        assert len(boss.adds[0].threat) <= 20  # bug3: 25个无上限

class TestInterrupt:
    def test_interrupt_checks_immune(self):
        boss = Boss()
        boss.casting = "fireball"
        boss.interrupt_immune = True
        assert boss.can_interrupt() == False  # bug4: 返回True

class TestEnrageReset:
    def test_enrage_resets_on_wipe(self):
        boss = Boss()
        boss.enrage_timer = 300
        boss.enraged = True
        boss.reset_encounter()
        assert boss.enrage_timer == 0  # bug5: 还是300
        assert boss.enraged == False

class TestSafeZone:
    def test_safe_zone_matches_damage_area(self):
        boss = Boss()
        aoe = AOE("circle", 0, 0, radius=5)
        sx, sy = boss.create_safe_zone(aoe)
        # 安全区应该在伤害区域边缘附近，误差不超过0.5
        assert abs(sx - 5.0) < 0.5 or abs(sx) < 0.5  # bug6: 偏移2码

class TestPhaseTransitionCancelsCast:
    def test_transition_cancels_casting(self):
        boss = Boss()
        boss.casting = "ultimate"
        boss.transition_phase(2)
        assert boss.casting is None  # bug7: 还是ultimate

class TestDamageReductionCap:
    def test_damage_reduction_cannot_be_invincible(self):
        boss = Boss()
        boss.damage_reduction = 1.5  # 三个50%减伤加法叠加
        result = boss.apply_damage_reduction(100)
        assert result > 0  # bug8: 100*(1-1.5)=-50，应该有下限
        assert result >= 10  # 至少保留10%伤害
