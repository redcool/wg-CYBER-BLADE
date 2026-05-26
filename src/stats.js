// ============================================================
// stats.js - 统一数值系统（v2：上限 + 递减 + 平衡）
// ============================================================
const StatsSystem = {
    // -------------------------------------------------------
    // 1. 属性定义（含上限、显示格式）
    // -------------------------------------------------------
    statDefs: {
        maxHp: {
            label: '最大生命', icon: '❤️', fmt: 'int',
            min: 5, max: null,
            desc: (v) => `最大生命 ${v}`,
        },
        hpRegen: {
            label: '生命回复', icon: '💚', fmt: 'float1',
            min: 0, max: null,
            desc: (v) => `每秒生命回复 +${v.toFixed(1)}`,
        },
        damage: {
            label: '攻击力', icon: '🗡️', fmt: 'int',
            min: 1, max: null,
            desc: (v) => `攻击力 +${Math.round(v * 100)}%`,
        },
        attackSpeed: {
            label: '攻击速度', icon: '⚡', fmt: 'float2',
            min: 0.2, max: 5.0,
            desc: (v) => `攻击速度 +${Math.round(v * 100)}%`,
        },
        attackRange: {
            label: '攻击范围', icon: '🎯', fmt: 'int',
            min: 20, max: 800,
            desc: (v) => `攻击范围 +${Math.round(v * 100)}%`,
        },
        armor: {
            label: '护甲', icon: '🛡️', fmt: 'int',
            min: 0, max: 100,
            desc: (v) => `护甲 +${v}（减伤 ${Math.round(v / (v + 50) * 100)}%）`,
        },
        dodge: {
            label: '闪避', icon: '💨', fmt: 'percent',
            min: 0, max: 0.6,
            desc: (v) => `闪避率 +${Math.round(v * 100)}%（上限 60%）`,
        },
        critChance: {
            label: '暴击率', icon: '💥', fmt: 'percent',
            min: 0, max: 0.8,
            desc: (v) => `暴击率 +${Math.round(v * 100)}%（上限 80%）`,
        },
        critMultiplier: {
            label: '暴击伤害', icon: '🔥', fmt: 'float1',
            min: 1.0, max: 6.0,
            desc: (v) => `暴击伤害 ${v.toFixed(1)} 倍`,
        },
        speed: {
            label: '移动速度', icon: '⚡', fmt: 'int',
            min: 50, max: 400,
            desc: (v) => `移动速度 +${Math.round(v * 100)}%`,
        },
        bulletCount: {
            label: '子弹数量', icon: '🔫', fmt: 'int',
            min: 1, max: 20,
            desc: (v) => `子弹 +${v}`,
        },
        bulletPierce: {
            label: '穿透', icon: '➡️', fmt: 'int',
            min: 0, max: 10,
            desc: (v) => `穿透 +${v}`,
        },
        bulletSpeed: {
            label: '弹道速度', icon: '➡️', fmt: 'int',
            min: 100, max: 2000,
            desc: (v) => `弹道速度 +${Math.round(v * 100)}%`,
        },
        lifeSteal: {
            label: '生命偷取', icon: '🩸', fmt: 'percent',
            min: 0, max: 0.5,
            desc: (v) => `生命偷取 +${Math.round(v * 100)}%（上限 50%）`,
        },
        harvesting: {
            label: '收获加成', icon: '💰', fmt: 'percent',
            min: 0, max: 500,
            desc: (v) => `材料收获 +${v}%`,
        },
        luck: {
            label: '幸运', icon: '🍀', fmt: 'int',
            min: 0, max: 50,
            desc: (v) => `幸运 +${v}`,
        },
        pickupRange: {
            label: '拾取范围', icon: '🧲', fmt: 'int',
            min: 10, max: 300,
            desc: (v) => `拾取范围 +${v}`,
        },
    },

    // -------------------------------------------------------
    // 2. 数值约束工具
    // -------------------------------------------------------

    /** 将属性值钳制在定义范围内 */
    clampStat(statId, value) {
        const def = this.statDefs[statId];
        if (!def) return value;
        if (def.min !== null && def.min !== undefined) value = Math.max(def.min, value);
        if (def.max !== null && def.max !== undefined) value = Math.min(def.max, value);
        return value;
    },

    /** 钳制玩家所有属性（含 hp 钳制到 maxHp） */
    clampPlayer(player) {
        if (!player) return;
        for (const statId of Object.keys(this.statDefs)) {
            if (player[statId] !== undefined) {
                player[statId] = this.clampStat(statId, player[statId]);
            }
        }
        // 额外钳制 hp ≤ maxHp
        if (player.hp !== undefined && player.maxHp !== undefined) {
            player.hp = Math.min(player.maxHp, Math.max(0, player.hp));
        }
    },

    // -------------------------------------------------------
    // 3. 伤害公式
    // -------------------------------------------------------

    /** 护甲减伤率：递减曲线 */
    armorDR(armor) {
        return armor / (armor + 50);
    },

    /** 计算最终伤害（含护甲减伤） */
    calcDamageReduction(rawDamage, armor) {
        const dr = this.armorDR(armor);
        return Math.max(1, Math.floor(rawDamage * (1 - dr)));
    },

    // -------------------------------------------------------
    // 4. 显示工具
    // -------------------------------------------------------

    /** 格式化属性值用于显示 */
    formatStat(statId, value) {
        const def = this.statDefs[statId];
        if (!def) return String(value);
        switch (def.fmt) {
            case 'int': return String(Math.round(value));
            case 'float1': return value.toFixed(1);
            case 'float2': return value.toFixed(2);
            case 'percent': return Math.round(value * 100) + '%';
            default: return String(value);
        }
    },

    /** 获取属性上限信息文本 */
    getCapInfo(statId, value) {
        const def = this.statDefs[statId];
        if (!def) return '';
        if (def.max === null) return '';
        const pct = Math.round((value / def.max) * 100);
        if (pct >= 90) return '⚠️ 接近上限';
        if (pct >= 70) return `已使用 ${pct}% 上限`;
        return '';
    },

    /** 获取显示用的统计列表（含计算值） */
    getDisplayStats(player) {
        if (!player) return [];
        const list = [];
        const statIds = [
            'maxHp', 'hpRegen', 'armor', 'dodge', 'damage', 'attackSpeed',
            'critChance', 'critMultiplier', 'attackRange', 'bulletSpeed',
            'bulletCount', 'bulletPierce', 'lifeSteal', 'speed',
            'pickupRange', 'harvesting', 'luck',
        ];
        for (const id of statIds) {
            const def = this.statDefs[id];
            if (!def) continue;
            const rawValue = player[id] ?? 0;
            const displayValue = this.formatStat(id, rawValue);
            const extra = this.getCapInfo(id, rawValue);
            let note = '';
            if (id === 'armor') {
                const dr = this.armorDR(rawValue);
                note = `减伤 ${Math.round(dr * 100)}%`;
            }
            list.push({
                id, icon: def.icon, label: def.label,
                value: displayValue, raw: rawValue,
                extra, note, cap: def.max,
                pctToCap: def.max ? Math.min(100, Math.round((rawValue / def.max) * 100)) : null,
            });
        }
        return list;
    },

    // -------------------------------------------------------
    // 5. 经验系统
    // -------------------------------------------------------

    /** 升级所需经验（递增曲线） */
    xpForLevel(level) {
        if (level <= 1) return 20;
        if (level <= 5) return Math.floor(20 + (level - 1) * 15);
        if (level <= 10) return Math.floor(80 + (level - 5) * 30);
        if (level <= 20) return Math.floor(230 + (level - 10) * 60);
        return Math.floor(830 + (level - 20) * 120);
    },

    // -------------------------------------------------------
    // 6. 等级可选项（百分比/搭配混合）
    // -------------------------------------------------------
    levelUpOptions: [
        { id: 'maxHp',         name: '生命强化',    desc: '最大生命 +20%',   icon: '❤️',
          apply: (p) => { p.maxHp = Math.floor(p.maxHp * 1.20); } },
        { id: 'hpRegen',       name: '生命恢复',    desc: '回复 +0.5/秒',   icon: '💚',
          apply: (p) => { p.hpRegen += 0.5; } },
        { id: 'damage',        name: '攻击强化',    desc: '攻击力 +22%',    icon: '🗡️',
          apply: (p) => { p.damage = Math.floor(p.damage * 1.22); } },
        { id: 'attackSpeed',   name: '攻速提升',    desc: '攻速 +18%',     icon: '⚡',
          apply: (p) => { p.attackSpeed = Math.min(5.0, p.attackSpeed * 1.18); } },
        { id: 'attackRange',   name: '射程提升',    desc: '射程 +15%',     icon: '🎯',
          apply: (p) => { p.attackRange = Math.min(800, p.attackRange * 1.15); } },
        { id: 'armor',         name: '护甲强化',    desc: '护甲 +3',       icon: '🛡️',
          apply: (p) => { p.armor = Math.min(100, p.armor + 3); } },
        { id: 'dodge',         name: '闪避强化',    desc: '闪避 +3%',      icon: '💨',
          apply: (p) => { p.dodge = Math.min(0.6, p.dodge + 0.03); } },
        { id: 'critChance',    name: '暴击强化',    desc: '暴击 +4%',      icon: '💥',
          apply: (p) => { p.critChance = Math.min(0.8, p.critChance + 0.04); } },
        { id: 'critMultiplier',name: '暴伤提升',    desc: '暴伤 +0.5x',    icon: '🔥',
          apply: (p) => { p.critMultiplier = Math.min(6.0, p.critMultiplier + 0.5); } },
        { id: 'speed',         name: '机动强化',    desc: '移速 +10%',     icon: '⚡',
          apply: (p) => { p.speed = Math.min(400, p.speed * 1.10); } },
        { id: 'bulletCount',   name: '多重射击',    desc: '子弹 +1',       icon: '🔫',
          apply: (p) => { p.bulletCount = Math.min(20, p.bulletCount + 1); } },
        { id: 'bulletPierce',  name: '穿透弹',      desc: '穿透 +1',       icon: '➡️',
          apply: (p) => { p.bulletPierce = Math.min(10, p.bulletPierce + 1); } },
        { id: 'lifeSteal',     name: '生命偷取',    desc: '偷取 +3%',      icon: '🩸',
          apply: (p) => { p.lifeSteal = Math.min(0.5, p.lifeSteal + 0.03); } },
        { id: 'bulletSpeed',   name: '弹速提升',    desc: '弹速 +15%',     icon: '➡️',
          apply: (p) => { p.bulletSpeed = Math.min(2000, p.bulletSpeed * 1.15); } },
        { id: 'harvesting',    name: '丰收',        desc: '收获 +20%',     icon: '💰',
          apply: (p) => { p.harvesting = Math.min(500, p.harvesting + 20); } },
        { id: 'pickupRange',   name: '引力场',      desc: '拾取范围 +20',  icon: '🧲',
          apply: (p) => { p.pickupRange = Math.min(300, p.pickupRange + 20); } },
        { id: 'luck',          name: '幸运提升',    desc: '幸运 +2',       icon: '🍀',
          apply: (p) => { p.luck = Math.min(50, p.luck + 2); } },
    ],
};
