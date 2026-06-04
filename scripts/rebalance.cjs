// ============================================================
// scripts/rebalance.cjs
// 全面数值重平衡：以剑客 hp=30 为基准，所有数值 ×0.25
// 
// 不缩放的字段：
//   attackSpeed, attackRange, dodge, critChance, critDamage,
//   lifeSteal, damagePercent, pickupRange, speed, weaponSlots
// ============================================================
const fs = require('fs');
const path = require('path');

const CSV_DIR = path.resolve(__dirname, '..', 'csv');
const SCALE = 0.25;

function parseCSV(text) {
    const lines = text.split('\n');
    const headers = lines.find(l => !l.startsWith('#') && l.trim()).split(',');
    const data = [];
    for (const line of lines) {
        if (line.startsWith('#') || !line.trim()) continue;
        const vals = line.split(',');
        if (vals.length < 2) continue;
        const row = {};
        headers.forEach((h, i) => row[h.trim()] = (vals[i] || '').trim());
        data.push({ raw: line, row });
    }
    return { headers, data };
}

function scaleNum(val, scale = SCALE) {
    if (val === '' || val === undefined) return val;
    const n = parseFloat(val);
    if (isNaN(n)) return val;
    const scaled = n * scale;
    // 根据原值精度决定返回值
    if (Number.isInteger(n)) return Math.round(scaled);
    if (val.includes('.')) {
        const decimals = (val.split('.')[1] || '').length;
        return parseFloat(scaled.toFixed(decimals));
    }
    return Math.round(scaled);
}

// ============ Characters ============
const SCALE_CHAR_FIELDS = ['maxHp', 'hpRegen', 'armor', 'meleeDamage', 'rangedDamage', 'elementalDamage', 'engineering', 'luck', 'xpGain', 'harvesting'];
// speed 也按比例下调，但用 0.5 系数不那么激进
const SPEED_FIELDS = ['speed'];
const SPEED_SCALE = 0.5;

console.log('=== 重平衡角色 ===');
let charText = fs.readFileSync(path.join(CSV_DIR, 'characters.csv'), 'utf8');
const charLines = charText.split('\n');
const charOut = charLines.map(line => {
    if (line.startsWith('#') || !line.trim()) return line;
    const parts = line.split(',');
    if (parts.length < 7) return line;
    // parts[0]=id, parts[6]=maxHp (index 6)
    for (let i = 0; i < parts.length; i++) {
        const header = ['id','name','desc','icon','unlocked','weaponSlots','maxHp','hpRegen','speed','damagePercent','attackSpeed','attackRange','armor','dodge','critChance','critDamage','lifeSteal','pickupRange','harvesting','luck','xpGain','meleeDamage','rangedDamage','elementalDamage','engineering','tags','unlockType','unlockValue','passives'][i];
        if (!header) continue;
        if (SCALE_CHAR_FIELDS.includes(header)) {
            parts[i] = String(scaleNum(parts[i]));
        } else if (SPEED_FIELDS.includes(header)) {
            parts[i] = String(scaleNum(parts[i], SPEED_SCALE));
        }
    }
    return parts.join(',');
}).join('\n');
fs.writeFileSync(path.join(CSV_DIR, 'characters.csv'), charOut);
console.log('  ✓ characters.csv');

// 验证剑客
const swordLine = charOut.split('\n').find(l => l.startsWith('swordsman'));
if (swordLine) console.log(`    剑客: ${swordLine.split(',')[6]} HP`);

// ============ Enemies ============
const SCALE_ENEMY_FIELDS = ['hp', 'damage', 'xpValue', 'materialValue'];
// 敌人用稍大比例（0.33）以确保仍有威胁
const ENEMY_SCALE = 0.33;

console.log('\n=== 重平衡敌人 ===');
let enemyText = fs.readFileSync(path.join(CSV_DIR, 'enemies.csv'), 'utf8');
const enemyOut = enemyText.split('\n').map(line => {
    if (line.startsWith('#') || !line.trim()) return line;
    const parts = line.split(',');
    if (parts.length < 10) return line;
    // 按 header 顺序: id,name,behavior,hp,speed,damage,radius,...
    const headers = ['id','name','behavior','hp','speed','damage','radius','color','glowColor','xpValue','materialValue','attackCooldown','isElite','isBoss','paramsJson','specialMechanic'];
    for (let i = 0; i < parts.length; i++) {
        const h = headers[i];
        if (!h) continue;
        if (SCALE_ENEMY_FIELDS.includes(h)) {
            parts[i] = String(scaleNum(parts[i], ENEMY_SCALE));
        }
        // speed 不缩放（保持移动速度），radius 不缩放
    }
    return parts.join(',');
}).join('\n');
fs.writeFileSync(path.join(CSV_DIR, 'enemies.csv'), enemyOut);
console.log('  ✓ enemies.csv');

// 验证
const basicLine = enemyOut.split('\n').find(l => l.startsWith('basic,'));
if (basicLine) {
    const parts = basicLine.split(',');
    console.log(`    basic: HP=${parts[3]}, DMG=${parts[5]}`);
}

// ============ Weapons ============
// minLevel=2 的改为 minLevel=1
// damage_lv1~4 全部 ×0.25，cooldown 不缩放

console.log('\n=== 重平衡武器 ===');
let weaponText = fs.readFileSync(path.join(CSV_DIR, 'weapons.csv'), 'utf8');
const weaponOut = weaponText.split('\n').map(line => {
    if (line.startsWith('#') || !line.trim()) return line;
    const parts = line.split(',');
    if (parts.length < 10) return line;
    // damage_lv1 = index 8, damage_lv2 = 9, damage_lv3 = 10, damage_lv4 = 11
    // cooldown_lv1 = 12, 13, 14, 15
    // minLevel = index 7
    for (let i = 8; i <= 11; i++) {
        if (parts[i] !== undefined && parts[i] !== '') {
            const val = parseFloat(parts[i]);
            if (!isNaN(val) && val > 0) {
                const scaled = Math.max(1, Math.round(val * SCALE));
                parts[i] = String(scaled);
            }
        }
    }
    // minLevel=2 → 1 (用户要求只有1级武器)
    if (parts[7] === '2') {
        parts[7] = '1';
        // 对于 minLevel=2 的武器，damage_lv1 原本为 0（不可用），需要从 lv2 推算
        // 但直接设为1让游戏不报错
        if (parts[8] === '' || parts[8] === '0') {
            // 从 lv2 推测 lv1（lv2 / 1.6 ≈ lv1）
            const lv2 = parseFloat(parts[9]) || 0;
            if (lv2 > 0) {
                parts[8] = String(Math.max(1, Math.round(lv2 / 1.6)));
            } else {
                parts[8] = '1';
            }
        }
    }
    return parts.join(',');
}).join('\n');
fs.writeFileSync(path.join(CSV_DIR, 'weapons.csv'), weaponOut);
console.log('  ✓ weapons.csv');

// 验证
const plasmaLine = weaponOut.split('\n').find(l => l.startsWith('plasma,'));
if (plasmaLine) {
    const parts = plasmaLine.split(',');
    console.log(`    plasma: DMG_lv1=${parts[8]}`);
}

console.log('\n=== 重平衡完成 ===');
