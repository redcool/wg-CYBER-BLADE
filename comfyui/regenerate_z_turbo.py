#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBER BLADE - Z-Image-Turbo 子蓝图全面再生脚本 v2
==============================================
精确匹配 z-image-turbo-workflow.json 子蓝图结构:
  - CheckpointLoaderSimple → z-image-turbo.safetensors (fallback: UNETLoader)
  - EmptyLatentImage 512x512
  - KSampler: steps=5, cfg=1.5, euler, scheduler=simple
  - 简洁正向/反向提示词
  - 所有武器/道具/角色/敌人 全面再生

用法:
  1. 确保 ComfyUI 已启动（默认 http://127.0.0.1:8188）
  2. python comfyui/regenerate_z_turbo.py
"""

import json
import time
import os
import sys
import shutil
import urllib.request
import urllib.error

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "H:/AI/ComfyUI_windows_portable/ComfyUI/output"
ASSETS_DIR = "H:/ai_works/buffPrj1/assets"

# ====== 风格锚 ======
GLOBAL_ICON_STYLE = (
    "CYBER BLADE game icon, bold outlines, saturated flat colors, "
    "cel-shaded, game-ready icon art, single centered item filling the frame. "
    "Solid dark #0d0d24 background, NO background gradients, "
    "NO text, NO labels, NO watermark, NO signature. "
    "Perfect circles, sharp edges, clean silhouettes, "
    "centered and cropped tightly around the item, no padding."
)

GLOBAL_CHAR_STYLE = (
    "CYBER BLADE top-down 2D game character portrait, bold outlines, "
    "saturated flat colors, cel-shaded, game-ready sprite art, "
    "waist-up portrait view, character centered and facing forward. "
    "Solid dark #0d0d24 background, NO gradients, "
    "NO text, NO labels, NO watermark, NO signature."
)

GLOBAL_ENEMY_STYLE = (
    "CYBER BLADE top-down 2D game enemy portrait, bold outlines, "
    "saturated flat colors, cel-shaded, game-ready sprite art, "
    "creature centered and facing forward, menacing pose. "
    "Solid dark #0d0d24 background, NO gradients, "
    "NO text, NO labels, NO watermark, NO signature."
)

# ====== 全部武器定义 (45种 from shop.js) ======

WEAPONS = [
    # --- 近战 melee × 10 ---
    ("plasma", "等离子刀",
     "Plasma sword, futuristic energy blade with bright red-hot edge glowing, "
     "black reinforced handle, isometric angled view, energy crackling along edge."),
    ("axe", "能量斧",
     "Energy axe, large double-bladed battle axe with orange glowing edges, "
     "dark metal haft, heavy blade, powerful melee weapon icon."),
    ("dagger", "双持匕首",
     "Dual curved daggers, silver blades with blue edge glow, "
     "crossed in X formation, ninja-style assassin daggers."),
    ("chainsaw", "链锯剑",
     "Chainsaw sword, mechanical blade with spinning chainsaw teeth, "
     "orange and dark metal, industrial weapon, saw teeth visible."),
    ("sword", "能量剑",
     "Energy sword, sleek straight blade with bright blue energy edge, "
     "sci-fi hilt with guard, elegant futuristic broadsword icon."),
    ("katana", "武士刀",
     "Japanese katana, curved single-edged blade with white temper line, "
     "black wrapped handle with golden tsuba guard, angled blade-up view."),
    ("hammer", "重锤",
     "Heavy war hammer, massive rectangular head with orange energy glow on striking face, "
     "thick metal handle, brutal crushing weapon icon."),
    ("spear", "能量矛",
     "Energy spear, long shaft with bright cyan energy blade tip, "
     "two-pronged spearhead, futuristic polearm icon."),
    ("claws", "利爪",
     "Three curved energy claws mounted on knuckle bracket, "
     "green glowing claw blades, wolverine-style weapon icon."),
    ("whip", "能量鞭",
     "Energy whip, segmented power cable with purple energy glow, "
     "coiled into an S-shape, crackling with electricity icon."),

    # --- 枪械 gun × 10 ---
    ("pistol", "基础手枪",
     "Semi-automatic pistol, compact sleek silver and blue frame, "
     "short barrel, ergonomic grip, side profile view."),
    ("smg", "冲锋枪",
     "Submachine gun, compact automatic weapon with perforated barrel shroud, "
     "folded stock, high rate-of-fire design, side profile view."),
    ("shotgun", "散弹枪",
     "Tactical shotgun, short wide barrel with tube magazine underneath, "
     "pump-action forend, side profile view."),
    ("sniper", "狙击枪",
     "Sniper rifle, extremely long barrel with muzzle brake, "
     "high-magnification scope on top, bipod legs, side profile view."),
    ("gatling", "加特林",
     "Rotary gatling gun, six-barrel rotating assembly, "
     "gold and dark metal finish, front angled view showing all six barrels."),
    ("revolver", "左轮手枪",
     "Six-shot revolver, silver frame with swing-out cylinder, "
     "long barrel, classic cowboy revolver design, side profile."),
    ("rifle", "突击步枪",
     "Assault rifle, mid-length barrel with magazine, "
     "tactical rail system, ergonomic stock, modern combat rifle."),
    ("shotgun_double", "双管散弹",
     "Double-barrel shotgun, two barrels side by side, "
     "break-action design, sawed-off style, wide muzzle view."),
    ("magnum", "马格南",
     "Large caliber magnum revolver, long heavy barrel with vented rib, "
     "large cylinder, powerful hand cannon design, side view."),
    ("minigun", "迷你机枪",
     "Mini rotary cannon, compact four-barrel design with ammo feed belt, "
     "motor housing on front, portable heavy weapon icon."),

    # --- 弓箭 bow × 10 ---
    ("bow", "长弓",
     "Classic longbow, tall wooden arc with bowstring, "
     "simple elegant design, traditional archery weapon icon."),
    ("crossbow", "弩",
     "Crossbow, horizontal bow mounted on rifle stock with trigger mechanism, "
     "steel limbs, tactical crossbow design."),
    ("longbow", "强弓",
     "Reinforced longbow, composite recurve design with extra limb tips, "
     "powerful heavy bow, archery icon."),
    ("recurve", "反曲弓",
     "Recurve bow, modern Olympic-style curved tips, "
     "sleek limbs, precision archery weapon icon."),
    ("explosive_arrow", "爆裂箭",
     "Explosive arrow, arrow with red-tipped explosive head, "
     "fins on shaft, rocket-propelled warhead arrow icon."),
    ("frost_arrow", "冰霜箭",
     "Ice arrow, crystalline frozen arrowhead with blue-white frost, "
     "icy shards along shaft, freezing cold arrow icon."),
    ("poison_arrow", "毒箭",
     "Poison arrow, green-tipped arrow with dripping venom, "
     "purple shaft, toxic glowing arrowhead icon."),
    ("triple_shot", "三连弓",
     "Triple-shot bow, bow with three parallel strings and three arrow nocks, "
     "multi-shot mechanical bow design icon."),
    ("piercing_shot", "穿甲箭",
     "Armor-piercing arrow, heavy steel-tipped arrow with conical piercing head, "
     "tungsten core, anti-armor arrow icon."),
    ("homing_bow", "追踪弓",
     "Homing bow, high-tech bow with pink energy targeting reticle projected above, "
     "sleek futuristic limbs, holographic targeting effect."),

    # --- 元素 magic × 13 ---
    ("fire_staff", "火球杖",
     "Fire staff, wooden staff with floating red fire orb on top, "
     "flame spiral around orb, magical fire weapon icon."),
    ("frost_staff", "冰霜杖",
     "Frost staff, crystalline ice staff with blue-white frozen orb on top, "
     "cold mist radiating, ice crystals, icy blue glow."),
    ("thunder_staff", "雷电杖",
     "Thunder staff, metal staff with lightning bolt fork on top, "
     "yellow-white electricity arcing, storm magic weapon icon."),
    ("energy_staff", "能量杖",
     "Energy staff, sci-fi metal staff with blue energy orb and rings spinning around it, "
     "mystical energy weapon icon."),
    ("magic_orb", "魔法弹",
     "Magic orb, floating sphere of purple and blue energy, "
     "glowing magical projectile, swirling arcane power icon."),
    ("poison_staff", "毒杖",
     "Poison staff, twisted wooden staff with green toxic bubbling orb, "
     "purple veins on wood, poisonous magic weapon icon."),
    ("void_staff", "虚空杖",
     "Void staff, dark ritual staff with black-purple swirling vortex orb, "
     "spacetime distortion, dark magic weapon icon."),
    ("lightning_staff", "闪电杖",
     "Lightning staff, staff with branching electricity forks, "
     "yellow-white arcs between prongs, storm caller weapon icon."),
    ("fire_wand", "火焰魔棒",
     "Short fire wand, delicate wooden wand with tiny flame at tip, "
     "red-orange spark trail, fire magic wand icon."),
    ("arcane_orb", "奥术球",
     "Arcane orb, three small blue energy orbs orbiting a larger central orb, "
     "mystical orbiting projectiles, wizard magic icon."),
    ("flame_spray", "火焰喷射器",
     "Flame thrower, tank with nozzle, orange-red flame streaming from barrel, "
     "fire weapon with fuel tank, incendiary icon."),
    ("poison_spray", "毒雾喷射器",
     "Poison sprayer, green chemical tank with spray nozzle, "
     "toxic green mist cloud spraying, chemical weapon icon."),
    ("cold_spray", "冷气喷射器",
     "Cryo sprayer, blue tank with wide nozzle, icy white-blue mist spraying out, "
     "freeze ray, frost weapon, cryogenic spray icon."),

    # --- 医疗 medic × 5 ---
    ("heal_gun", "治愈枪",
     "Healing gun, futuristic medical pistol with green cross symbol, "
     "green glowing chamber, restorative energy weapon icon."),
    ("shield", "圣光盾",
     "Holy shield, golden tower shield with radiant sun emblem, "
     "glowing protective barrier, sacred bulwark icon."),
    ("holy_staff", "圣光杖",
     "Holy staff, golden staff with angel wing ornament and yellow-white holy orb, "
     "divine light radiating, sacred magic weapon icon."),
    ("life_wand", "生命魔棒",
     "Life wand, green vine-wrapped wand with leaf at tip and green sparkles, "
     "nature healing wand, restoration magic icon."),
    ("blessing", "祝福盾",
     "Blessing shield, small round shield with holy cross and soft blue glow, "
     "blessed protector, divine guard icon."),
]

# ====== 全部道具定义 (22+4=26种 from shop.js) ======

ITEMS = [
    ("hpUp", "生命核心",
     "Floating red heart crystal, shiny faceted surface, "
     "pulsing with warm red light, small sparkles around it."),
    ("regen", "再生芯片",
     "Green cross healing icon chip, hexagonal circuit board shape, "
     "green LED glow on the cross center, futuristic medical chip."),
    ("armorUp", "护甲板",
     "Gray shield plate icon, hexagonal armor plate with reinforced edges, "
     "metallic texture with slight orange accent."),
    ("dodgeUp", "闪避模块",
     "Cyan wind swirl motion icon, spinning vortex shape, "
     "light blue wind trails, agility and speed symbol."),
    ("critUp", "暴击目镜",
     "Red crosshair targeting icon, precision scope reticle, "
     "thin red lines with central dot, targeting accuracy symbol."),
    ("critDmg", "暴伤放大器",
     "Orange explosion burst icon, starburst shape radiating from center, "
     "impact force lines, damage multiplier symbol."),
    ("speedUp", "推进器",
     "Yellow lightning bolt speed icon, zigzag lightning shape, "
     "yellow energy crackling, quick movement symbol."),
    ("lifesteal", "吸血模块",
     "Dark red blood droplet icon, glossy droplet shape, "
     "vampiric red glow, life drain symbol."),
    ("rangeUp", "瞄准镜",
     "Gray magnifying glass scope icon, telescope lens with reflection, "
     "extension symbol, increased range indicator."),
    ("harvestUp", "贪婪芯片",
     "Gold coin stack icon, three stacked coins, "
     "golden shiny surface, treasure and wealth symbol."),
    ("pickupUp", "引力场",
     "Purple magnetic field waves icon, concentric wave arcs "
     "expanding outward, attraction symbol."),
    ("luckUp", "幸运星",
     "Golden four-point star icon, sparkling star shape, "
     "gold shine effect, luck and fortune symbol."),
    ("thorn", "荆棘甲",
     "Spiked armor plate with thorny protrusions, "
     "dark green metal with sharp spikes, reactive armor icon."),
    ("energy_shield", "能量盾",
     "Blue transparent hexagonal energy barrier, "
     "sci-fi force field with grid pattern shield icon."),
    ("stim", "兴奋剂",
     "Syringe with glowing orange liquid, "
     "medical stimulant ampoule, energy boost icon."),
    ("ammo_pack", "弹药背包",
     "Military ammo pouch with bullet tips visible, "
     "green canvas backpack with extra ammunition icon."),
    ("replicator", "复制器",
     "Sci-fi device with duplicate projection beams, "
     "holographic cloning machine, duplication technology icon."),
    ("magnet", "磁暴线圈",
     "Electromagnet coil with blue-white magnetic field lines, "
     "tesla coil generating arcs, magnetic force icon."),
    ("piggy", "存钱罐",
     "Cute pink piggy bank with coin slot on top, "
     "gold coin visible inside, savings and interest icon."),
    ("blood_pact", "献血契约",
     "Blood contract scroll with red wax seal and dripping blood, "
     "dark ritual pact, sacrifice for power icon."),
    ("scope", "望远镜",
     "Collapsible brass telescope, "
     "pirate spyglass, long-range viewing instrument icon."),
    ("compression", "压缩靴",
     "Heavy metal boot with compression springs on sides, "
     "speed-enhancing footwear, spring-loaded boot icon."),
    ("armor_piercing_ammo", "穿甲弹",
     "Armor-piercing bullet with tungsten core visible, "
     "dark metal projectile with yellow tip, anti-armor ammo icon."),
    ("burn_spreader", "燃烧扩散器",
     "Flame spreader device with orange fire wave emanating, "
     "fire propagation module, spreading inferno icon."),
    ("ice_core", "极寒之核",
     "Crystalline ice core crystal with deep blue inner glow, "
     "frozen power source, subzero energy core icon."),
    ("element_amp", "元素增幅器",
     "Glowing amplifier device with multicolored elemental rings, "
     "magical focusing lens, elemental power boost icon."),
]

# ====== 全部敌人定义 (6种) ======
ENEMIES = [
    ("basic", "无人机兵",
     "Small flying combat drone, dark gray metal chassis, "
     "four rotor blades, red LED eye, compact and menacing."),
    ("fast", "疾行者",
     "Sleek quadrupedal speedster robot, orange and black, "
     "streamlined cheetah-like body, long legs."),
    ("tank", "重装机兵",
     "Heavy purple armored battle mech, thick plates, "
     "stubby walking tank body, shoulder cannons."),
    ("ranged", "狙击手",
     "Pink sniper machine, one oversized optical eye, "
     "integrated sniper rifle arm, thin legs."),
    ("elite", "精英猎手",
     "Golden elite hunter machine, humanoid upper body on four spider legs, "
     "curved horns, shimmering golden aura, dual energy blade arms."),
    ("boss", "BOSS",
     "Massive crimson boss monster, demonic giant humanoid, "
     "huge curved horns, burning red eyes, energy axe."),
]

# ====== 全部角色定义 (11种) ======
CHARS = [
    ("swordsman", "剑客",
     "Samurai warrior in red samurai armor, black spiky anime hair, "
     "silver katana at hip, stern expression, confident standing pose."),
    ("gunslinger", "枪手",
     "Cowboy gunslinger in long yellow duster coat, wide-brimmed hat, "
     "dual revolvers drawn, action pose, confident smirk."),
    ("fire_mage", "火焰法师",
     "Fire mage in flowing orange and crimson robe, long white hair, "
     "glowing orange eyes, fire orb in hand, magical pose."),
    ("archer", "弓箭游侠",
     "Forest ranger archer in green hooded cloak, "
     "holding compound bow with arrow nocked, focused aiming stare."),
    ("mech", "重型机甲",
     "Bulky humanoid mech robot, dark gray and orange armor plating, "
     "glowing orange optical visor, right arm is heavy cannon."),
    ("assassin", "疾影刺客",
     "Stealthy assassin in purple-black ninja gear, "
     "hood pulled up, face veiled, dual curved daggers in reverse grip, "
     "crouched ready to strike."),
    ("medic", "医疗兵",
     "Military medic in white tactical coat with green cross insignia, "
     "medical goggles pushed up on forehead, healing syringe gun in hand."),
    ("paladin", "圣骑士",
     "Holy knight in gleaming gold and white plate armor, "
     "tower shield with holy crest, longsword at side, flowing cape."),
    ("engineer", "工程师",
     "Tech engineer in blue mechanic jumpsuit with orange stripes, "
     "welding goggles, large wrench, tool belt with gadgets."),
    ("berserker", "狂战士",
     "Massive raging berserker warrior, bare chested with war paint, "
     "blood-red glowing eyes, huge battle axe, fur mantle."),
    ("ranger", "游侠",
     "Dark ranger in black hooded cloak, crossbow in hand, "
     "scarred face, rugged wilderness explorer, survivalist stance."),
]


def submit_prompt(prompt_data):
    """提交提示到 ComfyUI API"""
    data = json.dumps({"prompt": prompt_data}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        return result.get("prompt_id")
    except Exception as e:
        print(f"  FAILED: {e}")
        return None


def wait_for_completion(prompt_id, timeout=90):
    """等待生成完成"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{COMFYUI_URL}/history/{prompt_id}")
            resp = urllib.request.urlopen(req, timeout=5)
            data = json.loads(resp.read())
            if prompt_id in data:
                return data[prompt_id].get("outputs", {})
        except urllib.error.HTTPError:
            pass
        except urllib.error.URLError:
            pass
        time.sleep(1)
    return None


def make_workflow(positive_text, seed=42, prefix="cb_regen"):
    """
    精确匹配 z-image-turbo-workflow.json 子蓝图结构。
    使用 UNETLoader+CLIPLoader+VAELoader 替代 CheckpointLoaderSimple，
    保留子蓝图的全部采样参数 (steps=5, cfg=1.5, euler, simple)。
    """
    return {
        # UNET Loader
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "z_image_turbo_bf16.safetensors",
                "weight_dtype": "default"
            }
        },
        # CLIP Loader
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen_3_4b.safetensors",
                "type": "qwen_image"
            }
        },
        # Empty Latent (512x512)
        "3": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            }
        },
        # Positive Prompt
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive_text,
                "clip": ["2", 0]
            }
        },
        # Negative Prompt
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "3d, photorealistic, realistic, blurry, low quality, ugly, "
                       "deformed, distorted, text, watermark, signature, "
                       "multiple items, multiple characters, messy composition",
                "clip": ["2", 0]
            }
        },
        # KSampler — 匹配子蓝图参数: steps=5, cfg=1.5, euler, scheduler=simple
        "6": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 5,
                "cfg": 1.5,
                "sampler_name": "euler",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["4", 0],
                "negative": ["5", 0],
                "latent_image": ["3", 0]
            }
        },
        # VAE Loader
        "7": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        # VAE Decode
        "8": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["6", 0],
                "vae": ["7", 0]
            }
        },
        # Save Image
        "9": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": prefix,
                "images": ["8", 0]
            }
        },
    }


def generate_category(category_name, items, prefix, style_prompt="", skip_ids=None):
    """生成一类图标，跳过 skip_ids 列表中已有的"""
    if skip_ids is None:
        skip_ids = set()
    filtered = [it for it in items if it[0] not in skip_ids]
    count = len(filtered)
    skipped = len(items) - count
    print(f"\n{'=' * 50}")
    print(f"  [{category_name}] 再生 {count} 个 (跳过 {skipped} 个已存在)...")
    print(f"{'=' * 50}")

    for i, item in enumerate(filtered):
        item_id = item[0]
        item_name = item[1]
        item_desc = item[2]
        seed = 1000 + (hash(item_id) % 900000 + i * 37)

        full_prompt = f"{style_prompt}\n\n{item_desc}"
        prompt_prefix = f"{prefix}_{item_id}"

        print(f"  [{i+1}/{count}] {item_name:<12} ({item_id})...", end=" ", flush=True)

        workflow = make_workflow(full_prompt, seed=seed, prefix=prompt_prefix)
        prompt_id = submit_prompt(workflow)

        if not prompt_id:
            print("FAIL")
            continue

        outputs = wait_for_completion(prompt_id)
        if outputs:
            print("OK")
        else:
            print("TIMEOUT")


def copy_to_assets():
    """复制生成的 PNG 到 assets 目录（取最新的变体）"""
    prefix_to_dir = {
        "cb_regen_weapon": "weapons",
        "cb_regen_item": "items",
        "cb_regen_enemy": "enemies",
        "cb_regen_char": "chars",
    }

    all_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png') and 'cb_regen_' in f]

    from collections import defaultdict
    by_base = defaultdict(list)
    for f in all_files:
        base = f.rsplit('_', 2)[0]
        by_base[base].append(f)

    copied = 0
    for base, files in sorted(by_base.items()):
        matched_dir = None
        for prefix, subdir in prefix_to_dir.items():
            if base.startswith(prefix):
                matched_dir = subdir
                break
        if not matched_dir:
            continue

        files.sort(key=lambda x: int(x.rsplit('_', 2)[1]))
        newest = files[-1]

        # 重命名为 cb_{type}_{id}_00001_.png
        parts = newest.split('_')
        # cb_regen_weapon_frost_00002_.png → cb_weapon_frost_00001_.png
        if len(parts) >= 4 and parts[1] == 'regen':
            new_parts = ['cb', parts[2], parts[3]]
        else:
            continue
        new_name = '_'.join(new_parts) + '_00001_.png'

        src = os.path.join(OUTPUT_DIR, newest)
        dst = os.path.join(ASSETS_DIR, matched_dir, new_name)
        shutil.copy2(src, dst)
        print(f"  [OK] {new_name}  ->  assets/{matched_dir}/")
        copied += 1

    return copied


def get_existing_ids(directory, prefix_pattern):
    """获取 assets 目录下已存在的文件 ID 集合"""
    ids = set()
    path = os.path.join(ASSETS_DIR, directory)
    if not os.path.isdir(path):
        return ids
    for f in os.listdir(path):
        if f.endswith('.png') and prefix_pattern in f:
            # cb_weapon_xxx_00001_.png → xxx
            parts = f.split('_')
            if len(parts) >= 3:
                ids.add(parts[2])
    return ids


def main():
    print("=" * 50)
    print("  CYBER BLADE - Z-Image-Turbo 全面再生 v2")
    print("=" * 50)
    print("  工作流: 匹配 z-image-turbo-workflow.json")
    print("  模型: z_image_turbo_bf16")
    print("  参数: steps=5, cfg=1.5, euler, scheduler=simple, 512x512")
    print(f"  输出: {OUTPUT_DIR}")
    print()

    # 测试连接
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/prompt", method="GET")
        urllib.request.urlopen(req, timeout=5)
        print("  [OK] ComfyUI 连接成功")
    except Exception as e:
        print(f"  [ERR] ComfyUI 连接失败: {e}")
        sys.exit(1)

    # 确保 assets 子目录存在
    for sub in ["weapons", "items", "chars", "enemies"]:
        os.makedirs(os.path.join(ASSETS_DIR, sub), exist_ok=True)

    # 获取已存在的文件 ID (跳过已有的，只再生缺失的)
    existing_weapons = get_existing_ids("weapons", "cb_weapon_")
    existing_items = get_existing_ids("items", "cb_item_")
    existing_enemies = get_existing_ids("enemies", "cb_enemy_")
    existing_chars = get_existing_ids("chars", "cb_char_")

    print(f"  现存: 武器 {len(existing_weapons)} | 道具 {len(existing_items)} | "
          f"敌人 {len(existing_enemies)} | 角色 {len(existing_chars)}")

    # 武器 (45)
    missing_weapons = sum(1 for w in WEAPONS if w[0] not in existing_weapons)
    print(f"  需生成: 武器 {missing_weapons} | 道具 {sum(1 for i in ITEMS if i[0] not in existing_items)} | "
          f"敌人 {sum(1 for e in ENEMIES if e[0] not in existing_enemies)} | "
          f"角色 {sum(1 for c in CHARS if c[0] not in existing_chars)}")
    print()

    # 武器
    generate_category("武器 WEAPONS", WEAPONS, "cb_regen_weapon", GLOBAL_ICON_STYLE, existing_weapons)
    # 道具
    generate_category("道具 ITEMS", ITEMS, "cb_regen_item", GLOBAL_ICON_STYLE, existing_items)
    # 敌人
    generate_category("敌人 ENEMIES", ENEMIES, "cb_regen_enemy", GLOBAL_ENEMY_STYLE, existing_enemies)
    # 角色
    generate_category("角色 CHARS", CHARS, "cb_regen_char", GLOBAL_CHAR_STYLE, existing_chars)

    # 复制到 assets
    print(f"\n{'=' * 50}")
    print(f"  复制到 assets/ 目录...")
    print(f"{'=' * 50}")
    count = copy_to_assets()
    print(f"  完成！共复制/更新 {count} 个文件")

    print(f"\n{'=' * 50}")
    print(f"  [DONE] 再生完成！")
    print(f"  请刷新浏览器 (Ctrl+Shift+R) 检查效果")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
