"""
===============================================================================
PNG 色度抠图（Chroma Key）工具
用法:
    python scripts/chroma_key.py [目录] [选项]

功能:
    - 批量处理目录下所有 .png 文件
    - 将接近指定颜色（默认黑色 0,0,0）的像素设为透明
    - 硬阈值，容差内全透明，容差外保持原样
    - 支持预览模式（--dry-run）

选项:
    --key-color  目标色  R,G,B  (默认 0,0,0 纯黑)
    --tolerance  容差      0~255 (默认 60，越大抠得越多)
    --invert     反向抠图（保留目标色，抠掉其他）

示例:
    # 抠黑底
    python scripts/chroma_key.py assets/chars

    # 抠白底
    python scripts/chroma_key.py assets/items --key-color 255,255,255

    # 抠绿幕
    python scripts/chroma_key.py assets/sprites --key-color 0,255,0 -t 80

    # 抠掉非黑色部分（保留黑底）
    python scripts/chroma_key.py assets/ui --invert -t 40

依赖: pip install Pillow
===============================================================================
"""
import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要 Pillow 库，请运行: pip install Pillow")
    sys.exit(1)

# 项目根目录（脚本所在目录的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def chroma_key_pixel(r, g, b, key_r, key_g, key_b, tolerance):
    """判断像素是否在容差范围内。
    返回 0（透明）或 255（不透明），硬阈值无过渡。
    """
    dr = r - key_r
    dg = g - key_g
    db = b - key_b
    dist = (dr * dr + dg * dg + db * db) ** 0.5
    # 硬阈值：在容差内 → 全透明，否则保留原样
    return 0 if dist <= tolerance else 255


def process_image(filepath: Path, key_color, tolerance, invert, dry_run) -> bool:
    """处理单张 PNG，返回 True 表示已修改。"""
    try:
        img = Image.open(filepath).convert("RGBA")
    except Exception as e:
        print(f"  ⚠ 打开失败: {filepath.name} — {e}")
        return False

    key_r, key_g, key_b = key_color
    pixels = img.load()
    if pixels is None:
        print(f"  ⚠ 无法读取像素数据: {filepath.name}")
        return False
    w, h = img.size
    modified = False

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]  # type: ignore[misc]
            if a == 0:
                continue  # 已经是透明的，跳过
            new_alpha = chroma_key_pixel(r, g, b, key_r, key_g, key_b, tolerance)
            if invert:
                # 反向：保留目标色（不透明），抠掉其他
                new_alpha = 255 - new_alpha
            # 如果原有 alpha 更小，取更小值
            new_alpha = min(a, new_alpha)
            if new_alpha != a:
                if not dry_run:
                    pixels[x, y] = (r, g, b, new_alpha)
                modified = True

    if dry_run and modified:
        print(f"  ○ {filepath.relative_to(PROJECT_ROOT)} — 需要处理")

    if not dry_run and modified:
        img.save(filepath, optimize=True)
        print(f"  ✓ {filepath.name} — 已抠图")
        return True

    if not dry_run and not modified:
        print(f"  - {filepath.name} — 无变化")

    return modified


def main():
    parser = argparse.ArgumentParser(
        description="将 PNG 中接近指定颜色的像素设为透明"
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="assets",
        help="要扫描的目录（相对于项目根目录，默认 assets）"
    )
    parser.add_argument(
        "--key-color", "-k",
        type=str,
        default="0,0,0",
        help="目标色 R,G,B（默认 0,0,0 纯黑）"
    )
    parser.add_argument(
        "--tolerance", "-t",
        type=int,
        default=60,
        help="颜色容差 0~255（默认 60，越大抠得越多）"
    )
    parser.add_argument(
        "--invert", "-i",
        action="store_true",
        help="反向抠图：保留目标色，抠掉其他颜色"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="仅预览，不实际写入"
    )
    args = parser.parse_args()

    # 解析颜色
    try:
        key_color = tuple(int(c.strip()) for c in args.key_color.split(","))
        if len(key_color) != 3:
            raise ValueError
        if not all(0 <= c <= 255 for c in key_color):
            raise ValueError
    except (ValueError, AttributeError):
        print("错误: --key-color 格式无效，示例: --key-color 0,0,0")
        sys.exit(1)

    tolerance = max(0, min(255, args.tolerance))
    dry_run = args.dry_run
    invert = args.invert
    target_dir = (PROJECT_ROOT / args.directory).resolve()

    if not target_dir.is_dir():
        print(f"错误: 目录不存在: {target_dir}")
        sys.exit(1)

    mode_label = "反向" if invert else "正向"
    print(f"{'='*60}")
    print(f"  PNG 色度抠图")
    print(f"  目录: {target_dir}")
    print(f"  目标色: RGB{key_color} ({mode_label})")
    print(f"  容差: {tolerance}")
    if dry_run:
        print(f"  模式: 预览 (不写入)")
    print(f"{'='*60}")

    png_files = sorted(target_dir.rglob("*.png"))
    if not png_files:
        print("未找到任何 .png 文件")
        return

    modified = 0
    for fp in png_files:
        if process_image(fp, key_color, tolerance, invert, dry_run):
            modified += 1

    print(f"\n{'='*60}")
    print(f"  完成: 已处理 {len(png_files)} 个文件, 修改 {modified} 个")
    print(f"{'='*60}")
    print(f"  提示: 如果结果不理想，调整 --tolerance")
    print(f"        较大值 → 抠更多;  较小值 → 抠更少")
    if key_color == (0, 0, 0):
        print(f"  如果背景不是纯黑而是深色，试试 --tolerance 80~120")


if __name__ == "__main__":
    main()
