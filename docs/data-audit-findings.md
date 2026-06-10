# 数据审计发现（待讨论）

## 严重 BUG

### 1. `weaponSlots` 与 `maxWeapons` 字段名不匹配
- **文件：** `src/engine/character.js:149`
- **代码：** `player.weaponSlots = ch.weaponSlots || 6;`
- **问题：** CSV 列名是 `maxWeapons`，JS 读的是不存在的 `ch.weaponSlots`（旧字段名）
- **后果：** 所有角色武器槽 = `undefined || 6 = 6`，刺客/拳手/刀客应有 4 槽，实际 6 槽
- **影响：** 严重 ✅

### 2. 刀客 `critDamage` 解释错误
- **文件：** `src/engine/character.js:182-184` + `src/engine/formula.js:191-194`
- **CSV 注释：** `critDamage: 暴击伤害加算(小数, 0=基础2x, 0.5=2.5x)`
- **问题：** 刀客 `critDamage=0.5`，`formula.js` 直接将 0.5 作为暴击倍率（0.5x），而不是 `2.0 + 0.5 = 2.5x`
- **后果：** 刀客暴击造成减半伤害，角色设计被破坏
- **影响：** 严重 ✅

### 3. `speedMult` 解析但从未应用
- **文件：** `src/cyberblade/player.js:171-221` `_initWeaponParams` / `src/engine/engine-shop.js:822-873` `_updateWeaponParams`
- **影响武器：**
  - `chainsaw`（speedMult: -0.1）
  - `gatling`（speedMult: -0.1）
  - `minigun`（speedMult: -0.05）
  - `shield`（speedMult: -0.15）
- **后果：** 这些武器的减速惩罚未生效
- **影响：** 高 🟠

### 4. `armorAdd` / `hpRegenAdd` / `maxHpAdd` 解析但从未应用
- **文件：** 同上，未在任何运行时位置读取
- **影响武器：**
  - `shield`（armorAdd: 3）
  - `blessing`（armorAdd: 2）
  - `heal_gun`（hpRegenAdd: 2）
  - `holy_staff`（hpRegenAdd: 1）
  - `life_wand`（maxHpAdd: 5）
- **后果：** 五件医疗/防御武器的核心效果缺失
- **影响：** 高 🟠

### 5. `lifeStealAdd` 解析但从未应用
- **文件：** 同上
- **影响武器：**
  - `void_staff`（lifeStealAdd: 0.05）
- **后果：** 虚空杖 5% 生命偷取未生效
- **影响：** 高 🟠

---

## 中等问题

### 6. `_baseDamage = 15` 硬编码
- **文件：** `src/engine/character.js:178-180`
- **问题：** 所有角色 `_baseDamage = 15`，无视 CSV 或 system.csv 配置。`system.csv` 有 `playerBaseDamage` 但被覆盖。
- **影响：** 中 🟡

### 7. `attackRange` 回退值分散
- **文件：** `player.js` 多处（332, 479, 498, 532, 690, 757, 1175）
- **问题：** 各方法回退值不同（60/80/320），掩盖数据错误
- **影响：** 中 🟡

### 8. `bulletRange` 回退值不一致
- **文件：** `player.js` 各 `_fire*` 方法
- **问题：** 大多回退 300，`_fireSpray` 回退 320
- **影响：** 低（数据完整时不会被触发）

---

## 轻微问题

### 9. `materialGain` 在 statFields 中但不在 CSV schema 中
- **文件：** `character.js:129` vs `csv2json.cjs:252-284`
- **影响：** 无（仍可通过物品/升级/羁绊修改）

### 10. `bulletCount/Pierce/Speed` 在 statFields 中但不在 CSV schema 中
- **文件：** `character.js:131` vs schema
- **影响：** 无（仅物品/升级用）

---

## 正常的（已确认工作正常）

| 项目 | 状态 | 说明 |
|------|------|------|
| 被动技能 | ✅ | 18 个角色独特被动通过 PassiveSystem 执行 |
| `preferredClasses` / `_2` | ✅ | 影响伤害倍率 + 商店权重 |
| 标签系统 | ✅ | 标签匹配/不匹配惩罚生效 |
| 基础属性 | ✅ | `maxHp`/`speed`/`armor`/`dodge` 等从 CSV 正确流入 |
| 解锁条件 | ✅ | `unlockType`/`unlockValue` 正常工作 |
| 武器 38 种 | ✅ | 8 轴差异化（伤害/冷却/范围/弹速/穿透/弹数/行为/标签） |
| 10 种武器行为 | ✅ | bullet/spread/sweep/thrust/explode/frost/shock/homing/spray/heal |
| class 差异 | ✅ | 主类×细分类 + 商店加权 + formula 倍率 |
