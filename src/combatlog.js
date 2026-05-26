// ============================================================
// combatlog.js - 战斗日志系统（伤害数字 + 事件日志）
// ============================================================
const CombatLogSystem = {
    /** 浮动数字数组 { x, y, text, color, size, life, maxLife, vy } */
    floatingTexts: [],
    /** 事件日志数组 { text, icon, color, time } */
    logEntries: [],
    /** 日志最大保留条数 */
    maxLogEntries: 12,
    /** 是否显示日志面板 */
    showLogPanel: true,
    /** 日志显示时长（秒） */
    logDisplayDuration: 6,
    /** 日志面板是否需要刷新 */
    _dirty: false,
    /** 聚合半径（px）——同一位置短时间内的伤害合并为一个数字 */
    _mergeRadius: 35,
    /** 聚合窗口——目标剩余生命需大于此值才被视为「近期」 */
    _mergeMinLife: 0.3,

    // ====== 聚合辅助 ======

    /**
     * 在已有浮动文本中寻找可聚合的目标
     * @param {number} x - 新数字的 X
     * @param {number} y - 新数字的 Y
     * @param {string} mergeKey - 聚合分组标识（'dmg'/'crit'/'heal'/null=不分组）
     * @returns {{ entry: object, index: number } | null}
     */
    _findMergeTarget(x, y, mergeKey) {
        let best = null;
        let bestDist = this._mergeRadius;
        for (let i = 0; i < this.floatingTexts.length; i++) {
            const ft = this.floatingTexts[i];
            // 只有同组的才聚合
            if (ft._mergeKey !== mergeKey) continue;
            // 只有「近期」产生的才聚合（剩余生命够长）
            if (ft.life < this._mergeMinLife) continue;
            const dx = ft.x - x;
            const dy = ft.y - y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < bestDist) {
                bestDist = dist;
                best = { entry: ft, index: i };
            }
        }
        return best;
    },

    /**
     * 将伤害/数值叠加到目标上
     */
    _mergeInto(target, amount) {
        // 累加原始数值
        target._totalAmount = (target._totalAmount || 0) + amount;
        target._hitCount = (target._hitCount || 1) + 1;
        // 重置计时器（让合并后的数字多停留一会儿）
        target.life = Math.min(target.maxLife, target.life + 0.15);
        // 弹跳动画：合并时「嘭」地放大 35%
        target._bounceScale = 0.35;
        // 扩散光晕粒子特效
        if (typeof ParticleSystem !== 'undefined') {
            ParticleSystem.mergeGlow(target.x, target.y, target.color || '#ffffff');
        }
    },

    /**
     * 根据 _totalAmount / _hitCount 重新渲染文本
     */
    _renderMergeText(target) {
        const total = target._totalAmount;
        const count = target._hitCount;
        if (target._mergeKey === 'heal') {
            target.text = `+${Math.round(total)}`;
        } else if (target._mergeKey === 'crit') {
            target.text = `⚡${Math.round(total)}`;
        } else {
            target.text = `${Math.round(total)}`;
        }
        if (count > 1) {
            target.text += ` ×${count}`;
            // 多段命中稍微放大
            target.size = Math.min(target.size + 2, target._baseSize + 6);
        } else {
            target.size = target._baseSize;
        }
    },

    // ====== 初次命中入场特效（比合并微弱） ======

    /** 初次命中入场微闪 */
    _emitHitSpawn(x, y, color) {
        // 轻微的弹跳脉冲
        // 光晕会在下面的 push 后通过新条目的 _bounceScale 触发
        if (typeof ParticleSystem !== 'undefined') {
            ParticleSystem.emit(x, y, 3, {
                speed: 60,
                color: color,
                life: 0.25,
                size: 4,
                spread: Math.PI * 2,
                type: 'glow'
            });
        }
    },

    // ====== 浮动伤害数字 ======

    /** 添加普通伤害数字 */
    addDamage(x, y, amount, color = '#ffffff', size = 16) {
        // 尝试聚合
        const target = this._findMergeTarget(x, y, 'dmg');
        if (target) {
            this._mergeInto(target.entry, amount);
            this._renderMergeText(target.entry);
            // 轻微漂移，避免完全重叠后视觉效果太死板
            target.entry.vy = -60 - Math.random() * 30;
            target.entry.vx += (Math.random() - 0.5) * 5;
            return;
        }
        this.floatingTexts.push({
            x, y,
            text: String(Math.round(amount)),
            color: color,
            size: size,
            _baseSize: size,
            life: 1.0,
            maxLife: 1.0,
            vy: -60 - Math.random() * 30,
            vx: (Math.random() - 0.5) * 20,
            _mergeKey: 'dmg',
            _totalAmount: amount,
            _hitCount: 1,
            _bounceScale: 0.12,
        });
        this._emitHitSpawn(x, y, color);
    },

    /** 添加暴击数字（更大、黄色、⚡前缀） */
    addCritDamage(x, y, amount) {
        // 尝试聚合到同组暴击
        const target = this._findMergeTarget(x, y, 'crit');
        if (target) {
            this._mergeInto(target.entry, amount);
            this._renderMergeText(target.entry);
            target.entry.vy = -70 - Math.random() * 30;
            target.entry.vx += (Math.random() - 0.5) * 5;
            // 也更新「暴击!」子文本位置
            return;
        }
        this.floatingTexts.push({
            x, y,
            text: `⚡${Math.round(amount)}`,
            color: '#ffcc00',
            size: 22,
            _baseSize: 22,
            life: 1.2,
            maxLife: 1.2,
            vy: -70 - Math.random() * 30,
            vx: (Math.random() - 0.5) * 25,
            _mergeKey: 'crit',
            _totalAmount: amount,
            _hitCount: 1,
            _bounceScale: 0.12,
        });
        // 额外再弹一个小的「暴击!」（不参与聚合）
        this.floatingTexts.push({
            x, y: y - 8,
            text: '暴击!',
            color: '#ffaa00',
            size: 13,
            life: 0.8,
            maxLife: 0.8,
            vy: -40 - Math.random() * 20,
            vx: (Math.random() - 0.5) * 15,
        });
        this._emitHitSpawn(x, y, '#ffcc00');
    },

    /** 添加治疗数字 */
    addHeal(x, y, amount) {
        // 尝试聚合
        const target = this._findMergeTarget(x, y, 'heal');
        if (target) {
            this._mergeInto(target.entry, amount);
            this._renderMergeText(target.entry);
            target.entry.vy = -50 - Math.random() * 20;
            target.entry.vx += (Math.random() - 0.5) * 3;
            return;
        }
        this.floatingTexts.push({
            x, y: y - 5,
            text: `+${Math.round(amount)}`,
            color: '#00ff88',
            size: 16,
            _baseSize: 16,
            life: 1.0,
            maxLife: 1.0,
            vy: -50 - Math.random() * 20,
            vx: (Math.random() - 0.5) * 15,
            _mergeKey: 'heal',
            _totalAmount: amount,
            _hitCount: 1,
            _bounceScale: 0.12,
        });
        this._emitHitSpawn(x, y, '#00ff88');
    },

    /** 添加事件文本（非伤害，如 "吸血", "燃烧" 等） */
    addEventText(x, y, text, color = '#ffffff', size = 14) {
        this.floatingTexts.push({
            x, y: y - 10,
            text: text,
            color: color,
            size: size,
            life: 0.9,
            maxLife: 0.9,
            vy: -40 - Math.random() * 15,
            vx: (Math.random() - 0.5) * 10,
        });
    },

    // ====== 事件日志 ======

    /** 添加一条战斗事件日志 */
    addLog(icon, text, color = '#ffffff') {
        this.logEntries.unshift({
            icon: icon,
            text: text,
            color: color,
            time: this.logDisplayDuration,
        });
        if (this.logEntries.length > this.maxLogEntries) {
            this.logEntries.length = this.maxLogEntries;
        }
        this._dirty = true;
    },

    // ====== 通用快捷事件 ======

    /** 记录击杀 */
    logKill(enemyName) {
        this.addLog('💀', `击杀 ${enemyName}`, '#ff6666');
    },

    /** 记录暴击 */
    logCrit(damage) {
        this.addLog('⚡', `暴击! 造成 ${Math.round(damage)} 伤害`, '#ffcc00');
    },

    /** 记录金币掉落 */
    logDrop(amount) {
        this.addLog('🪙', `获得 ${amount} 金币`, '#ffcc00');
    },

    /** 记录宝箱掉落 */
    logChestDrop(enemyName, tier) {
        const tierName = tier === 2 ? '二级' : '一级';
        this.addLog('📦', `${enemyName} 掉落${tierName}宝箱`, '#ffcc00');
    },

    /** 记录宝箱拾取 */
    logChestPickup() {
        this.addLog('📦', '拾取宝箱', '#ffcc00');
    },

    /** 记录吸血 */
    logLifeSteal(amount) {
        this.addLog('🩸', `吸血 +${Math.round(amount)}`, '#ff6666');
    },

    /** 记录升级 */
    logLevelUp(level) {
        this.addLog('⬆️', `升级至 Lv.${level}`, '#00ff88');
    },

    /** 记录玩家受伤 */
    logDamageTaken(amount, enemyName) {
        this.addLog('💥', `${enemyName || '敌人'} 造成 ${Math.round(amount)} 伤害`, '#ff4444');
    },

    /** 记录燃烧伤害 */
    logBurnDamage(amount) {
        this.addLog('🔥', `燃烧造成 ${Math.round(amount)} 伤害`, '#ff8800');
    },

    /** 记录医药箱击破 */
    logCrateBroken() {
        this.addLog('❤️', '击破医药箱', '#00ff88');
    },

    // ====== 更新 ======

    /** 每帧更新 */
    update(dt) {
        // 浮动文本更新
        for (let i = this.floatingTexts.length - 1; i >= 0; i--) {
            const ft = this.floatingTexts[i];
            ft.y += ft.vy * dt;
            ft.x += ft.vx * dt;
            ft.life -= dt;
            ft.vy *= 0.97;

            // 弹跳弹簧衰减：0.3s 内衰减到 5%（95% 衰减）
            if (ft._bounceScale > 0.001) {
                ft._bounceScale *= Math.pow(0.05, dt / 0.3);
            } else {
                ft._bounceScale = 0;
            }

            if (ft.life <= 0) {
                this.floatingTexts.splice(i, 1);
            }
        }

        // 日志过期
        for (let i = this.logEntries.length - 1; i >= 0; i--) {
            this.logEntries[i].time -= dt;
            if (this.logEntries[i].time <= 0) {
                this.logEntries.splice(i, 1);
                this._dirty = true;
            }
        }
    },

    /** 更新日志面板 DOM（仅 dirty 时更新，避免每帧 innerHTML） */
    renderLogPanel() {
        if (!this._dirty) return;
        this._dirty = false;

        const container = document.getElementById('combatLogEntries');
        if (!container) return;

        const entries = this.logEntries;
        if (entries.length === 0) {
            container.innerHTML = '<div class="combat-log-entry" style="opacity:0.3"><span class="log-text">暂无战斗记录</span></div>';
            return;
        }

        let html = '';
        const maxShow = Math.min(entries.length, 8);
        for (let i = 0; i < maxShow; i++) {
            const e = entries[i];
            const alpha = Math.min(1, e.time / 2.0);
            html += `<div class="combat-log-entry" style="opacity:${alpha}">
                <span class="log-icon">${e.icon}</span>
                <span class="log-text" style="color:${e.color}">${this._escapeHtml(e.text)}</span>
            </div>`;
        }
        container.innerHTML = html;
    },

    /** 转义 HTML 特殊字符 */
    _escapeHtml(str) {
        const div = document.createElement('div');
        div.appendChild(document.createTextNode(str));
        return div.innerHTML;
    },

    /** 清除所有日志 */
    clear() {
        this.floatingTexts = [];
        this.logEntries = [];
        this._dirty = true;
    }
};
