// ============================================================
// test/setup.js — Vitest 全局设置
// 提供全局 SystemConfig mock（数据源: src/data/system.json）
// ============================================================
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

/** 从 system.json 构建 SystemConfig mock */
function buildSystemConfig() {
    const jsonPath = resolve(__dirname, '../src/data/system.json');
    let rows;
    try {
        const raw = readFileSync(jsonPath, 'utf-8');
        rows = JSON.parse(raw);
    } catch {
        // 若文件不存在（首次 clone 未生成），用空数组
        rows = [];
    }

    const cache = {};
    for (const row of rows) {
        if (!row || !row.key) continue;
        cache[row.key] = cast(row.value, row.valueType);
    }

    return {
        _loaded: true,
        _cache: cache,
        isLoaded() { return true; },
        get(key) {
            if (this._cache[key] !== undefined && this._cache[key] !== null) {
                return this._cache[key];
            }
            throw new Error(`[SystemConfig] 缺少配置项: "${key}" — 请在 csv/system.csv 中定义`);
        },
    };
}

function cast(raw, type) {
    if (raw === null || raw === undefined) return null;
    switch (type) {
        case 'number': {
            const v = parseFloat(raw);
            return isNaN(v) ? 0 : v;
        }
        case 'boolean':
            return String(raw).toLowerCase() === 'true' || raw === '1';
        default:
            return String(raw);
    }
}

// 设置全局 SystemConfig（与浏览器端 window.SystemConfig 对应）
globalThis.SystemConfig = buildSystemConfig();
