// ============================================================
// enemy.js - 敌人系统
// ============================================================
const EnemySystem = {
    enemies: [],

    // 敌人类型定义
    types: {
        basic: {
            name: '无人机兵',
            hp: 30,
            speed: 80,
            damage: 8,
            radius: 14,
            color: '#ff4444',
            glowColor: '#ff0044',
            xpValue: 5,
            materialValue: 2,
            attackCooldown: 1.5,
            behavior: 'chase'  // 直接追玩家
        },
        fast: {
            name: '疾行者',
            hp: 20,
            speed: 160,
            damage: 6,
            radius: 10,
            color: '#ff8800',
            glowColor: '#ff6600',
            xpValue: 6,
            materialValue: 2,
            attackCooldown: 1.2,
            behavior: 'chase'
        },
        tank: {
            name: '重装机兵',
            hp: 120,
            speed: 45,
            damage: 15,
            radius: 22,
            color: '#8844ff',
            glowColor: '#6622ff',
            xpValue: 12,
            materialValue: 5,
            attackCooldown: 2.0,
            behavior: 'chase'
        },
        ranged: {
            name: '狙击手',
            hp: 25,
            speed: 55,
            damage: 12,
            radius: 12,
            color: '#ff00aa',
            glowColor: '#ff0088',
            xpValue: 8,
            materialValue: 3,
            attackCooldown: 2.0,
            behavior: 'ranged',
            preferredDist: 250,
            bulletSpeed: 350
        },
        elite: {
            name: '精英猎手',
            hp: 250,
            speed: 70,
            damage: 20,
            radius: 24,
            color: '#ffcc00',
            glowColor: '#ffaa00',
            xpValue: 30,
            materialValue: 15,
            attackCooldown: 1.0,
            behavior: 'chase',
            isElite: true
        },
        boss: {
            name: 'BOSS·毁灭者',
            hp: 800,
            speed: 55,
            damage: 30,
            radius: 36,
            color: '#ff0044',
            glowColor: '#ff0000',
            xpValue: 80,
            materialValue: 40,
            attackCooldown: 0.8,
            behavior: 'chase',
            isBoss: true
        }
    },

    create(type, x, y, waveScale = 1) {
        const t = this.types[type];
        if (!t) return null;
        const e = {
            x, y,
            type: type,
            name: t.name,
            hp: t.hp * waveScale,
            maxHp: t.hp * waveScale,
            speed: t.speed * (1 + (waveScale - 1) * 0.3),
            damage: t.damage * waveScale,
            radius: t.radius,
            color: t.color,
            glowColor: t.glowColor,
            xpValue: Math.floor(t.xpValue * waveScale),
            materialValue: Math.floor(t.materialValue * waveScale),
            attackCooldown: t.attackCooldown,
            behavior: t.behavior,
            preferredDist: t.preferredDist || 200,
            bulletSpeed: t.bulletSpeed || 300,
            isElite: t.isElite || false,
            isBoss: t.isBoss || false,
            alive: true,
            attackTimer: Math.random() * t.attackCooldown,
            flashTimer: 0,
            knockbackX: 0,
            knockbackY: 0,
            // 行走方向跟踪（用于方向帧动画）
            prevX: x,
            prevY: y,
            moveAngle: 0,
            isMovingEnemy: false,
            // 减速
            slowTimer: 0,
            slowFactor: 0.5,
            speedMult: 1.0
        };
        this.enemies.push(e);
        return e;
    },

    update(dt, player) {
        for (let i = this.enemies.length - 1; i >= 0; i--) {
            const e = this.enemies[i];
            if (!e.alive) {
                this.enemies.splice(i, 1);
                continue;
            }

            // 闪避效果计时
            if (e.flashTimer > 0) e.flashTimer -= dt;

            // 击退衰减
            e.knockbackX *= 0.9;
            e.knockbackY *= 0.9;

            // 减速效果
            if (e.slowTimer > 0) {
                e.slowTimer -= dt;
                e.speedMult = e.slowFactor || 0.5;
            } else {
                e.speedMult = 1.0;
            }

            // ====== 燃烧DOT处理 ======
            if (e.burnStacks && e.burnStacks.length > 0) {
                for (let si = e.burnStacks.length - 1; si >= 0; si--) {
                    const stack = e.burnStacks[si];
                    stack.remaining -= dt;
                    if (stack.remaining <= 0) {
                        e.burnStacks.splice(si, 1);
                        continue;
                    }
                    // 每秒伤害
                    const dotDmg = stack.dps * dt;
                    e.hp -= dotDmg;
                    if (e.hp <= 0) break;
                }                    // 燃烧DOT日志（每秒记录一次）
                    e._burnLogTimer = (e._burnLogTimer || 0) + dt;
                    if (e._burnLogTimer >= 1.0) {
                        e._burnLogTimer = 0;
                        const totalBurnDmg = e.burnStacks.reduce((sum, s) => sum + s.dps, 0);
                        if (totalBurnDmg > 0) {
                            CombatLogSystem.addEventText(e.x, e.y - 15, `🔥${Math.round(totalBurnDmg)}`, '#ff8800', 12);
                            CombatLogSystem.logBurnDamage(totalBurnDmg);
                        }
                    }
                    // 燃烧粒子特效
                    if (e.burnStacks.length > 0 && Math.random() < 0.3) {
                    ParticleSystem.emit(e.x + (Math.random()-0.5)*10, e.y + (Math.random()-0.5)*10, 1, {
                        speed: 20, color: '#ff4400', life: 0.3, size: 3, type: 'glow'
                    });
                }
                // 检查燃烧DOT击杀
                if (e.hp <= 0 && e.alive) {
                    e.hp = 0;
                    e.alive = false;
                    // 燃烧传播（如果有扩散器）
                    if (PlayerSystem.player && PlayerSystem.player._burnSpreadLevel) {
                        PlayerSystem._spreadBurn(e);
                    }
                    // 冰爆触发（如果敌人有冰缓效果且死亡）
                    if (e.slowTimer > 0 && PlayerSystem.player) {
                        PlayerSystem._triggerIceExplosion(e);
                    }
                    continue;
                }
            }

            // AI行为
            const dx = player.x - e.x;
            const dy = player.y - e.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (e.behavior === 'chase') {
                // 追逐玩家
                if (dist > 5) {
                    const speed = e.speed * e.speedMult * dt;
                    e.x += (dx / dist) * speed + e.knockbackX * dt;
                    e.y += (dy / dist) * speed + e.knockbackY * dt;
                }
                // 碰撞伤害
                e.attackTimer -= dt;
                if (e.attackTimer <= 0 && dist < e.radius + player.radius + 5) {
                    PlayerSystem.takeDamage(e.damage);
                    e.attackTimer = e.attackCooldown;
                    // 击退玩家
                    player.knockbackX = -dx / dist * 200;
                    player.knockbackY = -dy / dist * 200;
                }
            } else if (e.behavior === 'ranged') {
                // 保持距离射击
                if (dist < e.preferredDist - 30) {
                    const speed = e.speed * e.speedMult * dt;
                    e.x -= (dx / dist) * speed;
                    e.y -= (dy / dist) * speed;
                } else if (dist > e.preferredDist + 30) {
                    const speed = e.speed * e.speedMult * dt;
                    e.x += (dx / dist) * speed;
                    e.y += (dy / dist) * speed;
                }
                e.x += e.knockbackX * dt;
                e.y += e.knockbackY * dt;

                // 远程攻击
                e.attackTimer -= dt;
                if (e.attackTimer <= 0 && dist < 500) {
                    const angle = Math.atan2(dy, dx);
                    BulletSystem.create(
                        e.x, e.y, angle,
                        e.damage, e.bulletSpeed, 0, false
                    );
                    e.attackTimer = e.attackCooldown;
                    ParticleSystem.emit(e.x, e.y, 3, {
                        speed: 30,
                        color: e.color,
                        life: 0.2,
                        size: 3,
                        type: 'spark'
                    });
                }
            }

            // 边界
            e.x = Math.max(10, Math.min(GameWorld.width - 10, e.x));
            e.y = Math.max(10, Math.min(GameWorld.height - 10, e.y));

            // 更新移动方向（用于方向帧动画）
            const moveDx = e.x - e.prevX;
            const moveDy = e.y - e.prevY;
            const moveDist = Math.sqrt(moveDx * moveDx + moveDy * moveDy);
            e.isMovingEnemy = moveDist > 0.5;
            if (e.isMovingEnemy) {
                e.moveAngle = Math.atan2(moveDy, moveDx);
            }
            e.prevX = e.x;
            e.prevY = e.y;
        }
    },

    takeDamage(enemy, damage) {
        if (!enemy.alive) return 0;
        enemy.hp -= damage;
        enemy.flashTimer = 0.1;

        // 击退
        const p = PlayerSystem.player;
        if (p) {
            const dx = enemy.x - p.x;
            const dy = enemy.y - p.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            enemy.knockbackX += dx / dist * 300;
            enemy.knockbackY += dy / dist * 300;
        }

        // 受击粒子
        ParticleSystem.emit(enemy.x, enemy.y, 4, {
            speed: 60,
            color: enemy.color,
            life: 0.2,
            size: 3,
            type: 'spark'
        });

        if (enemy.hp <= 0) {
            enemy.alive = false;
            return -1; // 死亡
        }
        return 0; // 受伤
    },

    clear() {
        this.enemies = [];
    }
};
