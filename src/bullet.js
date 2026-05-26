// ============================================================
// bullet.js - 子弹/投射物系统（多种弹道支持）
// ============================================================
const BulletSystem = {
    bullets: [],
    pool: [],

    create(x, y, angle, damage, speed, pierce, isPlayer = true, weaponId = 'pistol', extra = {}) {
        let b = this.pool.pop();
        if (!b) {
            b = { x: 0, y: 0, vx: 0, vy: 0, damage: 0, pierce: 0, life: 0, isPlayer: true, hits: [], weaponId: '' };
        }
        b.x = x;
        b.y = y;
        b.vx = Math.cos(angle) * speed;
        b.vy = Math.sin(angle) * speed;
        b.damage = damage;
        b.pierce = pierce;
        b.life = 3.0;
        b.isPlayer = isPlayer;
        b.hits = [];
        b.radius = isPlayer ? 4 : 3;
        b.weaponId = weaponId || 'pistol';
        // 特殊属性
        b.chainCount = extra.chainCount || 0;
        b.chainRange = extra.chainRange || 150;
        b.splashRadius = extra.splashRadius || 0;
        b.homingStrength = extra.homingStrength || 0;
        b.slowAmount = extra.slowAmount || 0;
        b.slowDuration = extra.slowDuration || 0;
        b.healOnHit = extra.healOnHit || 0;
        // 燃烧/毒属性
        b.burnDps = extra.burnDps || 0;
        b.burnMaxStacks = extra.burnMaxStacks || 0;
        // 冰爆
        b.iceExplosionRadius = extra.iceExplosionRadius || 0;
        // 跟踪用
        b.targetEnemy = null;
        this.bullets.push(b);
        return b;
    },

    update(dt) {
        for (let i = this.bullets.length - 1; i >= 0; i--) {
            const b = this.bullets[i];

            // 跟踪弹
            if (b.homingStrength > 0 && b.isPlayer) {
                this._updateHoming(b, dt);
            }

            b.x += b.vx * dt;
            b.y += b.vy * dt;
            b.life -= dt;

            // 范围爆炸（火箭筒）
            if (b.splashRadius > 0 && b.life <= 2.9) {
                // 只有飞出去后才检查爆炸
                this._checkSplash(b);
                this.pool.push(b);
                this.bullets.splice(i, 1);
                continue;
            }

            // 越界清除
            if (b.x < -100 || b.x > GameWorld.width + 100 ||
                b.y < -100 || b.y > GameWorld.height + 100) {
                this.pool.push(b);
                this.bullets.splice(i, 1);
                continue;
            }

            if (b.life <= 0) {
                this.pool.push(b);
                this.bullets.splice(i, 1);
            }
        }
    },

    /** 跟踪弹更新 */
    _updateHoming(b, dt) {
        // 寻找最近敌人
        if (!b.targetEnemy || !b.targetEnemy.alive) {
            let nearest = null, nearDist = Infinity;
            for (const e of EnemySystem.enemies) {
                if (!e.alive) continue;
                const dx = e.x - b.x, dy = e.y - b.y;
                const dist = dx * dx + dy * dy;
                if (dist < nearDist) {
                    nearDist = dist;
                    nearest = e;
                }
            }
            b.targetEnemy = nearest;
        }

        if (b.targetEnemy) {
            const dx = b.targetEnemy.x - b.x;
            const dy = b.targetEnemy.y - b.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist > 5) {
                const targetAngle = Math.atan2(dy, dx);
                const currentAngle = Math.atan2(b.vy, b.vx);
                let diff = targetAngle - currentAngle;
                if (diff > Math.PI) diff -= Math.PI * 2;
                if (diff < -Math.PI) diff += Math.PI * 2;
                const newAngle = currentAngle + diff * Math.min(1, b.homingStrength * dt);
                const speed = Math.sqrt(b.vx * b.vx + b.vy * b.vy);
                b.vx = Math.cos(newAngle) * speed;
                b.vy = Math.sin(newAngle) * speed;
            }
        }
    },

    /** 爆炸范围伤害 */
    _checkSplash(b) {
        const enemies = EnemySystem.enemies;
        const radius = b.splashRadius;
        let hitCount = 0;
        for (const e of enemies) {
            if (!e.alive) continue;
            const dx = e.x - b.x, dy = e.y - b.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < radius) {
                const atEdge = dist > radius * 0.3; // 边缘伤害衰减
                const dmg = atEdge ? Math.floor(b.damage * 0.5) : b.damage;
                EnemySystem.takeDamage(e, dmg);
                // 爆炸击退
                e.knockbackX += dx / (dist || 1) * 400;
                e.knockbackY += dy / (dist || 1) * 400;
                hitCount++;
            }
        }
        if (hitCount > 0) {
            // 爆炸特效
            ParticleSystem.explosion(b.x, b.y, '#ff6600', 20);
        }
    },

    /** 连锁电击 - 由碰撞检测调用 */
    chainLightning(b, hitEnemy) {
        if (b.chainCount <= 0) return;
        const enemies = EnemySystem.enemies.filter(e => e.alive && e !== hitEnemy && !b.hits.includes(e));
        let current = hitEnemy;
        let remaining = b.chainCount;
        while (remaining > 0 && enemies.length > 0) {
            // 找最近的下一个目标
            let nearest = null, nearDist = Infinity;
            for (const e of enemies) {
                if (b.hits.includes(e)) continue;
                const dx = e.x - current.x, dy = e.y - current.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < b.chainRange && dist < nearDist) {
                    nearDist = dist;
                    nearest = e;
                }
            }
            if (!nearest) break;
            // 连锁伤害（递减）
            const chainDmg = Math.floor(b.damage * (1 - (b.chainCount - remaining) * 0.2));
            EnemySystem.takeDamage(nearest, Math.max(1, chainDmg));
            b.hits.push(nearest);
            // 连锁闪电特效
            ParticleSystem.emit(nearest.x, nearest.y, 3, {
                speed: 40,
                color: '#00ffff',
                life: 0.15,
                size: 4,
                type: 'spark'
            });
            current = nearest;
            remaining--;
        }
    },

    clear() {
        while (this.bullets.length) {
            this.pool.push(this.bullets.pop());
        }
    }
};
