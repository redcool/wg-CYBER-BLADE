// ============================================================
// src/engine/turret.js — 炮塔系统 (Brotato 工程师·扳手机制)
// 依赖: enemy.js (EnemySystem), bullet.js (BulletSystem 复用), renderer.js
// ============================================================

/**
 * TurretSystem — 自动炮塔
 *
 * 每波开局: 扳手武器(每个1个) + synergy turretCount → 生成炮塔
 * 炮塔自动索敌射击, 范围300, 伤害 = 10 + (80% × engineering) × turretDamage
 * 炮塔子弹独立于 BulletSystem 管理
 *
 * API:
 *   spawnTurrets(player, currentLevel)   每波生成炮塔
 *   update(dt, enemies, player)          每帧更新 (索敌+射击+子弹)
 *   clear()                              清除所有炮塔
 *   reset()                              重置
 */

const TurretSystem = {
    turrets: [],
    bullets: [],

    /**
     * 每波开局: 统计角色 Tool 武器数 + synergy turretCount → 生成炮塔
     */
    spawnTurrets(player) {
        // 清空旧炮塔
        this.clear();

        if (!player) return;
        const weapons = player.weapons || [];

        // 每个 Tool 类武器 = 1 炮塔
        let toolCount = 0;
        for (const w of weapons) {
            if (w && w.class === 'Tool') toolCount++;
        }

        // synergy turretCount 加成
        const synergyCount = player.turretCount || 0;
        const total = Math.max(0, toolCount + synergyCount);
        if (total === 0) return;

        for (let i = 0; i < total; i++) {
            // 绕玩家分散生成
            const angle = (i / total) * Math.PI * 2 + (Math.random() - 0.5) * 0.5;
            const dist = 70 + Math.random() * 30;

            this.turrets.push({
                x: player.x + Math.cos(angle) * dist,
                y: player.y + Math.sin(angle) * dist,
                range: 300,
                fireRate: 0.73,
                fireTimer: Math.random() * 0.73, // 错峰开火
                baseDamage: 10,
                alive: true,
                radius: 14,
                angle: angle,       // 当前朝向
                targetAngle: angle, // 目标朝向（平滑旋转）
                scale: 1,
            });
        }
    },

    /**
     * 每帧: 索敌 → 射击 → 子弹碰撞
     */
    update(dt, enemies, player) {
        if (!player || !enemies) return;

        // ---- 炮塔更新 ----
        for (const t of this.turrets) {
            if (!t.alive) continue;

            // 找最近敌人 (300 范围)
            let nearest = null;
            let nearDist = t.range;
            for (const e of enemies) {
                if (!e.alive) continue;
                const dx = e.x - t.x;
                const dy = e.y - t.y;
                const d = dx * dx + dy * dy;
                if (d < nearDist * nearDist) {
                    nearDist = Math.sqrt(d);
                    nearest = e;
                }
            }

            if (nearest) {
                // 平滑转向
                const targetAngle = Math.atan2(nearest.y - t.y, nearest.x - t.x);
                t.targetAngle = targetAngle;
                t.angle += (t.targetAngle - t.angle) * Math.min(1, dt * 8);
            }

            t.fireTimer -= dt;

            // 开火
            if (nearest && t.fireTimer <= 0) {
                t.fireTimer = t.fireRate;

                // 伤害计算: 10 + 80% × engineering
                const eng = Math.max(0, player.engineering || 0);
                const dmgMult = Math.max(0.1, player.turretDamage || 1);
                const damage = Math.max(1, Math.round((t.baseDamage + eng * 0.8) * dmgMult));

                // 子弹朝向目标（不提前量）
                const angle = t.angle;
                const speed = 400;

                this.bullets.push({
                    x: t.x + Math.cos(angle) * t.radius,
                    y: t.y + Math.sin(angle) * t.radius,
                    vx: Math.cos(angle) * speed,
                    vy: Math.sin(angle) * speed,
                    damage: damage,
                    radius: 5,
                    life: t.range / speed + 0.2, // 存活 ≈ 射程/速度
                    alive: true,
                });

                // 开火特效
                if (typeof ParticleSystem !== 'undefined') {
                    ParticleSystem.emit(t.x + Math.cos(angle) * t.radius,
                        t.y + Math.sin(angle) * t.radius, 3, {
                            speed: 80, color: '#ffaa44', life: 0.15, size: 4, type: 'glow'
                        });
                }
            }
        }

        // ---- 子弹更新 + 碰撞 ----
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            const b = this.bullets[i];
            b.x += b.vx * dt;
            b.y += b.vy * dt;
            b.life -= dt;

            if (b.life <= 0) {
                this.bullets.splice(i, 1);
                continue;
            }

            // 对敌人碰撞
            let used = false;
            for (const e of enemies) {
                if (!e.alive) continue;
                const dx = b.x - e.x;
                const dy = b.y - e.y;
                if (dx * dx + dy * dy < (b.radius + e.radius) * (b.radius + e.radius)) {
                    e.hp -= b.damage;
                    if (typeof CombatLogSystem !== 'undefined') {
                        CombatLogSystem.addDamage(e.x, e.y, b.damage);
                    }

                    // 命中特效
                    if (typeof ParticleSystem !== 'undefined') {
                        ParticleSystem.emit(b.x, b.y, 4, {
                            speed: 50, color: '#ffaa44', life: 0.15, size: 3, type: 'spark'
                        });
                    }

                    if (e.hp <= 0 && e.alive) {
                        e.alive = false;
                        if (typeof GameEngine !== 'undefined') {
                            GameEngine._handleEnemyKill(e, b.damage);
                        }
                    }

                    used = true;
                    break;
                }
            }

            if (used) {
                this.bullets.splice(i, 1);
            }
        }
    },

    /** 清空所有炮塔和子弹 */
    clear() {
        this.turrets = [];
        this.bullets = [];
    },

    /** 重置 */
    reset() {
        this.clear();
    },
};

if (typeof module !== 'undefined') {
    module.exports = { TurretSystem };
}
