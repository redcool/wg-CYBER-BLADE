// ============================================================
// scripts/rebalance_items.cjs v4
// 无 bug 版本：处理正/负值，hpRegen 保留1位小数
// ============================================================
const fs = require('fs');
const path = require('path');

const CSV_PATH = path.resolve(__dirname, '..', 'csv', 'items.csv');
const SCALE = 0.25;

// round: 'int' → 四舍五入整数, 'dec1' → 保留1位小数
const FIELD_CFG = {
    maxHp:           { scale: 0.25, round: 'int', min: 1 },
    hpRegen:         { scale: 0.25, round: 'dec1', min: 0.1 },
    speed:           { scale: 0.25, round: 'int', min: 1 },
    armor:           { scale: 0.25, round: 'int', min: 1 },
    meleeDamage:     { scale: 0.25, round: 'int', min: 1 },
    rangedDamage:    { scale: 0.25, round: 'int', min: 1 },
    elementalDamage: { scale: 0.25, round: 'int', min: 1 },
    pickupRange:     { scale: 0.25, round: 'int', min: 1 },
    attackRange:     { scale: 0.25, round: 'int', min: 1 },
    engineering:     { scale: 0.25, round: 'int', min: 1 },
    luck:            { scale: 0.25, round: 'int', min: 1 },
};

function splitCSVRow(line) {
    const fields = [];
    let cur = '';
    let inQuotes = false;
    let i = 0;
    while (i < line.length) {
        const ch = line[i];
        const next = line[i + 1] || '';
        if (ch === '"' && !inQuotes) { inQuotes = true; cur += ch; i++; }
        else if (ch === '"' && inQuotes && next === '"') { cur += '""'; i += 2; }
        else if (ch === '"' && inQuotes) { inQuotes = false; cur += ch; i++; }
        else if (ch === ',' && !inQuotes) { fields.push(cur); cur = ''; i++; }
        else { cur += ch; i++; }
    }
    fields.push(cur);
    return fields;
}

/** 从 CSV 引用的字段中提取纯 JSON 字符串 */
function unescapeCSVJson(raw) {
    let s = raw.trim();
    if (s.startsWith('"') && s.endsWith('"')) s = s.slice(1, -1);
    return s.replace(/""/g, '"');
}

/** 将 JSON 字符串包装为 CSV 安全格式 */
function escapeCSVJson(jsonStr) {
    // 如果包含逗号，需要 CSV 引用
    if (jsonStr.includes(',')) {
        return '"' + jsonStr.replace(/"/g, '""') + '"';
    }
    return jsonStr;
}

function scaleVal(val, cfg) {
    const raw = val * cfg.scale;
    let scaled;
    if (cfg.round === 'dec1') {
        scaled = Math.round(raw * 10) / 10;
    } else {
        scaled = Math.round(raw);
    }
    // 正数有最小值，负数保留（但也要合理缩放）
    if (val > 0) {
        return Math.max(cfg.min || 1, scaled);
    } else if (val < 0) {
        // 负值按比例缩放但不低于 -1（保持有意义的惩罚）
        return Math.min(-1, Math.round(raw));
    }
    return scaled;
}

console.log('=== 重平衡物品 statMods v4 ===');
let text = fs.readFileSync(CSV_PATH, 'utf8');
const lines = text.split('\n');
let changedCount = 0;

const out = lines.map(line => {
    if (line.startsWith('#') || !line.trim()) return line;
    const parts = splitCSVRow(line);
    if (parts.length < 11) return line;
    
    const oldRaw = parts[10];
    if (oldRaw === '{}' || oldRaw === '""{}""') return line;
    
    try {
        const jsonStr = unescapeCSVJson(oldRaw);
        const mods = JSON.parse(jsonStr);
        const result = {};
        let changed = false;
        
        for (const [key, val] of Object.entries(mods)) {
            const cfg = FIELD_CFG[key];
            if (cfg && typeof val === 'number' && val !== 0) {
                const newVal = scaleVal(val, cfg);
                result[key] = newVal;
                if (newVal !== val) changed = true;
            } else {
                result[key] = val;
            }
        }
        
        if (!changed) return line;
        
        const newJsonStr = JSON.stringify(result);
        parts[10] = escapeCSVJson(newJsonStr);
        changedCount++;
        return parts.join(',');
    } catch (e) {
        return line;
    }
}).join('\n');

fs.writeFileSync(CSV_PATH, out);
console.log(`  ✓ items.csv (${changedCount} 个物品被修改)`);

// 验证
console.log('\n验证:');
for (const id of ['hp_up', 'hp_regen', 'melee_dmg', 'life_steal', 'crit_up', 'bigger_hp', 'giant_heart', 'blood_orb', 'celestial_wings', 'ninja_tabi', 'stone_armor', 'dmg_up', 'regen_belt']) {
    const sample = out.split('\n').filter(l => !l.startsWith('#') && l.trim());
    const line = sample.find(l => l.startsWith(id + ','));
    if (line) {
        const parts = splitCSVRow(line);
        const raw = parts[10];
        try {
            const json = JSON.parse(unescapeCSVJson(raw));
            console.log(`  ${parts[1]}: ${JSON.stringify(json)}`);
        } catch(e) {
            console.log(`  ${parts[1]}: RAW=${raw}`);
        }
    }
}
console.log('\n=== 完成 ===');
