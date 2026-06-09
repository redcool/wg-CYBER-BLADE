# cyberBlade UI 模块界面规范

## 原则

1. **HTML 是 HTML，JS 是 JS** — 结构标签放在 `<template>` 中，JS 只负责数据和行为
2. **数据驱动** — 使用 `data-key`、`data-if`、`data-class` 等属性规范数据注入
3. **事件委托** — 不在模板中绑 onclick，使用父容器事件监听
4. **方法单一职责** — 一个方法要么渲染，要么绑定事件，不要混合

---

## 标准渲染模式

### 1. 在 `index.html` 定义模板

```html
<!-- ===== Templates ===== -->

<!-- 简单面板 -->
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

    <div class="wd-dmg-breakdown-row wd-dmg-breakdown-total">
      <span>有效伤害</span>
      <span class="dmg" data-key="effDmg"></span>
    </div>
  </div>
</template>

<!-- 带条件类的模板 -->
<template id="tpl-fit-bar">
  <div class="wd-fit-section">
    <div class="wd-fit-label">角色适配度 <span data-key="fitPct" data-class="fit-level"></span></div>
    <div class="wd-fit-bar">
      <div class="wd-fit-fill" data-key="fitBarWidth"></div>
    </div>
  </div>
</template>
```

### 2. 模板命名规则

```
tpl-{模块名}-{面板名}
```

| 模板 ID | 用途 |
|---------|------|
| `tpl-dmg-breakdown` | 伤害计算明细 |
| `tpl-weapon-card` | 武器选择图标卡片 |
| `tpl-char-detail` | 角色详情面板 |
| `tpl-shop-item` | 商店武器/物品卡片 |
| `tpl-synergy-block` | 羁绊加成块 |
| `tpl-fit-panel` | 角色适配度面板 |

### 3. 数据注入约定

| 属性 | 用途 | JS 处理 |
|------|------|---------|
| `data-key="name"` | 填入文本 | `el.querySelector('[data-key="name"]').textContent = val` |
| `data-if="cond"` | 条件显示 | `if (!cond) el.querySelector('[data-if="cond"]').remove()` |
| `data-class="state"` | 动态 CSS 类 | `el.querySelector('[data-class="state"]').classList.add('active')` |
| `data-attr-href="url"` | 动态属性 | `el.querySelector('[data-attr-href]').href = url` |

### 4. JS 标准渲染方法

```js
_renderXxx(data) {
  // 1. 获取模板
  const tpl = document.getElementById('tpl-xxx');
  if (!tpl) return;

  // 2. clone 模板
  const el = tpl.content.cloneNode(true);

  // 3. 注入数据
  el.querySelector('[data-key="field1"]').textContent = data.field1;

  // 4. 条件显隐
  const condEl = el.querySelector('[data-if="field2"]');
  if (condEl && !data.field2) condEl.remove();

  // 5. 动态类
  const clsEl = el.querySelector('[data-class="state"]');
  if (clsEl) clsEl.classList.add(data.active ? 'active' : 'inactive');

  // 6. 挂载到 DOM
  const container = document.getElementById('xxxContainer');
  container.textContent = ''; // 清空（替代 innerHTML = ''）
  container.appendChild(el);
}
```

---

## 事件绑定规范

不要在模板中绑 `onclick`：

```html
<!-- ❌ 错误：事件写在模板中 -->
<template id="tpl-btn">
  <button onclick="handleClick()">点我</button>
</template>

<!-- ✅ 正确：模板无事件 -->
<template id="tpl-btn">
  <button class="js-action-btn">点我</button>
</template>
```

```js
// 在 init 或 setup 方法中用事件委托
_initEvents() {
  document.getElementById('parentContainer').addEventListener('click', (e) => {
    const btn = e.target.closest('.js-action-btn');
    if (btn) this._handleAction(btn.dataset.id);
  });
}
```

---

## 容器清理规范

```js
// ❌ 错误：用 innerHTML 清空
container.innerHTML = '';
container.innerHTML = htmlString;

// ✅ 正确：用 textContent 或 removeChildren
container.textContent = '';
container.appendChild(fragment);

// ✅ 或者（批量移除子节点）
while (container.firstChild) container.removeChild(container.firstChild);
```

---

## 数据预处理的放置

- **渲染方法**只负责：取模板 → 注入数据 → 挂载
- **数据预处理**（如 `_calcBaseDamage`、`_calcClassFitMult`）放在渲染方法之前，或提取为独立方法

```js
// ✅ 正确：数据结构化后再渲染
_showWeaponDetail(weaponId) {
  const weapon = ShopSystem.allWeapons.find(w => w.id === weaponId);
  const computed = this._computeWeaponDisplayData(weapon);
  this._renderWeaponDetail(computed); // 只负责注入
}

_computeWeaponDisplayData(weapon) {
  return {
    name: weapon.name,
    dmg: FormulaSystem._calcBaseDamage(weapon, player, 1),
    // ...
  };
}
```

---

## 渐进改造说明

现有代码已部分使用 `<template>` 模式，但大多数还是 HTML-in-JS。

改造原则：

1. **改动最小化** — 优先改造高频变更的面板（商店卡片、详情弹窗等）
2. **不改变功能** — 改结构不改逻辑，验证前后输出一致
3. **单文件提交** — 每个面板改造独立 commit

详见 `docs/html-in-js-migration-plan.md`。

---

## 修改检查清单

| 步骤 | 检查项 |
|------|--------|
| 1 | 模板用 `<template id="tpl-...">` 包裹 |
| 2 | 模板不在 JS 中做字符串拼接 |
| 3 | 数据注入用 `data-key` 属性 |
| 4 | 条件显隐用 `data-if` + `remove()` |
| 5 | 动态类用 `data-class` + `classList` |
| 6 | 事件用委托，模板无 `onclick` |
| 7 | 清空容器用 `textContent = ''` |
| 8 | `Ctrl+F5` 硬刷新后功能正常 |
| 9 | `npm test` 全量通过 |
