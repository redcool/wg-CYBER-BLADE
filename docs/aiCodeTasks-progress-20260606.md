# 20260606 收尾 — 进度保存 (断电前)

## 已完成
1. **Bug 修复: 枪手+手枪=1 伤害** (根因: 旧 `OLD_TAG_MAP` 把 `gun→ranged` 归一化, 但 `_isTagMatched` 比对 `player.tags (归一化后)` vs `weaponDef.tag (未归一化)`, 不匹配→0.10 兜底→1 伤害)
   - 修法: `formula.js:_isTagMatched` 双方都过 `TagSystem.normalizeTag`
   - 验证: 枪手+手枪 1→10 伤害
2. **架构: 抽 `extractCharacterTags` 工具 + 删 `OLD_TAG_MAP`** (新精确 tag 系统, csv 写 `gun/bow/magic/melee/lance/medic` 1:1)
3. **Bug 修复: 怪聚集阻挡玩家移动** (Brotato 风格 separation, 玩家身上重叠的怪被推开)
4. **UI: debug 面板移到 #hud 外, 战斗中始终可见**
5. **诊断: 加 9 条 csv 诊断条目 + 3 处 console.log 临时调试 → 修好后已删**
6. **测试: 5 个旧映射测试更新反映新系统, baseline 416/15 → 417/15 守恒**

## 关键文件改动
- `src/engine/tags.js`: 删 `OLD_TAG_MAP` + `getTagDef/normalizeTag` 改 identity
- `src/engine/character.js`: `_normalizeTags` 保留但简化 (只走 `TagSystem.normalizeTag`)
- `src/engine/formula.js`: `_isTagMatched` 双方都归一化 (兜底)
- `src/cyberblade/player.js`: `_updateMovement` 末尾加 separation 循环
- `csv/debug.csv` + `src/data/data-bundle.js`: 删 9 条临时诊断条目
- `test/unit/character.test.js`: C3/C15/C21 反映新系统
- `test/unit/tags.test.js`: T2/T5/T9/T10/T32 反映新系统
- `index.html`: ?v=2026060622, hudDebug 移出 #hud

## 待办 (明天续)
1. **武器 modal 显示惩罚后伤害** (非擅长武器预览实际伤害 = B×0.10 红色标"非擅长")
2. **可选: 修 `CharacterSystem.loadCharacters` fallback 缺失** (line 54-57 只 warn, 没填默认角色, 致 C2 等 16 测试 fail, 老 bug, 不紧急)
3. **可选: 旧标签迁移** (legacyGunWeapon 等 fixture 用 `gun` 标签, 跟新 7 大类不匹配, 7 大类的 synergy 不会触发旧标签武器; 长期应把旧标签也加进 TAG_DEFS 或迁移)
4. **验证: 浏览器测怪阻挡 + tag 系统 11 角色跑一遍**

## 验证命令
```bash
node --check src/engine/tags.js src/engine/character.js src/engine/formula.js src/cyberblade/player.js src/data/data-bundle.js
npm test  # 应 417/15
```
