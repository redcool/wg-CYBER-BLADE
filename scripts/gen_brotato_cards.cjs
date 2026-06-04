/**
 * Generate Brotato-style levelUpCards.csv
 * All 16 stats × 4 tiers + special cards
 * Uses exact Brotato upgrade names and values
 */
const fs = require('fs');

// Helper: proper CSV field quoting
function csvField(val) {
  if (val === undefined || val === null || val === '') return '';
  const s = String(val);
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

// Brotato stat definitions: [statField, name, valuesI/II/III/IV, tags]
const BROTATO_STATS = [
  // [field, name, [v1, v2, v3, v4], tags, descSuffix]
  ['maxHp',       'Heart',     [3, 6, 9, 12],      '',       '最大生命'],
  ['hpRegen',     'Lungs',     [1, 2, 3, 4],        '',       '生命回复/秒'],
  ['lifeSteal',   'Teeth',     [0.01, 0.02, 0.03, 0.04], 'melee', '生命偷取'],
  ['damagePercent','Triceps',  [0.05, 0.08, 0.12, 0.16], '',       '伤害%'],
  ['meleeDamage', 'Forearms',  [2, 4, 6, 8],         'melee',  '近战伤害'],
  ['rangedDamage','Shoulders', [1, 2, 3, 4],         'ranged', '远程伤害'],
  ['elementalDamage','Brain',  [1, 2, 3, 4],         'fire|explosive', '元素伤害'],
  ['attackSpeed', 'Reflexes',  [0.05, 0.10, 0.15, 0.20], '',       '攻速'],
  ['critChance',  'Fingers',   [0.03, 0.05, 0.07, 0.09], 'crit',  '暴击率'],
  ['engineering', 'Skull',     [2, 3, 4, 5],         'tech',   '工程'],
  ['attackRange', 'Eyes',      [15, 30, 45, 60],     'ranged', '射程'],
  ['armor',       'Chest',     [1, 2, 3, 4],         '',       '护甲'],
  ['dodge',       'Back',      [0.03, 0.06, 0.09, 0.12], '',       '闪避'],
  ['speed',       'Legs',      [3, 6, 9, 12],        '',       '移速'],
  ['luck',        'Nose',      [5, 10, 15, 20],      'economy','幸运'],
  ['materialGain','Hands',     [0.05, 0.08, 0.10, 0.12], 'economy', '材料获取%'],
];

// Tier unlock levels (matching Brotato's system)
// T1: level 1, T2: level 5, T3: level 10, T4: level 20
const TIER_UNLOCK = [1, 5, 10, 20];
const TIER_NAMES = ['I', 'II', 'III', 'IV'];
// Weights for each tier (within unlocked tiers, matches Brotato rarity scaling)
const TIER_WEIGHTS = [60, 25, 10, 5];

// Icons per stat (emoji)
const STAT_ICONS = {
  maxHp: '❤️', hpRegen: '💚', lifeSteal: '🩸', damagePercent: '🗡️',
  meleeDamage: '⚔️', rangedDamage: '🏹', elementalDamage: '🔮',
  attackSpeed: '⚡', critChance: '💥', engineering: '🤖',
  attackRange: '🎯', armor: '🛡️', dodge: '💨', speed: '👟',
  luck: '🍀', materialGain: '💰',
};

// ===== GENERATE ROWS =====
const rows = [];

// Generate stat cards
for (const [field, name, values, tags, descSuffix] of BROTATO_STATS) {
  for (let t = 0; t < 4; t++) {
    const tier = TIER_NAMES[t];
    const val = values[t];
    const unlockLv = TIER_UNLOCK[t];
    const icon = STAT_ICONS[field] || '⬆';
    const fullName = t === 0 ? name : `${name} ${tier}`;
    // Format value display
    let desc;
    if (field === 'hpRegen') desc = `${descSuffix} +${val}`;
    else if (field === 'damagePercent' || field === 'attackSpeed' || field === 'critChance' || field === 'dodge' || field === 'materialGain' || field === 'lifeSteal')
      desc = `${descSuffix} +${(val*100).toFixed(0)}%`;
    else desc = `${descSuffix} +${val}`;
    
    const id = `${field}_t${t+1}`;
    rows.push([id, fullName, desc, icon, tier, field, val, tags, unlockLv, '', '']);
  }
}

// Special cards (weapon upgrade, slot, etc.)
const specialCards = [
  // id, name, desc, icon, tier, statField, statValue, tags, unlockLevel, actionType, actionValue
  ['weaponLvUp',   '武器升级', '随机武器+1级', '⚔️', 'II', '', '', '', 3, 'weaponLevelUp', ''],
  ['weaponQuality','品质提升', '随机武器品质+1', '✨', 'III', '', '', '', 6, 'weaponQualityUp', ''],
  ['weaponSlotUp', '武器槽',  '武器槽+1', '📦', 'IV', '', '', '', 10, 'addWeaponSlot', ''],
];
for (const card of specialCards) rows.push(card);

// ===== WRITE CSV =====
const header = '# id,name,desc,icon,tier,statField,statValue,tags,unlockLevel,actionType,actionValue\n' +
  '# Brotato-style 升级抽卡系统\n' +
  '# tier: I|II|III|IV\n' +
  '# statField: 属性字段名（maxHp, armor 等）\n' +
  '# statValue: 数值（3, 0.05, 15 等）\n' +
  '# tags: 流派标签（melee|ranged|fire|explosive|tech|crit|economy）\n' +
  '# unlockLevel: 角色等级解锁（1=T1, 5=T2, 10=T3, 20=T4）\n' +
  '# actionType: weaponLevelUp|weaponQualityUp|addWeaponSlot\n' +
  'id,name,desc,icon,tier,statField,statValue,tags,unlockLevel,actionType,actionValue';

const csvLines = rows.map(r => r.map(csvField).join(','));
fs.writeFileSync('csv/levelUpCards.csv', header + '\n' + csvLines.join('\n') + '\n', 'utf8');
console.log('Generated', rows.length, 'cards in csv/levelUpCards.csv');
