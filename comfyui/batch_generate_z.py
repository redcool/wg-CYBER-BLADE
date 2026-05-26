#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBER BLADE - Z-Image-Turbo 批量图标生成器 v3
=============================================
v3 改进：统一 sprite 艺术风格
  - 与 sprite sheet 相同的 GLOBAL_STYLE 锚 → 视觉一致性
  - 暗色 (#0d0d24) 背景 → 与游戏主题色匹配（图标直接渲染，不经过色键处理）
  - 7步/CFG2.0 → 更高品质
  - 更详细的武器/道具/角色/敌人描述

模型: z_image_turbo_bf16 (diffusion_models)
CLIP: qwen_3_4b (text_encoders)
VAE: ae (vae)

用法:
  1. 确保 ComfyUI 已启动（默认 http://127.0.0.1:8188）
  2. python batch_generate_z.py

输出:
  - 生成到 ComfyUI/output/ 目录
  - 自动复制到 assets/ 对应子目录
"""

import json
import time
import os
import sys
import shutil
import urllib.request
import urllib.error

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "H:/AI/ComfyUI_windows_portable/ComfyUI/output"
ASSETS_DIR = "H:/ai_works/buffPrj1/assets"

# ====== 全局风格锚（与 sprite sheet 统一） ======
GLOBAL_ICON_STYLE = (
    "CYBER BLADE game icon, bold outlines, saturated flat colors, "
    "cel-shaded, game-ready icon art, same consistent visual style as character sprites, "
    "single centered item filling the frame. "
    "Solid dark #0d0d24 background, NO background gradients, "
    "NO text, NO labels, NO watermark, NO signature."
)

# ====== 武器图标定义 ======

WEAPONS = [
    # ==============================
    # 近战 (melee) × 10
    # ==============================
    ("plasma", "等离子刀",
     "Plasma sword, futuristic energy blade with bright red-hot edge glowing intensely, "
     "black reinforced handle with red accent, blade appears to be pure energy crackling, "
     "isometric angled view, sleek and deadly.",
     200),
    ("axe", "能量斧",
     "Energy axe, broad heavy blade with bright orange luminous edge, "
     "metallic shaft with orange grip tape, axe head glows with heat energy, "
     "angled view showing blade width, powerful brutal weapon.",
     201),
    ("dagger", "双持匕首",
     "Dual daggers crossed in X formation, cyan energy blades, black compact handles, "
     "small sleek thrower style, quick and deadly, "
     "both daggers shown at slight diagonal angle.",
     202),
    ("chainsaw", "链锯剑",
     "Chainsaw sword, long toothed blade like a chainsaw bar, red and dark gray mechanical body, "
     "serrated teeth visible on top edge, engine housing at base, "
     "barbaric brutal weapon design, angled view.",
     203),
    ("sword", "能量剑",
     "Energy sword, curved sweeping blade shape, cyan luminous edge, "
     "elegant silver guard with blue gem, wrapped handle, "
     "classic katana-like silhouette but made of pure energy.",
     204),
    ("katana", "武士刀",
     "Japanese katana, gently curved single-edged blade, silver metallic finish with hamon line, "
     "black wrapped tsuka handle with diamond pattern, square tsuba guard, "
     "traditional elegant weapon design, angled blade-up view.",
     205),
    ("hammer", "重锤",
     "Heavy war hammer, massive rectangular head with orange energy glow on striking surfaces, "
     "thick reinforced metallic shaft, heavy-duty handle, "
     "brutal crushing weapon, angled view showing hammer head size.",
     206),
    ("spear", "能量矛",
     "Energy spear, long shaft with cyan glowing spearhead, "
     "metallic pole with non-slip grip, double-edged energy blade tip, "
     "elegant reaching weapon, vertical angled view.",
     207),
    ("claws", "利爪",
     "Claw gauntlets, three curved razor-sharp cyan blades extending from a wrist base, "
     "metallic gauntlet with blue energy core, blades are retractable looking, "
     "slashing weapon, angled view showing blade curve.",
     208),
    ("whip", "能量鞭",
     "Energy whip, segmented energy links forming a coiled whip shape, "
     "blue glowing segments with electric arcs between joints, "
     "handle with blue gem, sleek elegant design, coiling dynamic pose.",
     209),

    # ==============================
    # 枪械 (gun) × 10
    # ==============================
    ("pistol", "基础手枪",
     "Semi-automatic pistol, compact sleek silver and blue frame, "
     "short barrel, ergonomic grip with texturing, "
     "side profile view, standard issue sidearm.",
     210),
    ("smg", "冲锋枪",
     "Compact submachine gun, short barrel with perforated barrel shroud, "
     "collapsible wire stock, angled magazine, blue and dark gray, "
     "side profile view, rapid fire close quarters weapon.",
     211),
    ("shotgun", "散弹枪",
     "Tactical shotgun, short wide barrel with tube magazine underneath, "
     "pump-action forend, orange accent on receiver, "
     "side profile view, close range devastating firepower.",
     212),
    ("sniper", "狙击枪",
     "Sniper rifle, extremely long barrel with muzzle brake, "
     "high-magnification scope on top, bipod legs folded, green and dark gray, "
     "side profile view, precision long range elimination.",
     213),
    ("gatling", "加特林",
     "Rotary gatling gun, six-barrel rotating assembly, gold and dark metal finish, "
     "large ammo feed mechanism on top, heavy barrel shroud, "
     "front angled view showing all six barrels, suppressive weapon.",
     214),
    ("revolver", "左轮手枪",
     "Six-shooter revolver, swing-out cylinder chamber visible, "
     "silver finish with engraved frame, wooden grip, hammer at rear, "
     "side profile view, classic powerful handgun.",
     215),
    ("rifle", "突击步枪",
     "Assault rifle, medium barrel with flash hider, "
     "detachable box magazine, carry handle on top, cyan and dark gray, "
     "side profile view, versatile all-purpose rifle.",
     216),
    ("shotgun_double", "双管散弹",
     "Double barrel break-action shotgun, two barrels stacked vertically, "
     "exposed hammers, orange and dark wood finish, "
     "front view showing both barrels, classic coach gun style.",
     217),
    ("magnum", "马格南",
     "Large frame magnum revolver, extra-long barrel with vented rib, "
     "large cylinder, silver and black finish, oversized grip for powerful caliber, "
     "side profile view, hand cannon sidearm.",
     218),
    ("minigun", "迷你机枪",
     "Minigun, compact multi-barrel rotary machine gun, "
     "four rotating barrels, gold and dark gray finish, "
     "front angled view showing barrel cluster, portable suppressive fire.",
     219),

    # ==============================
    # 弓箭 (bow) × 10
    # ==============================
    ("bow", "长弓",
     "Traditional longbow, tall curved arc shape, taut bowstring, "
     "polished wood finish with cyan energy shimmer along the limbs, "
     "vertical view, elegant archery weapon.",
     220),
    ("crossbow", "弩",
     "Compound crossbow, horizontal bow assembly mounted on rifle stock, "
     "silver and black, cable system visible, scope mounted on top, "
     "top-down angled view, mechanical bow weapon.",
     221),
    ("longbow", "强弓",
     "Heavy longbow, thick sturdy limbs, green energy glow on limb tips, "
     "reinforced grip, bowstring taut, "
     "vertical view, powerful long-range archery.",
     222),
    ("recurve", "反曲弓",
     "Recurve bow, limb tips curve forward away from archer, "
     "sleek cyan energy limbs, compact central riser with grip, "
     "vertical view, modern high-performance bow design.",
     223),
    ("explosive_arrow", "爆裂箭",
     "Explosive arrow, thick arrow shaft with grenade-like arrowhead, "
     "bright orange tip capsule, warning stripes, fletching at rear, "
     "diagonal pointing-up view, explosive ammunition.",
     224),
    ("frost_arrow", "冰霜箭",
     "Ice arrow, crystalline arrowhead made of blue-white ice shards, "
     "frost-covered shaft, cold mist rising from arrowhead, "
     "diagonal pointing-up view, frozen ammunition.",
     225),
    ("poison_arrow", "毒箭",
     "Poison arrow, green dripping arrowhead, toxic liquid visible, "
     "dark shaft with green spiral warning marks, "
     "diagonal pointing-up view, venomous ammunition.",
     226),
    ("triple_shot", "三连弓",
     "Triple shot bow, unique bow with three parallel arrow grooves on the riser, "
     "three nocking points on bowstring, reinforced limbs for extra power, "
     "vertical view, multi-shot bow design.",
     227),
    ("piercing_shot", "穿甲箭",
     "Armor-piercing arrow, narrow sharp silver tipped arrowhead "
     "with spiral grooves, heavy carbon shaft, stabilizing fins, "
     "diagonal pointing-up view, anti-armor ammunition.",
     228),
    ("homing_bow", "追踪弓",
     "Homing bow, high-tech bow with pink energy targeting reticle "
     "projected above the bow, sleek futuristic limbs, "
     "vertical view with holographic targeting effect.",
     229),

    # ==============================
    # 元素 (magic) × 10
    # ==============================
    ("fire_staff", "火球杖",
     "Fire mage staff, long dark wood staff with a flaming orb "
     "at the top, orange and red flames swirling, molten cracks on orb, "
     "vertical angled view, elemental fire weapon.",
     230),
    ("frost_staff", "冰霜杖",
     "Ice mage staff, crystalline staff with a frozen orb on top, "
     "blue-white ice crystal orb with cold mist radiating, "
     "frost patterns on staff, vertical angled view, ice elemental.",
     231),
    ("thunder_staff", "雷电杖",
     "Thunder mage staff, metallic staff with lightning bolt symbol "
     "at the top, yellow electric arcs crackling between two points, "
     "vertical angled view, lightning elemental.",
     232),
    ("energy_staff", "能量杖",
     "Energy mage staff, sleek metallic staff with spinning purple ring "
     "floating above the tip, purple energy trails, tech-magic hybrid, "
     "vertical angled view, arcane energy weapon.",
     233),
    ("magic_orb", "魔法弹",
     "Floating magic orb, swirling purple energy sphere with "
     "bright core, surrounded by orbiting arcane particles, "
     "centered floating view, pure magical projectile.",
     234),
    ("poison_staff", "毒杖",
     "Poison mage staff, twisted dark staff with skull-topped orb, "
     "green toxic gas leaking from the orb, bubbling green liquid inside, "
     "vertical angled view, poison elemental.",
     235),
    ("void_staff", "虚空杖",
     "Void mage staff, dark staff with miniature black sphere "
     "with purple rim on top, cosmic star-like dots around the void, "
     "vertical angled view, dark matter weapon.",
     236),
    ("lightning_staff", "闪电杖",
     "Lightning mage staff, jagged crystal mounted on metallic staff, "
     "bright yellow-white sparks emitting from crystal, electric field visible, "
     "vertical angled view, lightning elemental variant.",
     237),
    ("fire_wand", "火焰魔棒",
     "Short fire wand, compact wand with flame tip, "
     "red-orange fire burning at the tip, spiral pattern on wand, "
     "angled view, quick spellcasting focus.",
     238),
    ("arcane_orb", "奥术球",
     "Arcane orb, three orbiting energy rings around a central "
     "glowing sphere, rainbow-colored energy trails, "
     "centered floating view, ultimate magic focus.",
     239),

    # ==============================
    # 喷射 (spray) × 3
    # ==============================
    ("flame_spray", "火焰喷射器",
     "Industrial flame thrower, large nozzle with pilot light, "
     "red fuel tank attached, orange and dark metal, "
     "side profile view, area denial fire weapon.",
     240),
    ("poison_spray", "毒雾喷射器",
     "Chemical spray gun, wide nozzle with green residue, "
     "green toxic liquid tank, hose connecting tank to gun, "
     "side profile view, chemical weapon sprayer.",
     241),
    ("cold_spray", "冷气喷射器",
     "Cryogenic spray gun, insulated nozzle with ice crystal buildup, "
     "blue-white cold tank, frost covering parts of the gun, "
     "side profile view, freezing spray weapon.",
     242),

    # ==============================
    # 医疗 (medic) × 5
    # ==============================
    ("heal_gun", "治愈枪",
     "Syringe-shaped healing gun, green cross symbol on side, "
     "green translucent liquid visible in chamber, white and green finish, "
     "side profile view, restorative support tool.",
     243),
    ("shield", "圣光盾",
     "Holy shield, round shield with golden glowing cross emblem, "
     "polished metallic rim, golden white light radiating, "
     "front-facing view, protective barrier.",
     244),
    ("holy_staff", "圣光杖",
     "Holy staff, tall staff with angel wing shaped crest on top, "
     "golden and white finish, light beam emanating upward, "
     "vertical angled view, divine support weapon.",
     245),
    ("life_wand", "生命魔棒",
     "Life wand, delicate wand with green leaf-shaped tip, "
     "emerald green glow, vine patterns wrapping around the wand, "
     "angled view, nature healing focus.",
     246),
    ("blessing", "祝福盾",
     "Blessing shield, diamond-shaped kite shield, "
     "white-gold metallic finish with blue gem center, "
     "radiant light effect around edges, front-facing view.",
     247),
]

ITEMS = [
    # === 原有 12 种 ===
    ("hpUp", "生命核心",
     "Floating red heart crystal, shiny faceted surface, "
     "pulsing with warm red light, small sparkles around it.",
     300),
    ("regen", "再生芯片",
     "Green cross healing icon chip, hexagonal circuit board shape, "
     "green LED glow on the cross center, futuristic medical chip.",
     301),
    ("armorUp", "护甲板",
     "Gray shield plate icon, hexagonal armor plate with reinforced "
     "edges, metallic texture with slight orange accent.",
     302),
    ("dodgeUp", "闪避模块",
     "Cyan wind swirl motion icon, spinning vortex shape, "
     "light blue wind trails, agility and speed symbol.",
     303),
    ("critUp", "暴击镜",
     "Red crosshair targeting icon, precision scope reticle, "
     "thin red lines with central dot, targeting accuracy symbol.",
     304),
    ("critDmg", "暴击增幅",
     "Orange explosion burst icon, starburst shape radiating from "
     "center, impact force lines, damage symbol.",
     305),
    ("speedUp", "速度增幅",
     "Yellow lightning bolt speed icon, zigzag lightning shape, "
     "yellow energy crackling, quick movement symbol.",
     306),
    ("lifesteal", "生命偷取",
     "Dark red blood droplet icon, glossy droplet shape, "
     "vampiric red glow, life drain symbol.",
     307),
    ("rangeUp", "射程镜",
     "Gray magnifying glass scope icon, telescope lens with reflection, "
     "extension symbol, increased range indicator.",
     308),
    ("harvestUp", "采集增幅",
     "Gold coin stack icon, three stacked coins, "
     "golden shiny surface, treasure and wealth symbol.",
     309),
    ("pickupUp", "拾取范围",
     "Purple magnetic field waves icon, concentric wave arcs "
     "expanding outward, attraction symbol.",
     310),
    ("luckUp", "幸运星",
     "Golden four-point star icon, sparkling star shape, "
     "gold shine effect, luck and fortune symbol.",
     311),

    # === 新增 10 种 ===
    ("thorn", "荆棘甲",
     "Spiky thorny armor plate, green thorns protruding from "
     "metallic base, defensive spikes, retribution armor.",
     312),
    ("energy_shield", "能量盾",
     "Blue energy shield icon, hexagonal honeycomb pattern, "
     "translucent blue barrier, protective force field.",
     313),
    ("stim", "兴奋剂",
     "Syringe stim pack, green liquid in transparent chamber, "
     "plunger partially depressed, chemical stimulant.",
     314),
    ("ammo_pack", "弹药背包",
     "Military ammo backpack, olive drab bag with bullet belt "
     "across the front, ammunition symbol.",
     315),
    ("replicator", "复制器",
     "Purple replicator cube, 3D cube with duplicate symbol, "
     "holographic edges, duplication technology.",
     316),
    ("magnet", "磁暴线圈",
     "Purple magnetic coil, Tesla coil shape with lightning arcs "
     "between rings, electricity attraction symbol.",
     317),
    ("piggy", "存钱罐",
     "Golden piggy bank, cute pig shape with coin slot on top, "
     "gold coin partially inserted, savings symbol.",
     318),
    ("blood_pact", "献血契约",
     "Dark red blood pact scroll, rolled parchment with dripping "
     "blood droplets, seal stamp on bottom, sacrifice symbol.",
     319),
    ("scope", "望远镜",
     "Silver telescope scope, collapsible brass and silver telescope, "
     "lens reflection on objective, observation equipment.",
     320),
    ("compression", "压缩靴",
     "Heavy compression boots, thick metallic boots with spring "
     "coils on bottom, weight and force symbol.",
     321),

    # === 新增 4 种战斗道具 ===
    ("armor_piercing_ammo", "穿甲弹",
     "Armor piercing bullet, silver pointed tip with spiral grooves, "
     "brass casing, sleek deadly projectile.",
     322),
    ("burn_spreader", "燃烧扩散器",
     "Burn spreader device, mechanical gadget with orange flame wave "
     "expanding outward from center, heat haze effect.",
     323),
    ("ice_core", "极寒之核",
     "Ice core crystal, blue-white frozen shard with cold mist "
     "radiating from it, sharp crystal facets, absolute zero energy.",
     324),
    ("element_amp", "元素增幅器",
     "Element amplifier, purple glowing orb surrounded by four "
     "elemental symbols floating in orbit, mystical amplifier.",
     325),
]

CHARS = [
    # ======== 默认解锁 (4个) ========
    ("swordsman", "剑客",
     "Swordsman character portrait, samurai warrior in red armor, "
     "black spiky anime hair, stern focused expression, "
     "katana over shoulder, confident battle stance.",
     400),
    ("gunslinger", "枪手",
     "Gunslinger character portrait, cowboy in yellow duster coat, "
     "wide-brimmed hat, dual revolvers drawn, action pose.",
     401),
    ("fire_mage", "火焰法师",
     "Fire mage character portrait, hooded figure casting fire spell, "
     "fire orb in one hand, orange and crimson robe, glowing eyes.",
     402),
    ("archer", "弓箭游侠",
     "Archer character portrait, hooded ranger in green cloak, "
     "holding compound bow with arrow nocked, focused aiming stare.",
     403),
    # ======== 解锁角色 (6个) ========
    ("mech", "重型机甲",
     "Mech robot portrait, bulky armored war machine, "
     "orange glowing optics, heavy cannon arm, intimidating stance.",
     404),
    ("assassin", "疾影刺客",
     "Assassin portrait, dark stealthy figure in purple-black gear, "
     "dual curved daggers in reverse grip, crouched ready to strike.",
     405),
    ("medic", "医疗兵",
     "Medic portrait, battle medic in white tactical coat, "
     "healing syringe gun in hand, green cross visible, calm professional look.",
     406),
    ("paladin", "圣骑士",
     "Paladin portrait, holy knight in golden-white plate armor, "
     "tower shield with cross emblem, sword raised in blessing.",
     407),
    ("engineer", "工程师",
     "Engineer portrait, tech mechanic in blue jumpsuit, "
     "welding goggles, wrench in hand, surrounded by holographic blueprints.",
     408),
    ("berserker", "狂战士",
     "Berserker portrait, raging warrior with red glowing eyes, "
     "massive battle axe, muscular build, bloodthirsty roar expression.",
     409),
]

ENEMIES = [
    ("basic", "无人机兵",
     "Small flying combat drone, dark gray metal chassis, "
     "four rotor blades, red LED eye, compact and menacing.",
     500),
    ("fast", "疾行者",
     "Sleek quadrupedal speedster robot, orange and black, "
     "streamlined cheetah-like body, long legs, fast attack posture.",
     501),
    ("tank", "重装机兵",
     "Heavy purple armored battle mech, thick plates, "
     "stubby walking tank body, shoulder cannons, unstoppable force.",
     502),
    ("ranged", "狙击手",
     "Pink sniper machine, one oversized optical eye, "
     "integrated sniper rifle arm, long thin legs, precision killer.",
     503),
    ("elite", "精英猎手",
     "Gold elite hunter machine, humanoid upper body on spider legs, "
     "curved horns, dual energy blades, glowing gold core.",
     504),
    ("boss", "BOSS",
     "Massive crimson boss monster, demonic giant humanoid, "
     "huge curved horns, burning red eyes, energy axe, devastating presence.",
     505),
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


def wait_for_completion(prompt_id, timeout=120):
    """等待 ComfyUI 生成完成"""
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


def make_prompt(positive_text, seed=42, prefix="cb"):
    """
    构建 Z-Image-Turbo 工作流提示
    v3: 7 steps, CFG 2.0, 品红背景（与 sprite 统一）
    """
    return {
        # 1: UNETLoader - loads z_image_turbo_bf16
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "z_image_turbo_bf16.safetensors",
                "weight_dtype": "default"
            }
        },
        # 2: ModelSamplingAuraFlow - shift=3 refinement
        "2": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {
                "model": ["1", 0],
                "shift": 3.0
            }
        },
        # 3: CLIPLoader - loads qwen_3_4b
        "3": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen_3_4b.safetensors",
                "type": "qwen_image"
            }
        },
        # 4: EmptySD3LatentImage - 512x512 latent
        "4": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            }
        },
        # 5: CLIPTextEncode - positive prompt (sprite style)
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": f"{GLOBAL_ICON_STYLE}\n\n{positive_text}",
                "clip": ["3", 0]
            }
        },
        # 6: CLIPTextEncode - negative prompt
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": (
                    "3d, photorealistic, realistic, blurry, low quality, ugly, "
                    "deformed, distorted, text, watermark, signature, complex, messy, "
                    "realistic human, cluttered, noisy, dark gothic, horror, scary, "
                    "photoreal, oil painting, background gradients, multi-colored background, "
                    "multiple items, shadow under item, crossed edges"
                ),
                "clip": ["3", 0]
            }
        },
        # 7: ConditioningZeroOut - zero out negative conditioning
        "7": {
            "class_type": "ConditioningZeroOut",
            "inputs": {
                "conditioning": ["6", 0]
            }
        },
        # 8: KSampler - generate
        "8": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 7,
                "cfg": 2.0,
                "sampler_name": "res_multistep",
                "scheduler": "simple",
                "denoise": 1.0,
                "model": ["2", 0],
                "positive": ["5", 0],
                "negative": ["7", 0],
                "latent_image": ["4", 0]
            }
        },
        # 9: VAELoader - loads ae VAE
        "9": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        # 10: VAEDecode - decode latent to image
        "10": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["9", 0]
            }
        },
        # 11: SaveImage - save to output
        "11": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": prefix,
                "images": ["10", 0]
            }
        },
    }


def generate_category(category_name, items, prefix):
    """生成一类图标"""
    count = len(items)
    print(f"\n{'=' * 55}")
    print(f"  [{category_name}] 正在生成 {count} 个图标...")
    print(f"{'=' * 55}")

    for i, item in enumerate(items):
        item_id = item[0]
        item_name = item[1]
        item_desc = item[2]
        # Use per-item seed if available, otherwise derive from index
        item_seed = item[3] if len(item) > 3 else (42 + i * 7)
        prompt_prefix = f"{prefix}_{item_id}"

        print(f"  [{i+1}/{count}] {item_name:<12} ({item_id})...", end=" ", flush=True)

        prompt = make_prompt(item_desc, seed=item_seed, prefix=prompt_prefix)
        prompt_id = submit_prompt(prompt)

        if not prompt_id:
            print("FAIL")
            continue

        outputs = wait_for_completion(prompt_id)
        if outputs:
            print("OK")
        else:
            print("TIMEOUT")


def main():
    print("=" * 55)
    print("  CYBER BLADE - Z-Image-Turbo 批量图标生成器 v3")
    print("=" * 55)
    print("  模型: z_image_turbo_bf16 (UNET)")
    print("  CLIP: qwen_3_4b | VAE: ae")
    print("  参数: 7步, CFG 2.0, 512x512, res_multistep, 暗色背景")
    print("  风格: 与 sprite sheet 统一 — CYBER BLADE 风格")
    print(f"  输出: {OUTPUT_DIR}")
    print(f"  资产: {ASSETS_DIR}")
    print()

    # 测试连接
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/prompt", method="GET")
        urllib.request.urlopen(req, timeout=5)
        print("  [OK] ComfyUI 连接成功")
    except Exception as e:
        print(f"  [ERR] ComfyUI 连接失败: {e}")
        print("  请先启动 ComfyUI，再运行此脚本")
        sys.exit(1)

    # 确保 assets 子目录存在
    for sub in ["weapons", "items", "chars", "enemies"]:
        os.makedirs(os.path.join(ASSETS_DIR, sub), exist_ok=True)

    # 映射前缀到目标子目录
    prefix_to_dir = {
        "cb_weapon": "weapons",
        "cb_item": "items",
        "cb_char": "chars",
        "cb_enemy": "enemies",
    }

    generate_category("武器 WEAPONS", WEAPONS, "cb_weapon")
    generate_category("道具 ITEMS", ITEMS, "cb_item")
    generate_category("角色 CHARACTERS", CHARS, "cb_char")
    generate_category("敌人 ENEMIES", ENEMIES, "cb_enemy")

    print(f"\n{'=' * 55}")
    print(f"  正在复制到 assets/ 目录 (仅最高变体)...")
    print(f"{'=' * 55}")

    # 读取 ComfyUI output 中的所有 PNG
    all_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')]

    # 按基础名分组 (cb_weapon_pistol_00001_ -> 组: cb_weapon_pistol)
    from collections import defaultdict
    by_base = defaultdict(list)
    for f in all_files:
        base = f.rsplit('_', 2)[0]
        by_base[base].append(f)

    copied = 0
    for base, files in sorted(by_base.items()):
        # 只看我们关心的前缀
        matched_dir = None
        for prefix, subdir in prefix_to_dir.items():
            if base.startswith(prefix):
                matched_dir = subdir
                break
        if not matched_dir:
            continue

        # 取最高计数变体 (最新生成的)
        files.sort(key=lambda x: int(x.rsplit('_', 2)[1]))
        newest = files[-1]

        # 重命名为 _00001_
        parts = newest.rsplit('_', 2)
        new_name = f'{parts[0]}_00001_.png'

        src = os.path.join(OUTPUT_DIR, newest)
        dst = os.path.join(ASSETS_DIR, matched_dir, new_name)
        shutil.copy2(src, dst)
        print(f"  [OK] {new_name}  ->  assets/{matched_dir}/")
        copied += 1

    print(f"\n{'=' * 55}")
    print(f"  [DONE] 完成！共生成并复制 {copied} 个图标（每个取最新变体）")
    print(f"  风格统一: CYBER BLADE bold outlines + cel-shaded + 暗色背景")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
