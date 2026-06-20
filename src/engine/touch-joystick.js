// ============================================================
// touch-joystick.js - 移动端虚拟摇杆
// 基于 virtualjoystick.js 库（jeromeetienne），提供可靠的
// iOS 触摸支持和图层兼容。
//
// 关键设计：
// - VirtualJoystick 在 touchstart/touchmove/touchend 中
//   统一调用 preventDefault()，确保 iOS 不会优化掉 touchmove。
// - touchStartValidation 事件在菜单/奖励等场景返回 false，
//   阻止 preventDefault 影响 overlay 手势。
// - 自身 rAF 循环每帧轮询 deltaX/deltaY 更新 Input.joystickDir。
// ============================================================
const TouchJoystick = {
    testMode: false,
    _vj: null,
    _stickRadius: 50,
    active: false,
    _rafId: null,
    _boundOnVisible: null,
    _boundOnTouchCancel: null,

    CONFIG: {
        deadZone: 0.15,
    },

    init() {
        if (this._vj) return;
        if (!this.testMode && typeof DeviceDetect !== 'undefined' && DeviceDetect.isPC()) return;

        // 创建 VirtualJoystick 实例
        // 使用库自带的 canvas 元素绘制摇杆外观（stroke 圆环）
        // strokeStyle 匹配游戏的主题色
        this._vj = new VirtualJoystick({
            container: document.body,
            strokeStyle: '#ff8844',
            limitStickTravel: true,
            stickRadius: this._stickRadius,
            mouseSupport: false,
        });

        // 确保摇杆 canvas 位于 HUD/Overlay 之上
        this._vj._baseEl.style.zIndex = '1000';
        this._vj._stickEl.style.zIndex = '1000';

        // 验证事件：只在 gameplay 模式（无任何可见 overlay）激活摇杆
        // 菜单、角色选择、商店、升级奖励等界面不会触发 preventDefault，
        // 因此这些界面的手势操作（滚动、滑动）不受影响。
        this._vj.addEventListener('touchStartValidation', () => {
            if (!this._isGameplay()) return false;
        });

        // 跟踪激活状态
        this._vj.addEventListener('touchStart', () => { this.active = true; });
        this._vj.addEventListener('touchEnd', () => {
            this.active = false;
            if (window.Input) Input.joystickDir = null;
        });

        // ============================================================
        // 锁屏/来电/系统中断恢复
        // iOS 锁屏时 touch 被系统中断（不触发 touchend），
        // Vision state 的 _pressed=true _touchIdx 滞留，
        // 导致解锁后新触摸被拒绝、摇杆冻结。
        // ============================================================

        // 1) touchcancel：系统级触摸中断
        this._boundOnTouchCancel = (e) => {
            // 只有我们的摇杆正在触摸时才需要重置
            if (!this._vj || this._vj._touchIdx === null) return;
            console.log('[TouchJoystick] touchcancel → 重置摇杆');
            this._vj._onUp();
            this._vj._touchIdx = null;  // _onUp 不清理 touchIdx, 否则后续触摸被拒绝
            this.active = false;
            if (window.Input) Input.joystickDir = null;
        };
        document.addEventListener('touchcancel', this._boundOnTouchCancel, { passive: true });

        // 2) visibilitychange：锁屏/切后台回来后重置
        this._boundOnVisible = () => {
            if (document.visibilityState !== 'visible') return;
            if (!this._vj || this._vj._touchIdx === null) return;
            console.log('[TouchJoystick] 回到前台 → 重置摇杆');
            this._vj._onUp();
            this._vj._touchIdx = null;  // _onUp 不清理 touchIdx, 否则后续触摸被拒绝
            this.active = false;
            if (window.Input) Input.joystickDir = null;
        };
        document.addEventListener('visibilitychange', this._boundOnVisible);

        // 启动独立更新轮询
        this._startUpdateLoop();
    },

    /**
     * 判断是否 gameplay 模式：所有 overlay 均隐藏
     * 包括：菜单、角色的选择、游戏结束、商店、升级奖励
     */
    _isGameplay() {
        const ids = ['menuOverlay', 'gameOverOverlay', 'charSelectOverlay', 'shopOverlay', 'levelUpOverlay'];
        return ids.every(id => {
            const el = document.getElementById(id);
            if (!el) return true;
            if (el.classList.contains('hidden')) return true;
            if (el.style && el.style.display === 'none') return true;
            return false;
        });
    },

    _startUpdateLoop() {
        const tick = () => {
            this._update();
            this._rafId = requestAnimationFrame(tick);
        };
        this._rafId = requestAnimationFrame(tick);
    },

    /** 每帧轮询 VirtualJoystick 状态 → 更新 Input.joystickDir */
    _update() {
        if (!this._vj || !window.Input) {
            if (window.Input) Input.joystickDir = null;
            return;
        }

        if (!this._vj._pressed) {
            // joystick 未激活时由 touchEnd 事件负责清空 dir
            return;
        }

        const dx = this._vj.deltaX();
        const dy = this._vj.deltaY();
        const dist = Math.sqrt(dx * dx + dy * dy);
        const R = this._stickRadius;
        const dz = this.CONFIG.deadZone * R;

        let nx = 0, ny = 0;
        if (dist > dz) {
            nx = dx / R;
            ny = dy / R;
            const len = Math.sqrt(nx * nx + ny * ny);
            if (len > 1) { nx /= len; ny /= len; }
        }

        Input.joystickDir = { x: nx, y: ny };
    },

    destroy() {
        if (this._rafId) { cancelAnimationFrame(this._rafId); this._rafId = null; }
        if (this._boundOnTouchCancel) {
            document.removeEventListener('touchcancel', this._boundOnTouchCancel);
            this._boundOnTouchCancel = null;
        }
        if (this._boundOnVisible) {
            document.removeEventListener('visibilitychange', this._boundOnVisible);
            this._boundOnVisible = null;
        }
        if (this._vj) { this._vj.destroy(); this._vj = null; }
        this.active = false;
        if (window.Input) Input.joystickDir = null;
    },
};

if (typeof module !== 'undefined' && module.exports) module.exports = TouchJoystick;
else if (typeof window !== 'undefined') window.TouchJoystick = TouchJoystick;
