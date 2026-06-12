// ============================================================
// resourceLoader.js — 统一的资源加载器
// 约定: 每个 CSV/数据表对应 assets/{dir}/{id}.png
// 所有资源 ID 从已加载的 JSON 数据中动态读取，不硬编码
// ============================================================

/**
 * @typedef {Object} ResourceLoaderConfig
 * @property {string}  csvName       - DataLoader._cache 中的键名（如 'items', 'weapons'）
 * @property {string}  assetDir      - assets/ 下的子目录（如 'items', 'weapons'）
 * @property {string}  [fallbackText] - 图片缺失时显示的兜底文本（如 '🔧' 或 'I'）
 * @property {boolean} [skipCleanup] - 是否跳过黑色背景清理（ComfyUI PNG 需要清理）
 */

class ResourceLoader {
    /** @param {ResourceLoaderConfig} config */
    constructor(config) {
        this.csvName = config.csvName;
        this.assetDir = config.assetDir;
        this.fallbackText = config.fallbackText || '?';
        this.skipCleanup = !!config.skipCleanup;

        /** @type {Object<string, HTMLImageElement>} */
        this.cache = {};
        /** @type {Set<string>} */
        this.failedIds = new Set();
        /** @type {boolean} */
        this._loaded = false;
    }

    /**
     * 从 DataLoader 的缓存中收集所有资源 ID
     * @returns {string[]}
     */
    _collectIds() {
        if (typeof DataLoader === 'undefined' || !DataLoader._cache) {
            console.warn(`[ResourceLoader] DataLoader 未就绪，${this.csvName} 将跳过预加载`);
            return [];
        }
        const records = DataLoader._cache[this.csvName];
        if (!Array.isArray(records)) {
            console.warn(`[ResourceLoader] DataLoader._cache.${this.csvName} 不是数组`);
            return [];
        }
        return records.map(r => r.id).filter(Boolean);
    }

    /**
     * 预加载所有资源
     * @returns {Promise<void>}
     */
    preloadAll() {
        if (this._loaded) return Promise.resolve();
        return new Promise((resolve) => {
            const ids = this._collectIds();
            if (ids.length === 0) {
                this._loaded = true;
                resolve();
                return;
            }

            let total = ids.length;
            let loaded = 0;
            const _v = Date.now();

            const onLoad = () => {
                loaded++;
                if (loaded >= total) {
                    this._loaded = true;
                    resolve();
                }
            };

            for (const id of ids) {
                const src = `assets/${this.assetDir}/${id}.png?v=${_v}`;
                this._loadImage(src, id, (img) => {
                    this.cache[id] = img;
                    onLoad();
                }, () => {
                    this.failedIds.add(id);
                    onLoad();
                });
            }
        });
    }

    /**
     * 加载单张图片
     * @param {string} src
     * @param {function(HTMLImageElement): void} onSuccess
     * @param {function(): void} onError
     */
    _loadImage(src, id, onSuccess, onError) {
        const img = new Image();
        img.onload = () => {
            if (this.skipCleanup) {
                onSuccess(img);
            } else {
                const cleaned = this._removeBlackBg(img);
                if (cleaned && cleaned.toDataURL) {
                    const cleanedImg = new Image();
                    cleanedImg.onload = () => onSuccess(cleanedImg);
                    cleanedImg.onerror = () => onSuccess(cleanedImg);
                    cleanedImg.src = cleaned.toDataURL();
                } else {
                    onSuccess(img);
                }
            }
        };
        img.onerror = () => {
            console.warn(`[ResourceLoader] 加载失败: ${src}`);
            const fallback = this._createFallback();
            fallback.onload = () => onSuccess(fallback);
            fallback.onerror = () => onSuccess(fallback);
            if (onError) onError();
        };
        img.src = src;
    }

    /** 移除 ComfyUI PNG 的黑色背景 */
    _removeBlackBg(img) {
        try {
            const c = document.createElement('canvas');
            c.width = img.naturalWidth || img.width;
            c.height = img.naturalHeight || img.height;
            if (c.width === 0 || c.height === 0) return null;
            const ctx = c.getContext('2d');
            ctx.drawImage(img, 0, 0);
            const imageData = ctx.getImageData(0, 0, c.width, c.height);
            const data = imageData.data;

            // 取四角平均亮度判断背景色
            const corners = [
                { r: data[0], g: data[1], b: data[2] },
                { r: data[(c.width - 1) * 4], g: data[(c.width - 1) * 4 + 1], b: data[(c.width - 1) * 4 + 2] },
                { r: data[(c.height - 1) * c.width * 4], g: data[(c.height - 1) * c.width * 4 + 1], b: data[(c.height - 1) * c.width * 4 + 2] },
                { r: data[(c.height - 1) * c.width * 4 + (c.width - 1) * 4], g: data[(c.height - 1) * c.width * 4 + (c.width - 1) * 4 + 1], b: data[(c.height - 1) * c.width * 4 + (c.width - 1) * 4 + 2] },
            ];
            const avgBrightness = corners.reduce((sum, p) => sum + p.r + p.g + p.b, 0) / 12;
            const threshold = 60;

            for (let i = 0; i < data.length; i += 4) {
                const r = data[i], g = data[i+1], b = data[i+2];
                if (avgBrightness > 128) {
                    if (r > 255 - threshold && g > 255 - threshold && b > 255 - threshold) {
                        data[i+3] = 0;
                    }
                } else {
                    if (r + g + b < 50) {
                        data[i+3] = 0;
                    }
                }
            }
            ctx.putImageData(imageData, 0, 0);
            return c;
        } catch (e) {
            console.warn('[ResourceLoader] _removeBlackBg 失败:', e);
            return null;
        }
    }

    /** 创建兜底图片（灰色 ? 图标） */
    _createFallback() {
        const canvas = document.createElement('canvas');
        canvas.width = 48;
        canvas.height = 48;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = '#333';
        ctx.fillRect(0, 0, 48, 48);
        ctx.fillStyle = '#666';
        ctx.font = 'bold 20px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('?', 24, 24);
        const fallback = new Image();
        fallback.src = canvas.toDataURL();
        return fallback;
    }

    /** 获取图片元素 */
    getImage(id) {
        return this.cache[id] || null;
    }

    /** 是否加载失败（走兜底） */
    isFailed(id) {
        return this.failedIds.has(id);
    }

    /** 生成 HTML 字符串 */
    getHTML(id, size) {
        const s = size || 48;
        const img = this.cache[id];
        if (!img) {
            return `<div class="icon-fallback" style="width:${s}px;height:${s}px;font-size:${Math.round(s * 0.6)}px;line-height:${s}px;text-align:center">${this.fallbackText}</div>`;
        }
        return `<img class="asset-icon" src="${img.src}" alt="${id}" width="${s}" height="${s}" style="object-fit:contain;" >`;
    }
}

// 用于从 data-bundle.js 导入（非 ES Module 环境下通过全局变量使用）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ResourceLoader };
}
