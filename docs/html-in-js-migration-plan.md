# HTML-in-JS 迁移计划

## 问题

`ui.js` ~2200 行中，大量 HTML 结构以模板字符串形式嵌入 JS：

```js
el.innerHTML = `<div class="xxx">
    <span>${data}</span>
    ${cond ? '<div>...</div>' : ''}
</div>`;
```

### 痛点

- **维护困难**：改布局要在 JS 字符串里搜，改错引号就崩
- **低可读性**：条件分支和模板字符串混在一起，结构不直观
- **无工具支持**：IDE 没有语法高亮、自动补全，CSS 选择器无法定位
- **高耦合**：展示层和数据逻辑在同一处，改 UI 要懂 JS，改 JS 要懂 UI
- **难测试**：无法单独验证 HTML 结构

## 目标

将 JS 中的 HTML 模板字符串全部迁移为 `<template>` 元素模式，实现：

- HTML 结构放在 `index.html` 的 `<template>` 中
- JS 只负责 clone 模板 + 注入数据 + 控制显隐
- 布局修改只需改 HTML，不碰 JS

## 方案：`<template>` + `data-key` 注入

```html
<!-- index.html -->
<template id="tpl-dmg-breakdown">
  <div class="wd-dmg-breakdown">
    <div class="wd-dmg-breakdown-title">📐 伤害计算</div>
    <div class="wd-dmg-breakdown-row">
      <span>武器基础</span>
      <span class="dmg" data-key="baseDmg"></span>
    </div>
    <div class="wd-dmg-breakdown-row" data-if="flatDmg" style="display:none">
      <span>角色加成</span>
      <span class="dmg" data-key="flatDmgVal"></span>
    </div>
    <!-- ... -->
  </div>
</template>
```

```js
// ui.js — 只做数据注入
_renderDamageBreakdown(def, player, level) {
  const tpl = document.getElementById('tpl-dmg-breakdown');
  const el = tpl.content.cloneNode(true);

  el.querySelector('[data-key="baseDmg"]').textContent = val;
  if (flatDmg <= 0) el.querySelector('[data-if="flatDmg"]').remove();

  target.insertAdjacentElement('afterend', el);
}
```

### 条件显隐约定

| 属性 | 含义 |
|------|------|
| `data-if="key"` | JS 中根据条件决定保留或删除 |
| `data-key="key"` | JS 中填入文本 |
| `data-class="cond"` | JS 中根据条件添加/移除 CSS 类 |
| `data-attr-*` | JS 中注入属性值 |

## 迁移范围

`ui.js` 中约 **20 处** HTML 模板字符串需要迁移，按复杂度分三阶段：

### Phase 1 — 独立面板（低风险，可逐个验证）

| # | 位置 | 模板 | 复杂度 |
|---|------|------|--------|
| 1 | 伤害细分面板 `_renderDamageBreakdown` | ~15 行 HTML | ⭐ |
| 2 | 职业适配面板 `_showWeaponFitPopup` specialHtml | ~15 行 HTML | ⭐ |
| 3 | 商店武器详情 `_showWeaponDetailModal` statsRows | ~20 行 HTML | ⭐ |
| 4 | 羁绊加成面板 `wdSynergy` innerHTML | ~12 行 HTML | ⭐ |

### Phase 2 — 核心面板（中风险，需配合测试）

| # | 位置 | 模板 | 复杂度 |
|---|------|------|--------|
| 5 | 武器详情面板 `_showWeaponDetail` | ~60 行 HTML | ⭐⭐ |
| 6 | 角色详情面板 `_showCharDetail` (解锁) | ~50 行 HTML | ⭐⭐ |
| 7 | 商店卡片 `_renderShopItems` | ~40 行 HTML | ⭐⭐ |
| 8 | 物品列表 `_renderItems` | ~40 行 HTML | ⭐⭐ |
| 9 | 库存列表 `_renderOwnedItems` + badges | ~30 行 HTML | ⭐⭐ |
| 10 | 商店结算展示 | ~30 行 HTML | ⭐⭐ |

### Phase 3 — 次要面板（低风险，可随时做）

| # | 位置 | 模板 | 复杂度 |
|---|------|------|--------|
| 11 | 武器选择卡片 `_renderWeaponGrid` | ~5 行 | ⭐ |
| 12 | 解锁展示卡片 | ~5 行 | ⭐ |
| 13 | 商店空状态 | ~2 行 | ⭐ |
| 14 | 重掷按钮面板 | ~10 行 | ⭐ |
| 15 | 商店角色信息 | ~3 行 | ⭐ |

## 实施步骤

### 1. 新增 `<template>` 块

在 `index.html` 中找到对应区域（通常在 `<!-- templates -->` 注释附近），添加：

```html
<template id="tpl-my-panel">
  <!-- 完整 HTML 结构，不需要 JS 决定结构 -->
</template>
```

### 2. 重构 JS 方法

保留方法签名不变（不破坏调用方），内部改为：

```js
// 改前
_showXxx(data) {
  const html = `<div class="xxx">...${data.value}...</div>`;
  container.innerHTML = html;
}

// 改后
_showXxx(data) {
  const tpl = document.getElementById('tpl-xxx');
  const el = tpl.content.cloneNode(true);
  el.querySelector('[data-key="value"]').textContent = data.value;
  container.innerHTML = '';
  container.appendChild(el);
}
```

### 3. 验证

- 功能验证：`Ctrl+F5` 硬刷新后逐项检查
- 回归测试：`npm test` 全量通过
- 无 `Uncaught TypeError` 和空白区域

## 注意事项

1. **`<template>` 的 `content` 是 DocumentFragment**，`cloneNode(true)` 后可直接操作，但注意 `querySelector` 是在 fragment 上做，不是在 document 上
2. **不要在外层容器上用 innerHTML 清空后追加** — 用 `container.innerHTML = ''; container.appendChild(cloned)` 或设 `textContent = ''` 代替
3. **事件绑定**：模板中不要绑事件（事件在 JS 中通过委托或 `onclick` 绑定），事件逻辑和数据注入分离
4. **不要一次改完**— 依照 Phase 1→2→3 逐个 git commit，每个 Phase 可独立 `Ctrl+F5` 验证

## 预期收益

| 指标 | 改前 | 改后 |
|------|------|------|
| HTML 修改成本 | 搜 JS 字符串，小心引号 | 改 .html 文件，IDE 高亮 |
| CSS 选择器 | 无法利用 | 可用 #id .class |
| 新人上手 | 需理解 JS 模板字符串 | 看懂 HTML 即可 |
| 测试难度 | 功能测试 | HTML + JS 分开验证 |
