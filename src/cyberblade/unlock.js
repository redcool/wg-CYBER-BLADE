// ============================================================
// cyberblade/unlock.js - 解锁进度系统（localStorage跨局保存）
// 数据驱动：武器解锁条件从 weapons.csv (unlockType/unlockValue) 读取，
//           角色解锁条件从 characters.csv (unlockType/unlockValue) 读取
// ============================================================
const STORAGE_KEY = 'cyberblade_unlocks';

const UnlockSystem = {
    // 跨局统计
    stats: {
        totalKills: 0,
        totalMaterials: 0,
        totalLevels: 0,     // 累计通关关卡数
        maxLevel: 0,         // 单局最高关卡
        highestLevel: 0,
        totalPlayTime: 0,
    },
    // 解锁集
    unlockedWeapons: new Set(),
    // 基础武器ID列表（用于武器选择界面） — 从 CSV isBasic 动态生成
    basicWeaponIds: new Set(),
    unlockedCharacters: new Set(),

    _dataLoaded: false,

    // 本局记录（仅用于结算时更新跨局统计）
    sessionStats: {
        weapons: [],   // 装备过的武器id
        items: [],     // 购买过的道具id
        levelsCleared: 0,
        kills: 0,
        materials: 0,
    },

    /** 初始化 - 从localStorage读取 */
    init() {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const data = JSON.parse(saved);
                this.stats = data.stats || this.stats;
                if (data.unlockedWeapons) {
                    this.unlockedWeapons = new Set(data.unlockedWeapons);
                }
                if (data.unlockedCharacters) {
                    this.unlockedCharacters = new Set(data.unlockedCharacters);
                }
            }
        } catch (e) {
            console.warn('UnlockSystem: Failed to load saves', e);
        }
        // 如果 DataLoader 已就绪，立即加载 CSV 默认值
        if (typeof DataLoader !== 'undefined' && DataLoader._cache) {
            this._loadCSVDefaults();
        }
    },

    /**
     * 从 CSV 数据加载默认解锁和 basicWeaponIds
     * 由 engine.js GameEngine.init() 在 DataLoader 加载完成后调用
     */
    loadData() {
        this._loadCSVDefaults();
    },

    /** 内部：加载 CSV 默认解锁 */
    _loadCSVDefaults() {
        if (this._dataLoaded) return;

        let hadWeaponData = false;
        let hadCharData = false;

        // --- 武器 ---
        if (Array.isArray(DataLoader._cache?.weapons)) {
            hadWeaponData = true;
            for (const w of DataLoader._cache.weapons) {
                if (w.isBasic) {
                    this.basicWeaponIds.add(w.id);
                }
                // 默认解锁条件：isBasic (基础武器) 或 无 unlockType (无锁定)
                if (w.isBasic || !w.unlockType) {
                    if (!this.unlockedWeapons.has(w.id)) {
                        this.unlockedWeapons.add(w.id);
                    }
                }
            }
        }

        // --- 角色（从 characters.csv unlocked 字段 + unlockType）---
        if (Array.isArray(DataLoader._cache?.characters)) {
            hadCharData = true;
            for (const c of DataLoader._cache.characters) {
                // unlocked=true 或者没有 unlockType → 默认解锁
                if (c.unlocked || !c.unlockType) {
                    if (!this.unlockedCharacters.has(c.id)) {
                        this.unlockedCharacters.add(c.id);
                    }
                }
            }
        }

        // 只有确实读取到了数据，才标记为已加载（防止 DataLoader 尚未就绪时跳过）
        if (hadWeaponData && hadCharData) {
            this._dataLoaded = true;
        }
    },

    /** 保存到localStorage */
    _save() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify({
                stats: this.stats,
                unlockedWeapons: [...this.unlockedWeapons],
                unlockedCharacters: [...this.unlockedCharacters],
            }));
        } catch (e) {
            console.warn('UnlockSystem: Failed to save', e);
        }
    },

    /** 重置本局记录 */
    resetSession() {
        this.sessionStats = { weapons: [], items: [], levelsCleared: 0, kills: 0, materials: 0 };
    },

    /** 记录本局购买的武器 */
    recordWeaponBought(weaponId) {
        if (!this.sessionStats.weapons.includes(weaponId)) {
            this.sessionStats.weapons.push(weaponId);
        }
    },

    /** 记录本局购买的道具 */
    recordItemBought(itemId) {
        if (!this.sessionStats.items.includes(itemId)) {
            this.sessionStats.items.push(itemId);
        }
    },

    /** 本局结束 - 结算并检查新解锁 */
    endSession() {
        const ss = this.sessionStats;

        // 从玩家身上获取本局材料收入（未花完的金币 = 已赚取）
        const p = typeof PlayerSystem !== 'undefined' ? PlayerSystem.player : null;
        if (p) {
            ss.materials = p.materials;
        }

        // 更新跨局统计
        this.stats.totalKills += ss.kills;
        this.stats.totalMaterials += ss.materials;
        this.stats.totalLevels += ss.levelsCleared;
        if (ss.levelsCleared > this.stats.maxLevel) {
            this.stats.maxLevel = ss.levelsCleared;
        }
        if (ss.levelsCleared > this.stats.highestLevel) {
            this.stats.highestLevel = ss.levelsCleared;
        }

        // 检查新解锁（确保数据已加载）
        if (!this._dataLoaded) this._loadCSVDefaults();
        const newUnlocks = this._checkUnlocks();

        // 保存到 localStorage
        this._save();
        if (typeof SaveSystem !== 'undefined') {
            SaveSystem.save();
        }
        return {
            newUnlocks,
            weaponsUsed: [...ss.weapons],
            itemsUsed: [...ss.items],
        };
    },

    /** 检查所有解锁条件（武器 + 角色） */
    _checkUnlocks() {
        const newUnlocks = [];

        // ====== 武器解锁 — 从 DataLoader._cache.weapons 读取 ======
        if (Array.isArray(DataLoader._cache?.weapons)) {
            for (const w of DataLoader._cache.weapons) {
                if (!w.unlockType) continue; // 无锁定条件
                if (this.unlockedWeapons.has(w.id)) continue; // 已解锁
                if (this._checkCondition(w.unlockType, w.unlockValue)) {
                    this.unlockedWeapons.add(w.id);
                    newUnlocks.push({ type: 'weapon', id: w.id });
                }
            }
        }

        // ====== 角色解锁 — 从 DataLoader._cache.characters 读取 ======
        if (Array.isArray(DataLoader._cache?.characters)) {
            for (const c of DataLoader._cache.characters) {
                if (!c.unlockType) continue;
                if (this.unlockedCharacters.has(c.id)) continue;
                if (this._checkCondition(c.unlockType, c.unlockValue)) {
                    this.unlockedCharacters.add(c.id);
                    newUnlocks.push({ type: 'character', id: c.id });
                }
            }
        }

        return newUnlocks;
    },

    /**
     * 检查单个解锁条件
     * @param {string} type - 条件类型: totalLevels | totalKills | maxLevel
     * @param {number} value - 阈值
     */
    _checkCondition(type, value) {
        switch (type) {
            case 'totalLevels': return this.stats.totalLevels >= value;
            case 'totalKills':  return this.stats.totalKills >= value;
            case 'maxLevel':    return this.stats.maxLevel >= value;
            default: return false;
        }
    },

    /** 检查是否已解锁武器 */
    isWeaponUnlocked(id) {
        return this.unlockedWeapons.has(id);
    },

    /** 检查是否已解锁角色 */
    isCharacterUnlocked(id) {
        return this.unlockedCharacters.has(id);
    },
};

// 自动初始化
UnlockSystem.init();
