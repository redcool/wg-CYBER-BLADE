// ============================================================
// scripts/gen_card_icons.cjs
// 生成升级卡 SVG 图标，每个 stat 类别一个 SVG
// 输出到 assets/levelUpCards/
// ============================================================
const fs = require('fs');
const path = require('path');

const OUT = path.resolve(__dirname, '..', 'assets', 'levelUpCards');
fs.mkdirSync(OUT, { recursive: true });

// 每张卡 64×64 SVG，Cyber Blade 风格（暗色透明底，发光描边）
const ICONS = {
    maxHp: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M32 54S12 40 12 26c0-8 6-14 14-14 5 0 9 2 12 5 3 2 7 2 12 0 3-3 7-5 12-5 8 0 14 6 14 14 0 14-20 28-20 28z" fill="none" stroke="#ff3355" stroke-width="2.5" stroke-linejoin="round"/></svg>', color: '#ff3355' },
    hpRegen: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M20 40Q32 52 44 40Q50 34 44 28L32 16 20 28Q14 34 20 40z" fill="none" stroke="#44ff88" stroke-width="2" stroke-linejoin="round"/><path d="M30 26L34 26 34 30 38 30 38 34 34 34 34 38 30 38 30 34 26 34 26 30 30 30z" fill="#44ff88"/></svg>', color: '#44ff88' },
    lifeSteal: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M16 20L26 14 34 18 42 12 52 18 48 30 36 48 28 48 16 30z" fill="none" stroke="#ff2266" stroke-width="2" stroke-linejoin="round"/><circle cx="32" cy="28" r="4" fill="#ff2266"/><path d="M38 38Q42 44 48 48" fill="none" stroke="#ff2266" stroke-width="2" stroke-linecap="round"/></svg>', color: '#ff2266' },
    damagePercent: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="14" fill="none" stroke="#ffcc00" stroke-width="2"/><path d="M32 18L36 28 46 28 38 34 40 44 32 38 24 44 26 34 18 28 28 28z" fill="#ffcc00" opacity="0.6"/></svg>', color: '#ffcc00' },
    meleeDamage: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M8 56L28 36M40 24L56 8" fill="none" stroke="#00ddff" stroke-width="2.5" stroke-linecap="round"/><path d="M12 8L56 52 52 56 8 12z" fill="none" stroke="#00ddff" stroke-width="2" stroke-linejoin="round"/></svg>', color: '#00ddff' },
    rangedDamage: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M8 32L48 12 44 28 56 32 44 36 48 52z" fill="none" stroke="#ff8833" stroke-width="2" stroke-linejoin="round"/><circle cx="32" cy="32" r="3" fill="#ff8833"/></svg>', color: '#ff8833' },
    elementalDamage: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M32 6L38 24 56 24 42 34 48 52 32 42 16 52 22 34 8 24 26 24z" fill="none" stroke="#aa66ff" stroke-width="2" stroke-linejoin="round"/><circle cx="32" cy="28" r="3" fill="#aa66ff"/></svg>', color: '#aa66ff' },
    attackSpeed: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M36 8L18 34 30 34 22 56 48 26 34 26 44 8z" fill="none" stroke="#ffff44" stroke-width="2" stroke-linejoin="round"/></svg>', color: '#ffff44' },
    critChance: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M32 4L38 22 56 22 42 34 48 52 32 42 16 52 22 34 8 22 26 22z" fill="none" stroke="#ff4444" stroke-width="2.5" stroke-linejoin="round"/></svg>', color: '#ff4444' },
    engineering: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="10" fill="none" stroke="#44aaff" stroke-width="2"/><circle cx="32" cy="32" r="4" fill="#44aaff"/><path d="M32 8L34 16 30 16zM32 48L34 56 30 56zM8 32L16 34 16 30zM48 32L56 34 56 30z" fill="#44aaff"/><path d="M14 14L20 20M44 44L50 50M14 50L20 44M44 20L50 14" fill="none" stroke="#44aaff" stroke-width="2" stroke-linecap="round"/></svg>', color: '#44aaff' },
    attackRange: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="6" fill="#44ddff" opacity="0.3"/><circle cx="32" cy="32" r="6" fill="none" stroke="#44ddff" stroke-width="2"/><path d="M32 8L34 14 30 14zM32 50L34 56 30 56zM8 32L14 34 14 30zM50 32L56 34 56 30z" fill="#44ddff"/><path d="M14 14L18 18M46 46L50 50M14 50L18 46M46 18L50 14" fill="none" stroke="#44ddff" stroke-width="1.5" stroke-linecap="round"/></svg>', color: '#44ddff' },
    armor: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M16 12L32 6 48 12v14c0 12-16 26-16 26S16 38 16 26z" fill="none" stroke="#44ccff" stroke-width="2" stroke-linejoin="round"/><path d="M26 28L30 32 38 24" fill="none" stroke="#44ccff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>', color: '#44ccff' },
    dodge: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M16 52Q8 40 10 28 12 18 22 14 30 10 38 12L56 8 50 24Q52 32 48 40 42 50 32 52 24 54 16 52z" fill="none" stroke="#66ffcc" stroke-width="2" stroke-linejoin="round"/><path d="M38 26Q44 20 48 16" fill="none" stroke="#66ffcc" stroke-width="2" stroke-linecap="round"/></svg>', color: '#66ffcc' },
    speed: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="20" fill="none" stroke="#ff6644" stroke-width="2"/><path d="M32 12L36 24 48 24 38 32 42 44 32 36 22 44 26 32 16 24 28 24z" fill="none" stroke="#ff6644" stroke-width="2" stroke-linejoin="round"/><path d="M8 56L20 40" fill="none" stroke="#ff6644" stroke-width="2" stroke-linecap="round"/></svg>', color: '#ff6644' },
    luck: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M32 6L36 18 48 18 38 26 42 38 32 30 22 38 26 26 16 18 28 18z" fill="none" stroke="#44ff44" stroke-width="2" stroke-linejoin="round"/><circle cx="32" cy="28" r="2" fill="#44ff44"/></svg>', color: '#44ff44' },
    materialGain: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><circle cx="32" cy="32" r="18" fill="none" stroke="#ffcc44" stroke-width="2"/><path d="M32 14L34 24 44 24 36 30 38 40 32 34 26 40 28 30 20 24 30 24z" fill="#ffcc44" opacity="0.5"/><circle cx="32" cy="32" r="4" fill="none" stroke="#ffcc44" stroke-width="1.5"/></svg>', color: '#ffcc44' },
    weaponLevelUp: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M10 56L30 36M42 24L58 8" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-linecap="round"/><path d="M14 10L54 50 50 54 10 14z" fill="none" stroke="#ffffff" stroke-width="2" stroke-linejoin="round"/><circle cx="44" cy="20" r="8" fill="none" stroke="#ffcc00" stroke-width="2"/><path d="M44 16L44 24M40 20L48 20" stroke="#ffcc00" stroke-width="2" stroke-linecap="round"/></svg>', color: '#ffffff' },
    weaponQualityUp: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M32 6L36 18 48 18 38 26 42 38 32 30 22 38 26 26 16 18 28 18z" fill="none" stroke="#ffcc00" stroke-width="2.5" stroke-linejoin="round"/><circle cx="42" cy="42" r="10" fill="none" stroke="#ff88ff" stroke-width="2"/><path d="M42 38L42 46M38 42L46 42" stroke="#ff88ff" stroke-width="2" stroke-linecap="round"/></svg>', color: '#ffcc00' },
    addWeaponSlot: { svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect x="14" y="20" width="14" height="28" rx="2" fill="none" stroke="#44ddff" stroke-width="2"/><rect x="36" y="20" width="14" height="28" rx="2" fill="none" stroke="#44ddff" stroke-width="2"/><circle cx="32" cy="12" r="6" fill="none" stroke="#ffcc44" stroke-width="2"/><path d="M32 9L32 15M29 12L35 12" stroke="#ffcc44" stroke-width="2" stroke-linecap="round"/></svg>', color: '#44ddff' },
};

// 写入 SVGs
for (const [key, icon] of Object.entries(ICONS)) {
    const svg = icon.svg;
    fs.writeFileSync(path.join(OUT, `${key}.svg`), svg);
    console.log(`  ✓ ${key}.svg`);
}

// 也生成 desc.json 供 UI 引用
const desc = {};
for (const [key, icon] of Object.entries(ICONS)) {
    desc[key] = { color: icon.color };
}
fs.writeFileSync(path.join(OUT, 'iconDesc.json'), JSON.stringify(desc, null, 2));
console.log('\n  ✓ iconDesc.json');
console.log(`\n共生成 ${Object.keys(ICONS).length} 个 SVG 图标 → ${OUT}`);
