// ============================================================
// affixes.js — 词条系统（已禁用，保留代码供未来接入）
// 原始来源: engine-shop.js (affixDefs + 生成方法)
//           player.js (_AFFIX_MAP + _computeAffixBonuses)
// ============================================================
// 接入指南:
//   1. engine-shop.js: 取消注释 affixDefs / _rollAffix 等
//   2. player.js:      启用 _AFFIX_MAP / _computeAffixBonuses
//   3. player._updateSynergies(): 启用词条反转+应用段
//   4. ui.js:           恢复词条渲染代码
// ============================================================
// 注意: 本文件中的 desc 函数引用了 _ESHOP_STR 字符串表,
//       恢复时需确保 _ESHOP_STR 在 engine-shop.js 中已定义.
// ============================================================

// ============================================================
// 词条定义 (affixDefs)
// 每个词条的 name/desc/baseValue/perLevel/isInt
// ============================================================
const AFFIX_DEFS = {
    damagePct: {
        name: _ESHOP_STR.affix_damagePct, icon: '🗡️',
        desc: (v) => _ESHOP_STR.desc_damagePct.replace('{0}', Math.round(v * 100)),
        baseValue: [0.08, 0.15], perLevel: [0.02, 0.04],
    },
    attackSpeedPct: {
        name: _ESHOP_STR.affix_attackSpeedPct, icon: '⚡',
        desc: (v) => _ESHOP_STR.desc_attackSpeedPct.replace('{0}', Math.round(v * 100)),
        baseValue: [0.05, 0.10], perLevel: [0.01, 0.03],
    },
    critChancePct: {
        name: _ESHOP_STR.affix_critChancePct, icon: '💥',
        desc: (v) => _ESHOP_STR.desc_critChancePct.replace('{0}', Math.round(v * 100)),
        baseValue: [0.02, 0.04], perLevel: [0.005, 0.01],
    },
    critMultiplierAdd: {
        name: _ESHOP_STR.affix_critMultiplierAdd, icon: '🔥',
        desc: (v) => _ESHOP_STR.desc_critMultiplierAdd.replace('{0}', v.toFixed(1)),
        baseValue: [0.15, 0.30], perLevel: [0.05, 0.10],
    },
    lifeStealPct: {
        name: _ESHOP_STR.affix_lifeStealPct, icon: '🩸',
        desc: (v) => _ESHOP_STR.desc_lifeStealPct.replace('{0}', Math.round(v * 100)),
        baseValue: [0.01, 0.03], perLevel: [0.005, 0.01],
    },
    armor: {
        name: _ESHOP_STR.affix_armor, icon: '🛡️',
        desc: (v) => _ESHOP_STR.desc_armor.replace('{0}', v),
        baseValue: [1, 3], perLevel: [1, 1],
        isInt: true,
    },
    hpRegenPct: {
        name: _ESHOP_STR.affix_hpRegenPct, icon: '💚',
        desc: (v) => _ESHOP_STR.desc_hpRegenPct.replace('{0}', v.toFixed(1)),
        baseValue: [0.3, 0.8], perLevel: [0.1, 0.2],
    },
    maxHp: {
        name: _ESHOP_STR.affix_maxHp, icon: '❤️',
        desc: (v) => _ESHOP_STR.desc_maxHp.replace('{0}', v),
        baseValue: [5, 15], perLevel: [3, 5],
        isInt: true,
    },
    attackRangePct: {
        name: _ESHOP_STR.affix_attackRangePct, icon: '🎯',
        desc: (v) => _ESHOP_STR.desc_attackRangePct.replace('{0}', Math.round(v * 100)),
        baseValue: [0.05, 0.10], perLevel: [0.015, 0.03],
    },
    bulletSpeedPct: {
        name: _ESHOP_STR.affix_bulletSpeedPct, icon: '➡️',
        desc: (v) => _ESHOP_STR.desc_bulletSpeedPct.replace('{0}', Math.round(v * 100)),
        baseValue: [0.05, 0.10], perLevel: [0.015, 0.03],
    },
    bulletPierceAdd: {
        name: _ESHOP_STR.affix_bulletPierceAdd, icon: '🔱',
        desc: (v) => _ESHOP_STR.desc_bulletPierceAdd.replace('{0}', v),
        baseValue: [1, 1], perLevel: [0, 0],
        isInt: true,
    },
    knockbackAdd: {
        name: _ESHOP_STR.affix_knockbackAdd, icon: '💨',
        desc: (v) => _ESHOP_STR.desc_knockbackAdd.replace('{0}', v),
        baseValue: [20, 50], perLevel: [5, 15],
        isInt: true,
    },
};

// ============================================================
// 词条ID → 玩家属性映射 (_AFFIX_MAP)
// stat: 玩家属性名, op: 'mult'|'add'
// ============================================================
const AFFIX_MAP = {
    damagePct: { stat: 'damage', op: 'mult' },
    attackSpeedPct: { stat: 'attackSpeed', op: 'mult' },
    critChancePct: { stat: 'critChance', op: 'add' },
    critMultiplierAdd: { stat: 'critMultiplier', op: 'add' },
    lifeStealPct: { stat: 'lifeSteal', op: 'add' },
    armor: { stat: 'armor', op: 'add' },
    hpRegenPct: { stat: 'hpRegen', op: 'add' },
    maxHp: { stat: 'maxHp', op: 'add' },
    attackRangePct: { stat: 'attackRange', op: 'mult' },
    bulletSpeedPct: { stat: 'bulletSpeed', op: 'mult' },
    bulletPierceAdd: { stat: 'bulletPierce', op: 'add' },
    knockbackAdd: { stat: 'knockback', op: 'add' },
};

// ============================================================
// Helper 函数 (从 engine-shop.js 复制, 适配为独立函数)
// ============================================================

/**
 * 投掷一个词条
 * @param {number} level - 武器等级
 * @returns {{ id: string, value: number }}
 */
function _rollAffix(level) {
    const ids = Object.keys(AFFIX_DEFS);
    const id = ids[Math.floor(Math.random() * ids.length)];
    const def = AFFIX_DEFS[id];
    const base = def.baseValue[0] + Math.random() * (def.baseValue[1] - def.baseValue[0]);
    const perLvl = def.perLevel[0] + Math.random() * (def.perLevel[1] - def.perLevel[0]);
    let value = base + (level - 1) * perLvl;
    if (def.isInt) value = Math.round(value);
    else value = Math.round(value * 100) / 100;
    return { id, value };
}

/**
 * 投掷一个不重复的词条 ID
 * @param {string[]} existingIds - 已存在的词条 ID 数组
 * @returns {string|null} 新词条 ID 或 null（无可用）
 */
function _rollNewAffixId(existingIds) {
    const pool = Object.keys(AFFIX_DEFS).filter(id => !existingIds.includes(id));
    if (pool.length === 0) return null;
    return pool[Math.floor(Math.random() * pool.length)];
}

/**
 * 初始化武器词条（购买时调用）
 * @param {Object} weapon - 武器对象
 */
function _initWeaponAffixes(weapon) {
    const level = weapon.level || 1;
    weapon.affixes = [_rollAffix(level)];
}

/**
 * 合并时升级词条
 * @param {Object} weapon - 武器对象
 * @param {number} [fromLevel=1] - 合并来源等级
 */
function _increaseAffixesOnMerge(weapon, fromLevel) {
    const levelIncrease = fromLevel || 1;
    for (const aff of (weapon.affixes || [])) {
        const def = AFFIX_DEFS[aff.id];
        if (!def) continue;
        const inc = def.perLevel[0] + Math.random() * (def.perLevel[1] - def.perLevel[0]) * levelIncrease;
        if (def.isInt) aff.value += Math.round(inc);
        else aff.value = Math.round((aff.value + inc) * 100) / 100;
    }
}

/**
 * 确保武器词条数量达标
 * T1=1个词条, T2/T3/T4=2个词条, 最多2个
 * @param {Object} weapon - 武器对象
 */
function _ensureAffixCount(weapon) {
    if (!weapon.affixes) weapon.affixes = [];
    const level = weapon.level || 1;
    const quality = weapon.quality || 'T1';
    const maxAffixes = quality === 'T1' ? 1 : 2;
    const existingIds = weapon.affixes.map(a => a.id);
    while (weapon.affixes.length < maxAffixes) {
        const newId = _rollNewAffixId(existingIds);
        if (!newId) break;
        const newAff = _rollAffix(level);
        newAff.id = newId;
        weapon.affixes.push(newAff);
        existingIds.push(newId);
    }
}

/**
 * 合并时应用词条升级（带高亮标记）
 * @param {Object} weapon - 武器对象
 * @param {number} fromLevel - 合并来源等级
 */
function _applyMergeWithHighlights(weapon, fromLevel) {
    const before = (weapon.affixes || []).map(a => ({ id: a.id, value: a.value }));
    _increaseAffixesOnMerge(weapon, fromLevel);
    _ensureAffixCount(weapon);
    // highlight diff removed (was UI concern)
}

/**
 * 计算武器词条重 roll 价格
 * @param {Object} weapon - 武器对象
 * @returns {number} 重 roll 价格
 */
function getRerollCost(weapon) {
    const level = weapon.level || 1;
    const quality = weapon.quality || 'T1';
    const baseCosts = { T1: 5, T2: 8, T3: 14, T4: 22 };
    const base = baseCosts[quality] || 5;
    const rerollPenalty = (weapon._rerollCount || 0) * 2;
    return base + (level - 1) * 3 + rerollPenalty;
}

/**
 * 武器词条重 roll
 * 注意: 依赖 ShopSystem._updateWeaponParams(player, weapon.id) 外部调用
 * @param {Object} weapon - 武器对象
 * @param {Object} player - 玩家对象
 * @returns {boolean|Object} 失败返回 false, 成功返回 { cost, newAffixes }
 */
function rerollAffixes(weapon, player) {
    const cost = getRerollCost(weapon);
    if ((player.materials || 0) < cost) return false;
    player.materials -= cost;
    weapon._rerollCount = (weapon._rerollCount || 0) + 1;
    const level = weapon.level || 1;
    const quality = weapon.quality || 'T1';
    const maxCount = quality === 'T1' ? 1 : 2;
    weapon.affixes = [];
    const existingIds = [];
    for (let i = 0; i < maxCount; i++) {
        const newId = _rollNewAffixId(existingIds);
        const aff = _rollAffix(level);
        aff.id = newId || Object.keys(AFFIX_DEFS)[Math.floor(Math.random() * Object.keys(AFFIX_DEFS).length)];
        weapon.affixes.push(aff);
        if (newId) existingIds.push(newId);
    }
    // 恢复时需调用: ShopSystem._updateWeaponParams(player, weapon.id);
    return { cost, newAffixes: weapon.affixes };
}

/**
 * 计算玩家所有武器词条加成总和
 * @param {Object} p - 玩家对象
 * @returns {Object} { affixId: totalValue, ... }
 */
function computeAffixBonuses(p) {
    const bonuses = {};
    for (const w of (p.weapons || [])) {
        for (const aff of (w.affixes || [])) {
            bonuses[aff.id] = (bonuses[aff.id] || 0) + aff.value;
        }
    }
    return bonuses;
}

// ============================================================
// 导出
// ============================================================
if (typeof module !== 'undefined') {
    module.exports = {
        AFFIX_DEFS,
        AFFIX_MAP,
        _rollAffix,
        _rollNewAffixId,
        _initWeaponAffixes,
        _increaseAffixesOnMerge,
        _ensureAffixCount,
        _applyMergeWithHighlights,
        getRerollCost,
        rerollAffixes,
        computeAffixBonuses,
    };
}
