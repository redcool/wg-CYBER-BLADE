# Project knowledge

This file gives Codebuff context about your project: goals, commands, conventions, and gotchas.

## Quickstart
- Setup:
- Dev:
- Test:

## Architecture
- Key directories:
- Data flow:

## Conventions
- Formatting/linting:
- Patterns to follow:
- Things to avoid:

## Combat System Design

The following is the persistent design document for the combat system. Refer to `战斗系统策划文档.md` for the full original.

### Core Combat Loop
```
每帧循环:
  1. 玩家移动 (WASD + facingAngle 更新)
  2. 每个武器独立检查:
     a. 冷却就绪? (cooldownTimer <= 0)
     b. 范围内有敌人? (近战用 meleeRange, 远程用 attackRange)
     c. ✅ → 前方向对准目标 → 开火
  3. 子弹飞行 + 碰撞检测
  4. 敌人 AI 更新
  5. 拾取/材料/宝箱检测
```

#### Direction System
- **forward**: 0 rad（正右方）— 所有武器图标的默认朝向
- **facingAngle**: `atan2(dy, dx)` — 玩家朝向，由 WASD 移动方向决定
- **attackTargetAngle**: `atan2(target.y - p.y, target.x - p.x)` — 开火时瞄准目标的方向
- **orbitalAngle**: `(i/count) * 2π - π/2` — 第 i 个武器在 360° 轨道上的角度

Behavior rules:
- 移动时：`facingAngle` 跟随 WASD 方向
- 攻击时（无论是否移动）：`facingAngle` 覆盖为攻击目标方向（角色面朝敌人）
- 未移动且未攻击：保持上一次的 `facingAngle` 值
- 武器图标默认朝外（沿 orbitalAngle 方向）
- 攻击时：武器图标朝目标方向旋转
- 角色 PNG 默认朝右，向左时水平翻转 (scaleX = -1)

### Weapon System

#### Weapon Properties
```
{
  id: string,          // 唯一标识
  name: string,        // 显示名称
  tag: string,         // 标签 (melee/gun/bow/magic/medic)
  behavior: string,    // 行为模式
  slots: number,       // 占位格数 (1~3)
  damageMult: number,  // 伤害倍率
  attackSpeedMult: number, // 攻速倍率
  bulletSpeed: number, // 弹速
  bulletCount: number, // 弹数
  pierce: number,      // 穿透次数
  spread: number,      // 散射弧度
  meleeRange: number,  // 近战范围
  attackRange: number, // 远程射程
}
```

#### Level & Quality Scaling
```
等级加成: damageMult *= 1 + (level - 1) * 0.25
品质加成: T1=1.0, T2=1.15, T3=1.35
最终伤害 = 玩家基础伤害 × damageMult × 品质加成 × 等级加成
```

#### Weapon Behaviors
| behavior | Description |
|----------|-------------|
| `bullet` | 标准子弹，直线飞行 |
| `spread` | 散射，多弹体扇形分布 |
| `laser` | 快速直线，3发微扩散 |
| `shock` | 电击，穿透+连锁弹跳 |
| `melee_sweep` | **近战横扫** — 180° 扇形范围，直接命中检测 |
| `melee_thrust` | **近战突刺** — 直线穿透，窄扇形命中检测 |
| `explode` | 爆炸弹，命中后范围伤害 |
| `frost` | 冰霜，减速+冰爆 |
| `homing` | 跟踪弹，自动追踪最近敌人 |
| `spray` | 喷射，锥形多弹体（火焰/毒/冷气） |
| `heal_bullet` | 治愈弹，命中回血 |
| `shield_aura` | 圣光盾，光环治疗 |

#### Melee: Dynamic Sweep/Thrust Selection
```
targetDist < meleeRange * 0.45  →  melee_sweep（近距离横扫）
targetDist >= meleeRange * 0.45 →  melee_thrust（中远距离突刺）
```
- **Sweep**: 180° 扇形，范围全额伤害，弧形火花轨迹
- **Thrust**: 直线~30px宽，pierce次穿透（默认3），直接伤害检测（不生成子弹对象），命中火花特效

#### Cooldown System
- 每个武器拥有独立冷却 `cooldownTimer`
- 多个武器独立循环检查冷却
- 每个武器各自检查自身射程内的敌人
- 冷却未到、或范围内无敌人 → 跳过此武器
- 不共享全局攻击计时器

#### Weapon Orbit Distribution
```
360° 均匀环绕，从正上方(-π/2)开始:
angle = (i / count) × 2π - π/2

轨道距离:
iconSize = max(18, round(玩家半径 × 1.0 + slots × 5))
dist = 玩家半径 + 6 + iconSize × 0.55

最大 6 个武器。
```

### Damage System

#### Damage Calculation
```
基础伤害 = 玩家 damage × 武器 damageMult × 品质加成 × 等级加成
暴击判定: random < critChance
暴击伤害: 基础伤害 × critMultiplier
最终伤害 = StatsSystem.calcDamageReduction(伤害, 护甲)
```

#### Damage Types
- **物理**: 直接扣血
- **燃烧 (burn)**: DOT，每秒 dps 伤害，最多 burnMaxStacks 层
- **冰冻 (slow)**: 减速，slowFactor 持续 slowDuration 秒
- **爆炸 (splash)**: 范围伤害，边缘衰减50%
- **连锁 (chain)**: 弹跳至附近敌人，每跳伤害衰减20%
- **跟踪 (homing)**: 自动修正弹道追踪敌人

#### Kill Processing Chain
```
敌人 hp <= 0
    ↓
1. kills++（统计）
2. addXP(e.xpValue) → 可能触发升级
3. lifeSteal 吸血处理
4. _dropMaterials(e) → 掉落金币
5. 精英 → ChestSystem.spawnChest(x, y, tier=1)
   Boss  → ChestSystem.spawnChest(x, y, tier=2)
6. ParticleSystem.enemyDeath() → 死亡特效
```

### Chest System
| Source | Tier | Description |
|--------|------|-------------|
| Elite kill | 1 | ~20-40 gold value rewards |
| Boss kill | 2 | ~50-80 gold value + boss-exclusive rewards |

**Pickup Flow:** 战斗期间自动拾取 → `pendingChests` 队列 → 关卡结束后逐个展示奖励选择弹窗（3个随机选项）→ 检查升级溢出 → 商店

### Enemy Spawn Rules
- **Type unlock**: basic(L1), fast(L2), tank(L4), ranged(L6), elite(L10), boss(L15+)
- **Simultaneous limits**: elite max 1, boss max 1
- **Difficulty scaling**: `difficultyScale = 1 + (level-1) × 0.15`, `spawnRate = max(0.4, 1.5 - (level-1) × 0.04)`, `enemyCount = 4 + floor(level × 1.5)`
- **Boss**: 每5关第4秒生成（5~10关精英，15关+Boss）

### Rendering
- Weapons: default facing right (0 rad), orbit outward, thrust flies forward, sweep arcs 180°
- Character sprite: default facing right, flip horizontally when facing left
- Icons: PNGs auto-clean background (dark/light detection via corner sampling)

### Melee Weapon Speed Tiers (v1.1)

近战武器按 `attackSpeedMult` 分为 5 个梯度，极差约 **7.2 倍**（最快 0.26s → 最慢 1.87s/击）：

| Tier | attackSpeedMult | Weapons | Effective CD | Atk/s |
|------|---------------|---------|-------------|-------|
| ⚡极速 | 0.15~0.35 | 利爪 (0.30) | 0.26s | 3.8 |
| ⚡快速 | 0.36~0.50 | 匕首 (0.38), 等离子刀 (0.50) | 0.35~0.50s | 2.0~2.9 |
| 🔄中等 | 0.51~0.70 | 链锯剑 (0.55), 能量剑 (0.60), 武士刀 (0.70) | 0.55~0.70s | 1.4~1.8 |
| 🔨慢速 | 0.71~1.00 | 矛 (0.85), 斧 (1.00) | 0.94~1.18s | 0.85~1.1 |
| 🐢极慢 | 1.01~1.40 | 鞭 (1.25), 锤 (1.40) | 1.25~1.87s | 0.54~0.80 |

Formula: `cd = (1.0 / player.attackSpeed) × attackSpeedMult`. Player attackSpeed is also modified by weapon `mods.attackSpeedMult` (e.g., hammer -25%).

### Attack Animation Durations
| Type | Duration | Description |
|------|----------|-------------|
| melee_sweep | 350ms | 180° arc |
| melee_thrust | 250ms | fly-out & return |
| spray | 150ms | cone spread |
| default | 200ms | muzzle flash |

#### Crate Targeting
- 无敌人范围时，自动瞄准最近的可击破医药箱
- 远程武器：攻击范围 = attackRange (默认300)
- 近战武器：攻击范围 = meleeRange + 箱体半径 (约18px)
- `_fireMeleeSweep` 和 `_fireMeleeThrust` 均内置医药箱碰撞检测

### Data Flow (per frame)
```
PlayerSystem.update(dt)
  - 自动瞄准：敌人优先 → 无敌人时→医药箱
  - 每个武器独立冷却+独立搜索目标
  → BulletSystem.update(dt)
  → GameEngine._checkBulletCollisions() → EnemySystem.update(dt)
  → GameEngine._checkMedkitCollisions() → 子弹击破医药箱
  → MedkitSystem.update() → 玩家拾取医疗包
  → ChestSystem/MedkitSystem pickup → WaveSystem.update(dt)
  → UISystem.updateHUD()
```

#### Medkit Crate System
- **生成**: 每关开始 2~3 个，随机散布在地图内
- **击破方式**: 玩家自动瞄准攻击（无敌人时）、近战横扫/突刺均能命中
- **HP**: 30~50，受击显示绿色火花粒子
- **掉落**: 击破后掉落 1~2 个医疗包 (+15~25 HP)，8秒后自动消失
- **拾取**: 玩家靠近自动拾取 (pickupRange + 8px)，显示绿色十字+补血粒子
