// ============================================================
// device.js — 设备类型检测
// 提供统一的方法判断运行环境：pc / mobile / tablet
// ============================================================
const DeviceDetect = {
    /** 缓存结果，避免重复计算 */
    _type: null,

    /**
     * 返回设备类型:
     *   'pc'      — 桌面电脑（无触屏）
     *   'mobile'  — 手机（触屏 + 小屏幕）
     *   'tablet'  — 平板（触屏 + 中等屏幕）
     *   'tv'      — 智能电视
     *   'unknown' — 无法判断
     */
    getType() {
        if (this._type) return this._type;

        // 1) UA 关键字快速匹配（先于触屏检测，因为 Win11 触屏本 ontouchstart 为 true）
        const ua = (navigator.userAgent || '').toLowerCase();

        // 智能电视
        if (/tv|smart-tv|googletv|appletv|roku/.test(ua)) {
            this._type = 'tv';
            return this._type;
        }

        // 平板: iPadOS 或明确 tablet 标识
        const isTabletUA = /ipad|tablet|playbook|silk|android(?!.*mobile)/.test(ua);
        // 手机: 手机 UA 关键字
        const isMobileUA = /mobile|iphone|ipod|blackberry|opera mini|opera mobi|iemobile|wpdesktop/.test(ua);

        // 2) 触屏能力
        const hasTouch = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;

        // 3) 屏幕尺寸判断
        // 对有触屏的设备，用屏幕尺寸区分手机 vs 平板
        const w = window.innerWidth;
        const h = window.innerHeight;
        const minDim = Math.min(w, h);

        if (hasTouch) {
            if (isTabletUA || (!isMobileUA && minDim >= 600)) {
                this._type = 'tablet';
            } else {
                this._type = 'mobile';
            }
        } else if (isMobileUA || isTabletUA) {
            // 无触屏但有移动 UA（极罕见，如某些模拟器）
            this._type = isTabletUA ? 'tablet' : 'mobile';
        } else {
            this._type = 'pc';
        }

        return this._type;
    },

    /** 简写: 是否移动设备（mobile 或 tablet） */
    isMobile() {
        const t = this.getType();
        return t === 'mobile' || t === 'tablet';
    },

    /** 简写: 是否触摸设备（手机/平板/触屏本） */
    isTouchDevice() {
        return ('ontouchstart' in window) || navigator.maxTouchPoints > 0;
    },

    /** 简写: 是否 PC */
    isPC() {
        return this.getType() === 'pc';
    },
};

// 模块导出
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DeviceDetect;
} else if (typeof window !== 'undefined') {
    window.DeviceDetect = DeviceDetect;
}
