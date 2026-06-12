// ============================================================
// src/engine/turret.js — 炮塔系统 (Brotato 工程师·扳手机制)
// 每把 Tool 武器（扳手）生成一个炮塔，等级=武器等级
// 4 级炮塔各有不同行为
// ============================================================

const TurretSystem = {
    turrets: [],
    bullets: [],

    /** 每波开局: 每把 Tool 武器生成一个炮塔，等级=武器等级 */
    spawnTurrets(player) {
        this.clear();
        if (!player) return;

        const weapons = player.weapons || [];
        const params = player.weaponParams || {};

        // 每把 Tool 类武器 → 1 个炮塔，等级 = 武器等级
        for (const w of weapons) {
            const wp = params[w.id];
            if (wp && wp.class === 'Tool') {
                const level = Math.min(Math.max(w.level || 1, 1), 4);
                this._addTurret(player, level);
            }
        }

        // synergy turretCount 加成炮塔（等级 1）
        const synergyCount = player.turretCount || 0;
        for (let i = 0; i < synergyCount; i++) {
            this._addTurret(player, 1);
        }
    },

    /** 创建单个炮塔并加入列表 */
    _addTurret(player, level) {
        // 从 sceneItems 表读取尺寸，无代码缩放
        let width = 128; // 默认 128px（匹配 PNG 原生尺寸）
        if (typeof DataLoader !== 'undefined') {
            const items = DataLoader.get('sceneItems');
            const item = items.find(it => it.id === `turret${level}`);
            if (item && item.width > 0) width = item.width;
        }
        const radius = Math.round(width / 2);

        const angle = Math.random() * Math.PI * 2;
        const dist = 70 + Math.random() * 30;

        // 等级参数
        const LEVEL_CFG = {
            1: { range: 280, fireRate: 1.5, speed: 600, radius: 12, pierce: 0, spread: 0, count: 1 },   // 炮击
            2: { range: 160, fireRate: 0.25, speed: 700, radius: 8, pierce: 1, spread: 0.45, count: 3 },// 喷火
            3: { range: 180, fireRate: 0.3, speed: 700, radius: 8, pierce: 1, spread: 0.45, count: 3 }, // 冷冻
            4: { range: 350, fireRate: 0.1, speed: 0, radius: 0, pierce: 999, spread: 0, count: 1 },     // 激光
        };
        const cfg = LEVEL_CFG[level] || LEVEL_CFG[1];

        this.turrets.push({
            x: player.x + Math.cos(angle) * dist,
            y: player.y + Math.sin(angle) * dist,
            level: level,
            range: cfg.range,
            fireRate: cfg.fireRate,
            fireTimer: Math.random() * cfg.fireRate, // 错峰
            speed: cfg.speed,
            bulletRadius: cfg.radius,
            pierce: cfg.pierce,
            spread: cfg.spread,
            bulletCount: cfg.count,
            baseDamage: 10,
            alive: true,
            radius: radius,
            angle: angle,
            targetAngle: angle,
            attackPulse: 0,
            // 激光持续计时
            beamTimer: 0,
            beamTarget: null,
        });
    },

    /**
     * 每帧: 索敌 → 射击（按等级分支）→ 子弹碰撞
     */
    update(dt, enemies, player) {
        if (!player || !enemies) return;

        // 基础伤害公式
        const eng = Math.max(0, player.engineering || 0);
        const dmgMult = Math.max(0.1, player.turretDamage || 1);

        // ---- 炮塔更新 ----
        for (const t of this.turrets) {
            if (!t.alive) continue;

            // 索敌
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
                t.targetAngle = Math.atan2(nearest.y - t.y, nearest.x - t.x);
                t.angle = t.targetAngle; // 不旋转绘制,仅用于子弹方向
            }

            // 攻击脉冲衰减
            if (t.attackPulse > 0) t.attackPulse -= dt;

            // ====== 按等级分支 ======
            if (t.level === 4) {
                // L4 激光：持续光束，无子弹
                this._updateLaser(t, dt, nearest, enemies, eng, dmgMult);
            } else {
                t.fireTimer -= dt;
                if (nearest && t.fireTimer <= 0) {
                    t.fireTimer = t.fireRate;
                    const damage = Math.max(1, Math.round((t.baseDamage + eng * 0.8) * dmgMult));

                    if (t.level === 1) {
                        // L1 炮击：单发炮弹 + AoE
                        this._fireCannon(t, nearest, damage);
                    } else {
                        // L2/L3 喷射：多发穿透弹
                        this._fireSpray(t, nearest, damage);
                    }
                }
            }
        }

        // ---- 子弹更新 + 碰撞 ----
        this._updateBullets(dt, enemies);
    },

    /** L1 炮击：发射一发大炮弹，命中时 AoE 爆炸 */
    _fireCannon(t, target, damage) {
        t.attackPulse = 0.3;
        const angle = t.angle;
        const b = {
            x: t.x + Math.cos(angle) * t.radius,
            y: t.y + Math.sin(angle) * t.radius,
            vx: Math.cos(angle) * t.speed,
            vy: Math.sin(angle) * t.speed,
            damage: damage,
            radius: t.bulletRadius || 6,
            life: t.range / t.speed + 0.3,
            alive: true,
            level: 1,
            pierceRemaining: 0,
            hitTargets: [],
        };
        this.bullets.push(b);

        // 开火特效
        if (typeof ParticleSystem !== 'undefined') {
            ParticleSystem.emit(t.x + Math.cos(angle) * t.radius,
                t.y + Math.sin(angle) * t.radius, 4, {
                    speed: 120, color: '#ff6622', life: 0.2, size: 6, type: 'glow'
                });
        }
    },

    /** L2/L3 喷射：多发穿透弹 */
    _fireSpray(t, target, damage) {
        t.attackPulse = 0.3;
        const angle = t.angle;
        const count = t.bulletCount || 3;
        const spread = t.spread || 0.45;
        const startAngle = angle - spread * (count - 1) / 2;
        const pierce = t.pierce || 1;

        for (let i = 0; i < count; i++) {
            const a = startAngle + spread * i;
            const b = {
                x: t.x + Math.cos(a) * t.radius,
                y: t.y + Math.sin(a) * t.radius,
                vx: Math.cos(a) * t.speed,
                vy: Math.sin(a) * t.speed,
                damage: damage,
                radius: t.bulletRadius || 3,
                life: t.range / t.speed + 0.2,
                alive: true,
                level: t.level,
                pierceRemaining: pierce,
                hitTargets: [],
            };
            this.bullets.push(b);
        }

        // 开火特效
        const color = t.level === 3 ? '#44ccff' : '#ff6600';
        if (typeof ParticleSystem !== 'undefined') {
            for (let i = 0; i < count; i++) {
                const a = startAngle + spread * i;
                ParticleSystem.emit(t.x + Math.cos(a) * t.radius,
                    t.y + Math.sin(a) * t.radius, 2, {
                        speed: 60, color: color, life: 0.12, size: 3, type: 'spark'
                    });
            }
        }
    },

    /** L4 激光：持续光束，无子弹，每 tick 判定命中 */
    _updateLaser(t, dt, nearest, enemies, eng, dmgMult) {
        t.beamTimer += dt;
        if (t.beamTimer >= t.fireRate) {
            t.beamTimer = 0;
            t.beamTarget = nearest;
            if (nearest) {
                const damage = Math.max(1, Math.round((t.baseDamage * 0.4 + eng * 0.3) * dmgMult));
                // 激光穿透：沿途所有敌人
                const angle = t.angle;
                const beamEndX = t.x + Math.cos(angle) * t.range;
                const beamEndY = t.y + Math.sin(angle) * t.range;

                for (const e of enemies) {
                    if (!e.alive) continue;
                    // 点到线段距离检测
                    const dx = e.x - t.x;
                    const dy = e.y - t.y;
                    const tParam = Math.max(0, Math.min(1, (dx * Math.cos(angle) + dy * Math.sin(angle)) / t.range));
                    const projX = t.x + Math.cos(angle) * t.range * tParam;
                    const projY = t.y + Math.sin(angle) * t.range * tParam;
                    const distSq = (e.x - projX) * (e.x - projX) + (e.y - projY) * (e.y - projY);
                    if (distSq < (e.radius + 8) * (e.radius + 8)) {
                        e.hp -= damage;
                        if (typeof CombatLogSystem !== 'undefined') {
                            CombatLogSystem.addDamage(e.x, e.y, damage);
                        }
                        if (e.hp <= 0 && e.alive) {
                            e.alive = false;
                            if (typeof GameEngine !== 'undefined') {
                                GameEngine._handleEnemyKill(e, damage);
                            }
                        }
                    }
                }

                // 激光命中特效
                if (typeof ParticleSystem !== 'undefined') {
                    ParticleSystem.emit(nearest.x, nearest.y, 3, {
                        speed: 100, color: '#cc44ff', life: 0.1, size: 4, type: 'spark'
                    });
                }
            }
        }
    },

    /** 子弹更新 + 碰撞检测 */
    _updateBullets(dt, enemies) {
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            const b = this.bullets[i];
            b.x += b.vx * dt;
            b.y += b.vy * dt;
            b.life -= dt;

            if (b.life <= 0) {
                this.bullets.splice(i, 1);
                continue;
            }

            let used = false;
            for (const e of enemies) {
                if (!e.alive) continue;
                // 跳过已命中的目标（穿透弹不重复损伤同一敌人）
                if (b.hitTargets && b.hitTargets.includes(e)) continue;

                const dx = b.x - e.x;
                const dy = b.y - e.y;
                if (dx * dx + dy * dy < (b.radius + e.radius) * (b.radius + e.radius)) {
                    // 伤害
                    e.hp -= b.damage;
                    if (typeof CombatLogSystem !== 'undefined') {
                        CombatLogSystem.addDamage(e.x, e.y, b.damage);
                    }

                    // ====== 等级特殊效果 ======
                    if (b.level === 1) {
                        // L1 炮击：AoE 爆炸
                        this._applyExplosion(b.x, b.y, 70, b.damage * 0.5, enemies);
                        if (typeof ParticleSystem !== 'undefined') {
                            ParticleSystem.emit(b.x, b.y, 8, {
                                speed: 150, color: '#ff4422', life: 0.25, size: 8, type: 'glow'
                            });
                        }
                    } else if (b.level === 2) {
                        // L2 喷火：燃烧
                        this._applyBurn(e, 5, 2.0);
                        if (typeof ParticleSystem !== 'undefined') {
                            ParticleSystem.emit(b.x, b.y, 3, {
                                speed: 40, color: '#ff6600', life: 0.2, size: 4, type: 'spark'
                            });
                        }
                    } else if (b.level === 3) {
                        // L3 冷冻：减速
                        this._applySlow(e, 0.5, 1.5);
                        if (typeof ParticleSystem !== 'undefined') {
                            ParticleSystem.emit(b.x, b.y, 3, {
                                speed: 40, color: '#44ccff', life: 0.2, size: 4, type: 'spark'
                            });
                        }
                    } else {
                        // 通用命中特效
                        if (typeof ParticleSystem !== 'undefined') {
                            ParticleSystem.emit(b.x, b.y, 3, {
                                speed: 50, color: '#ffaa44', life: 0.15, size: 3, type: 'spark'
                            });
                        }
                    }

                    if (e.hp <= 0 && e.alive) {
                        e.alive = false;
                        if (typeof GameEngine !== 'undefined') {
                            GameEngine._handleEnemyKill(e, b.damage);
                        }
                    }

                    // 穿透处理
                    if (b.pierceRemaining !== undefined && b.pierceRemaining > 0) {
                        if (!b.hitTargets) b.hitTargets = [];
                        b.hitTargets.push(e);
                        b.pierceRemaining--;
                        if (b.pierceRemaining <= 0) {
                            used = true;
                            break;
                        }
                    } else {
                        used = true;
                        break;
                    }
                }
            }

            if (used) {
                this.bullets.splice(i, 1);
            }
        }
    },

    _applyExplosion(x, y, radius, damage, enemies) {
        for (const e of enemies) {
            if (!e.alive) continue;
            const dx = e.x - x;
            const dy = e.y - y;
            if (dx * dx + dy * dy < radius * radius) {
                e.hp -= damage;
                if (typeof CombatLogSystem !== 'undefined') {
                    CombatLogSystem.addDamage(e.x, e.y, Math.round(damage));
                }
                if (e.hp <= 0 && e.alive) {
                    e.alive = false;
                    if (typeof GameEngine !== 'undefined') {
                        GameEngine._handleEnemyKill(e, damage);
                    }
                }
            }
        }
    },

    _applyBurn(enemy, dps, duration) {
        if (!enemy.burnStacks) enemy.burnStacks = [];
        enemy.burnStacks.push({ dps, remaining: duration });
    },

    _applySlow(enemy, amount, duration) {
        enemy.slowTimer = duration;
        enemy.slowFactor = 1 - amount;
    },

    clear() {
        this.turrets = [];
        this.bullets = [];
    },

    reset() {
        this.clear();
    },
};

if (typeof module !== 'undefined') {
    module.exports = { TurretSystem };
}
