# Cyber Blade 常见问题解决 (FAQ)

> 记录项目开发中反复遇到的问题、根因、修复方式。
> 适用读者: 维护 / 重构 / 加新功能时的自己或协作者。
>
> 最后更新: 2026-06-09

---

## 目录

- [1. 浏览器缓存导致改动不生效 — 用 `?v=` 强制刷新](#1-浏览器缓存导致改动不生效--用-v-强制刷新)
- [2. 浏览器 `<script>` 不支持 `import` / `export`](#2-浏览器-script-不支持-import--export)
- [3. Animator 双环境兼容模式 (globalThis)](#3-animator-双环境兼容模式-globalthis)
- [4. 测试基线 416 passed / 15 failed](#4-测试基线-416-passed--15-failed)
- [5. 武器详情 Modal 点击无反应](#5-武器详情-modal-点击无反应)
- [6. ESC 暂停 / 中止界面](#6-esc-暂停--中止界面)
- [7. 攻击距离公式 (Brotato 风格加法)](#7-攻击距离公式-brotato-风格加法)
- [8. 调试速查表 (症状 → 根因)](#8-调试速查表-症状--根因)
- [9. 新增模块的接入清单](#9-新增模块的接入清单)

---

## 1. 浏览器缓存导致改动不生效 — 用 `?v=` 强制刷新

### 问题
改完 JS / CSS 后浏览器看到的还是**旧版本**, 出现各种诡异报错:
- `Identifier '_Animator' has already been declared` (旧版 `import` + 新版 `const _Animator` 同时执行)
- `Unexpected token 'export'` (旧版有 `export` 语句)
- 渲染错误但代码看上去对

### 根因
`<script src="x.js">` 和 `<link href="x.css">` 默认走 HTTP 缓存, 浏览器不会重新拉取, 即使服务器端文件已变。

### 解决: 缓存破坏 (Cache Busting)
`index.html` 中所有 `src` / `href` 末尾加 `?v=<版本号>`, 文件改动后**手动递增**版本号:

```html
<!-- 缓存破坏: 修改任意 JS/CSS 后, 必须把 ?v= 后面的版本号递增 (yyyyMMddHHmm) -->
<link rel="stylesheet" href="style.css?v=20260606">

<script src="src/engine/save.js?v=20260606"></script>
<script src="src/engine/time.js?v=20260606"></script>
...
```

### 维护规则
- 格式: `yyyyMMdd` 或 `yyyyMMddHHmm` (精确到分钟)
- **任何** JS / CSS 文件**实质改动** → 必须递增 `?v=` 后的版本号
- 一次性批量替换脚本 (PowerShell):
  ```powershell
  $p = "index.html"
  $c = Get-Content -LiteralPath $p -Raw -Encoding utf8
$c = $c -replace '<script src="([^"?]+)\.js"></script>', '<script src="$1.js?v=2026060913"></script>'
  Set-Content -LiteralPath $p -Value $c -Encoding utf8 -NoNewline
  ```
- HTML 注释中包裹的 script (如 `<!-- <script ...> -->`) **不**需要加 `?v=`, 但替换脚本会一并加上, 改完后手动还原即可
- HTML 顶部的 `<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">` 等 meta 标签**不能**取代 `?v=`, 只对 HTML 自身生效, 对引用的子资源没用

### 用户硬刷新技巧
- 普通刷新不够, 要 **Ctrl+F5** (强制不走缓存)
- 或 DevTools → Network → 勾 "Disable cache"

---

## 2. 浏览器 `<script>` 不支持 `import` / `export`

### 问题
- `Uncaught SyntaxError: Unexpected token 'export'`
- `Uncaught SyntaxError: Unexpected token 'import'`

### 根因
`index.html` 用的是普通 `<script src="x.js">`, 不是 `<script type="module">`. 普通 `<script>` 是**经典脚本**, 顶层不能有 `import` / `export` 语句.

ES module 才支持:
```html
<script type="module" src="x.js"></script>
```

但项目里其他文件 (character.js, enemy.js 等) 都用全局 `var` / `const X = {...}` 模式, **改成 `type="module"` 会大面积破坏** (this 变 undefined, window 作用域丢失等).

### 解决
**所有 JS 模块保持全局 `const` 模式**, 通过 `globalThis` 共享:
```js
// 顶部
const Animator = (typeof globalThis !== 'undefined' && globalThis.Animator) || null;
```

跨文件访问:
```js
// 暴露方 (animator.js 末尾)
if (typeof globalThis !== 'undefined') {
    globalThis.Animator = Animator;
    if (typeof window !== 'undefined') window.Animator = Animator;
    if (typeof global !== 'undefined' && global !== window) global.Animator = Animator;
}

// 严禁添加 `export { Animator };` — 浏览器 <script> 加载会立即抛 SyntaxError
```

### 检查清单
- ✅ `import { X } from '...'` — **禁用**
- ✅ `export { X };` — **禁用**
- ✅ `const X = globalThis.X || null;` — **正确**
- ✅ `globalThis.X = X;` (暴露方) — **正确**
- vitest 测试需要 X 时, 在测试 setup 或受测代码顶部**显式 import** (Node ESM 模式)

---

## 3. Animator 双环境兼容模式 (globalThis)

### 问题
`Animator is not defined` 在 vitest 测试中, 但在浏览器中正常 (或反过来)。

### 根因
- **浏览器** `<script>` 顺序加载, 后加载的文件用 `typeof Animator !== 'undefined'` 检测前一个文件设的 `window.Animator`
- **vitest** 用 ESM 模式, 每个文件独立作用域, `Animator` 标识符**完全没定义** (但 `globalThis.Animator` 可能被其他文件设过)

### 正确模式
```js
// === animator.js (暴露方) ===
const Animator = { ... };

if (typeof globalThis !== 'undefined') {
    globalThis.Animator = Animator;
    if (typeof window !== 'undefined') window.Animator = Animator;
    if (typeof global !== 'undefined' && global !== window) global.Animator = Animator;
}

// === 消费方 (e.g. enemy.js / player.js / renderer.js) ===
const _Animator = (typeof globalThis !== 'undefined' && globalThis.Animator) || null;

// 使用: null 兜底跳过
if (_Animator && e.animator) {
    _Animator.update(e.animator, dt);
}
```

### 关键点
- `_Animator` 在消费方**模块顶层**求值, 后续使用同一个引用
- 不用 `typeof Animator !== 'undefined'`, 因为 ESM 严格模式 + 未 import 时会抛 ReferenceError
- 渲染层 (renderer.js) 因为在 player/enemy 之后加载, `_Animator` 通常有值, 但仍需 null 兜底 (单元测试环境没有)

---

## 4. 测试基线 465 passed / 0 failed

### 基线数据
```
Test Files  16 passed (16)
Tests       465 passed (465)
```

### 关键约束
- **任何**改动不能让 465 passed 减少
- 跑测试: `npm test`
- 跑单个: `npm test -- test/unit/enemy.test.js -t E3`

### 修复时常见破坏点
1. **顶层语法错** → 整个 test file suite-failed, 51+ 测试瞬间消失
   - 检查: `node --check src/engine/enemy.js` (所有改过的文件)
   - 症状: `Failed to parse source for import analysis` (vite)
2. **新模块没加载** → 测试运行时 `X is not defined`
   - 解决: 按"消费方"模式 `const _X = globalThis.X || null;`
3. **`import` 残留** → 浏览器 + Node 都会抛 SyntaxError
   - 解决: 全部改用 globalThis 模式

---

## 5. 武器详情 Modal 点击无反应

### 问题
商店装备区每个武器槽右下角有 `▾` 小三角按钮, 点击**没任何反应**.

### 根因
HTML 中**整个 `weaponDetailModal` overlay 元素缺失**!

`src/cyberblade/ui.js:1073-1174` 的 `_showWeaponDetailModal` 函数引用以下 DOM:
- `#weaponDetailModal` (overlay 容器)
- `#wdIcon / wdName / wdLevel / wdQuality / wdStats / wdSpecial / wdBtnSell / wdBtnMerge / wdBtnCancel / wdClose`

这些 ID 在 `index.html` 中**一个都没有**, 函数调用 `document.getElementById(...)` 返回 `null`, 然后访问 `.classList.remove('hidden')` → 抛 `TypeError: Cannot read properties of null`. 因为 `e.stopPropagation()` 已经在按钮 handler 里, 错误被吞掉 (handler 是 async 路径, 浏览器 console 才看得到).

### 解决
在 `index.html` 中, 任意位置 (推荐在 `levelUpOverlay` 后面) 加:
```html
<!-- 武器详情 Modal (点击装备区 ▾ 三角触发) -->
<div id="weaponDetailModal" class="overlay hidden">
    <div class="weapon-detail-content">
        <div class="wd-header">
            <div id="wdIcon" class="wd-icon"></div>
            <div class="wd-header-text">
                <div id="wdName" class="wd-name"></div>
                <div class="wd-meta">
                    <span id="wdQuality" class="wd-quality"></span>
                    <span id="wdLevel" class="wd-level"></span>
                </div>
            </div>
            <button id="wdClose" class="wd-close" title="关闭">×</button>
        </div>
        <div id="wdStats" class="wd-stats"></div>
        <div id="wdSpecial" class="wd-special"></div>
        <div class="wd-actions">
            <button id="wdBtnSell" class="wd-btn wd-btn-sell">💰 卖出</button>
            <button id="wdBtnMerge" class="wd-btn wd-btn-merge">🔗 合并</button>
            <button id="wdBtnCancel" class="wd-btn wd-btn-cancel">取消</button>
        </div>
    </div>
</div>
```

CSS 样式在 `style.css:1962-2120` 已就绪 (`.weapon-detail-content` / `.wd-*`).

### 调试技巧
- 浏览器 F12 → Console, 看点击 ▾ 后是否有 `TypeError: Cannot read properties of null`
- Console 报错说明 DOM 缺失; 报错位置在 `ui.js:1173` (`modal.classList.remove('hidden')`) 或 line 1086-1144 (各种 getElementById 之后)

---

## 6. ESC 暂停 / 中止界面

### 功能
- 战斗中按 `ESC` → 暂停, 显示中止界面
- 界面 3 按钮: ▶ 继续游戏 / 🔄 新开游戏 / 🚪 退出游戏
- 中止界面按 `ESC` → 继续

### 涉及文件
- `index.html`: `pauseOverlay` (含 3 按钮)
- `style.css:2487-2532`: `.pause-content` (黄色调主题)
- `src/engine/engine.js:78-82`: state 加 `'paused'` 分支 (跳过 update, 渲染继续)
- `src/cyberblade/main.js`: `GameEngine.pauseGame / resumeGame / newGameFromPause / exitGame / togglePause` (含 BGM pause/resume)
- `src/cyberblade/ui.js`:
  - `init()` 加 ESC keydown + 3 按钮事件
  - `showPause() / hidePause()` 新增
  - `showMenu()` 加 `pauseOverlay.classList.add('hidden')`

### 状态机扩展
`GameEngine.state` 现有值: `menu / playing / shopping / levelup / gameover / loot / paused`

**新加模块如果也有"暂停场景"**: 也加 `'paused'` 分支, 但**别**用 `state === 'playing'` 之外的判断 (避免 bug).

---

## 7. 攻击距离公式 (Brotato 风格加法)

### 设计
```js
// 武器 + 角色 (加法, 不是乘法)
const weaponRange = (wp.attackRange || 60) + (player.attackRange || 0);
```

### Brotato 平衡
范围越大, 冷却越长 (200 像素 ≈ +100% cd):
```js
let cd = FormulaSystem.calcWeaponCooldown(rawDef, p, lv);
if (p.attackRange) cd *= 1 + Math.max(0, p.attackRange) / 200;
```

### 角色 attackRange 数据
11 角色 (Brotato 风味 ±50~150):
| 角色 | attackRange |
|------|-------------|
| swordsman | +50 |
| gunslinger | +120 |
| fire_mage | +100 |
| archer | +150 |
| mech | -30 |
| assassin | -20 |
| medic | 0 |
| paladin | +30 |
| engineer | +60 |
| berserker | -50 |
| dragon_knight | +80 |

### 同步位置 (3 处必须一致)
- `csv/characters.csv` (源)
- `src/data/characters.json` (中间产物)
- `src/data/data-bundle.js` (内嵌, 浏览器用)

修改流程:
1. 改 `csv/characters.csv`
2. 跑 `node scripts/csv2json.cjs` 生成 JSON
3. 跑 `node scripts/generate-data-bundle.js` 生成 bundle
4. 验证 3 处一致

### Cap 范围
`src/engine/stats.js:69`: `attackRange` cap 0 ~ 500
`src/engine/stats.js:371`: 升级时 +15 像素

---

## 8. 调试速查表 (症状 → 根因)

| 症状 | 可能根因 | 验证方法 |
|------|----------|----------|
| `Unexpected token 'export'` | 浏览器 `<script>` 不支持 export | 搜 `^export `, 改用 `globalThis.X = X;` |
| `Unexpected token 'import'` | 同上, 用 `<script>` 加载 | 搜 `^import `, 改用 `globalThis` 模式 |
| `X is not defined` (浏览器) | X 模块没在 `<script>` 列表里 | 检查 `index.html` 是否加载 X |
| `X is not defined` (vitest) | 测试没显式 import X, 顶层 `const X = ...` 也没值 | 改用 `globalThis.X \|\| null` 模式 |
| `Identifier 'X' has already been declared` | 浏览器加载了**新旧两个版本** (缓存) | 强制刷新 (Ctrl+F5) + `?v=` 版本号递增 |
| `Renderer is not defined` (engine.js 调用) | renderer.js 语法错, 顶层未执行 | `node --check src/engine/renderer.js` |
| 点击按钮无反应, console 有 TypeError | 按钮 handler 调用的 DOM 元素缺失 | 看 console 报哪个 ID null, 补 HTML |
| `Failed to parse source for import analysis` | 文件顶层语法错 (多打 `}` 之类) | `node --check` 验, 报错位置可能不准, 看最后 10 行 |
| 怪停下后不攻击 / 怪不扣血 | `_touchDist` 缓冲太大 (修: 30→15) | 搜 `_touchDist` |
| 武器双重扣血 | 攻击逻辑在 2 处都扣血 (修: `_fireMeleeSweep/Thrust` 改纯特效, 唯一伤害源 `_tickMeleeHitDetection`) | 搜 `_tickMeleeHitDetection` |
| 远程武器像近战一样刺出 | renderer 远程分支没设 `drawDist = dist` | 改 `src/engine/renderer.js:441-449` |
| ESC 暂停不生效 | ESC 监听没加 / `GameEngine.togglePause` 没实现 | 看 `ui.js init` keydown + `main.js` togglePause |
| 暂停时背景还在动 | engine.js loop state 漏 `'paused'` 分支 | `src/engine/engine.js:78-82` 加注释 |

---

## 9. 新增模块的接入清单

> 新建一个 JS 模块 (如 `src/engine/foo.js`) 并在主游戏中使用时, 按此清单检查, 避免漏。

### 浏览器接入 (硬性)
- [ ] `index.html` 在合适位置加 `<script src="src/engine/foo.js?v=20260606"></script>` (注意加 `?v=`)
- [ ] 顺序: 依赖项**之前**加载
- [ ] 顶部声明: `const Foo = (typeof globalThis !== 'undefined' && globalThis.Foo) || null;` (消费方)
- [ ] 暴露方末尾:
  ```js
  if (typeof globalThis !== 'undefined') {
      globalThis.Foo = Foo;
      if (typeof window !== 'undefined') window.Foo = Foo;
  }
  ```
- [ ] **不要**加 `import` / `export` 语句 (浏览器 `<script>` 不支持)
- [ ] HTML 顶部加 `?v=` 缓存破坏版本号

### vitest 接入 (硬性)
- [ ] `vitest.config.js` 不需要改 (默认 ESM)
- [ ] 测试 `import { Foo } from 'src/engine/foo.js';` (Node 22+ + Vitest 支持)
- [ ] 测试运行前**无**需在 html 加载, ESM 模式自动 import

### 测试基线
- [ ] `npm test` → 必须是 **465 passed / 0 failed**, 不能少
- [ ] 跑单个验: `npm test -- test/unit/foo.test.js`
- [ ] 新增测试时**不**计入"15 failed 基线", 是新加的通过测试

### 改动 JS / CSS 后 (硬性)
- [ ] `?v=` 版本号递增 (yyyyMMdd)
- [ ] `node --check src/.../foo.js` 过
- [ ] 浏览器 Ctrl+F5 硬刷新

### 文档
- [ ] 如果是新功能 / 修了重要 bug → 在 `docs/cyberBlade项目解决.md` 追加一条
- [ ] 复杂的模式 / 协议 → 写进本 FAQ

---

## 10. 源码文件中文注释乱码

### 问题
在编辑器中打开 `enemy.js` / `wave.js` 等文件，看到中文变成 `�` (U+FFFD) 或乱码如 `绯荤粺`（即 mojibake，UTF-8 双编码错误）。

### 根因
两种不同的编码损坏：

| 症状 | 原因 | 示例 |
|------|------|------|
| `�` (U+FFFD) | 文件被非 UTF-8 编码保存，多字节字符无法映射，被替换为 U+FFFD | `敌人 AI 系统` → `敌人 AI 系统�` |
| mojibake | UTF-8 字节被错误地按 Latin-1/Windows-1252 解码，再重新保存为 UTF-8（双编码） | `波次系统` → `æ³¢æ¬¡ç³»ç»Ÿ` |

### 如何判断
```bash
# 查找 U+FFFD（替换字符）— 用二进制扫描
# PowerShell
$bytes = [System.IO.File]::ReadAllBytes("src/engine/enemy.js")
$count = 0
for ($i = 0; $i -lt $bytes.Count - 2; $i++) {
    if ($bytes[$i] -eq 0xEF -and $bytes[$i+1] -eq 0xBF -and $bytes[$i+2] -eq 0xBD) { $count++ }
}
"U+FFFD count: $count"
```

### 修复方法

#### U+FFFD 修复（enemy.js 示例）
只能**手动逐行恢复**：
1. 读取文件，定位 `�` 位置
2. 根据上下文推测原文（注释多为中文描述）
3. 用 `edit` 工具逐行替换为正确中文
4. 验证: `node --check src/engine/enemy.js`

#### Mojibake 修复（wave.js 示例）
最安全方案: **`git checkout -- src/engine/wave.js`** 从 git 恢复原始版本。

若文件不在版本控制中，可用以下 PowerShell 尝试解码还原：
```powershell
$bytes = [System.IO.File]::ReadAllBytes("x.js")
$wrong = [System.Text.Encoding]::UTF8.GetString($bytes)
$fixed = [System.Text.Encoding]::UTF8.GetString(
    [System.Text.Encoding]::GetEncoding(1252).GetBytes($wrong)
)
Set-Content -Path "x.js" -Value $fixed -Encoding UTF8
```
⚠ **注意**: 此方案可能损坏 ASCII 之外的字符（如 `—`、`±` 等符号），建议仅在纯中文 + ASCII 文件上使用。

### 预防
- 编辑器始终设定为 **UTF-8 无 BOM** 保存
- git 配置 `git config --global core.autocrlf true` 配合 `.gitattributes` 中 `*.js text=auto`
- 团队约定: 禁止 GBK/GB2312 编码提交
- 每次 `git diff` 留意非 ASCII 文件是否出现意外变更

---

## 11. 敌人速度异常快（spdMult 系数 BUG）

### 问题
Wave 1 的基础敌人（basic）速度 80，但游戏中感觉比角色快很多。
数值上：Wave 1 basic 敌 = 168 px/s，枪手 = 110 px/s，**怪快 53%**。

### 根因
`enemy.js:484` 的速度缩放公式：
```js
// BUG: spdMultFactor=2 导致整个式子翻倍
const spdMult = (1 + level * spdScale) * spdMultFactor;
//       Wave 1: (1 + 1*0.05) * 2 = 2.10 → basic 速度 80*2.1 = 168
```

对比 HP 和伤害的公式（无此问题）：
```js
const hpMult  = 1 + level * 0.15;   // Wave 1: 1.15  ✓
const dmgMult = 1 + level * 0.15;   // Wave 1: 1.15  ✓
// 速度却额外乘了 spdMultFactor=2 → Wave 1: 2.10  ✗
```

CSV 定义 (`csv/system.csv:38`)：
```
spdMult,2,number,敌人速度缩放翻倍系数,difficulty
```

### 修复
`enemy.js:484` 改为：
```js
// FIX: spdMultFactor 仅放大每波增量，不翻倍底数
const spdMult = 1 + level * spdScale * spdMultFactor;
//       Wave 1: 1 + 1*0.05*2 = 1.10 → basic 速度 80*1.1 = 88
//       Wave 5: 1 + 5*0.05*2 = 1.50 → basic 速度 80*1.5 = 120（刚超枪手 110）
//       Wave 20: 1 + 20*0.05*2 = 3.00 → basic 速度 240（后期碾压）
```

### 修复后效果对比
| 波次 | 旧 basic 速度 | 新 basic 速度 | 枪手(110) | 感觉 |
|------|---------------|---------------|-----------|------|
| W1 | 168 (53% > 枪手) | 88 (20% < 枪手) | 有余裕风筝 | ✅ |
| W5 | 200 (82% > 枪手) | 120 (9% > 枪手) | 略慢但能打 | ⚠️ |
| W10 | 240 (118% > 枪手) | 160 (45% > 枪手) | 必须靠技能 | ✅ |
| W20 | 320 (190% > 枪手) | 240 (118% > 枪手) | 跑不过 | ✅ 后期应有压迫感 |

### 相关文件
- `csv/system.csv:37-38`: `spdScale=0.05` + `spdMult=2`（值不变，公式修复）
- `src/engine/enemy.js:484`: 公式修改处

---

## 附录: 项目结构速查

```
buffPrj1/
├── index.html                 # 主入口, 所有 <script> + <link> 在这里
├── style.css                  # 唯一 CSS
├── csv/                       # 数据源 (csv)
├── src/
│   ├── data/                  # 生成的 JSON + 内嵌 bundle
│   ├── engine/                # 通用引擎 (player/enemy/renderer 都在这)
│   │   ├── animator.js        # 通用动画状态机 (idle/attack/death)
│   │   ├── engine.js          # 主循环 + 状态机
│   │   ├── renderer.js        # Canvas 2D 渲染
│   │   └── ...
│   └── cyberblade/            # 赛博土豆专用
│       ├── main.js            # 启动 / 暂停 / 状态流转
│       ├── player.js          # 玩家系统
│       └── ui.js              # UI 渲染 + 事件
├── test/unit/                 # vitest 测试
└── docs/                      # 文档 (本 FAQ 在这)
```

### 关键文件改动影响范围
- `engine.js` state 改动 → 所有系统 (player/enemy/...) 都要适配
- `data-bundle.js` 改动 → 必须同步 csv + json (3 处一致)
- `index.html` script 顺序 → 严格按依赖关系
- `style.css` 大改 → 注意测试是否依赖 class 名

---

## 附录: 常用命令

```bash
# 跑所有测试
npm test

# 跑单个测试
npm test -- test/unit/enemy.test.js
npm test -- test/unit/enemy.test.js -t E3

# 单文件语法检查
node --check src/engine/foo.js

# 数据重新生成 (csv → json → bundle)
node scripts/csv2json.cjs
node scripts/generate-data-bundle.js

# 批量加 ?v= 版本号 (PowerShell)
$p = "index.html"
$c = Get-Content -LiteralPath $p -Raw -Encoding utf8
$c = $c -replace '<script src="([^"?]+)\.js"></script>', '<script src="$1.js?v=20260606"></script>'
Set-Content -LiteralPath $p -Value $c -Encoding utf8 -NoNewline
```
