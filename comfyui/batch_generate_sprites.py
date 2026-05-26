#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBER BLADE - Z-Image-Turbo Sprite Sheet 生成器 v2
=================================================
生成 2x2 待机动画 sprite sheet（1024x1024，4帧/每个角色）
v2 改进：
  - 品红 (#FF00FF) 背景 → 适配 agent-sprite-forge 色键处理
  - 7步/CFG2.0 → 更高品质
  - 统一全局风格锚 → 所有 sprite 视觉一致性
  - 更详细的角色/敌人 prompt

模型: z_image_turbo_bf16 (diffusion_models)
CLIP: qwen_3_4b (text_encoders)
VAE: ae (vae)

用法:
  1. 确保 ComfyUI 已启动（默认 http://127.0.0.1:8188）
  2. python batch_generate_sprites.py

输出:
  - ComfyUI/output/ 下生成 cb_sprite_*.png
  - 自动复制到 assets/sprites/ 对应子目录
  - 自动用 agent-sprite-forge 处理器分割成独立帧
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

# ====== 全局风格锚 ======
GLOBAL_STYLE = (
    "CYBER BLADE top-down 2D game character sprite, bold outlines, "
    "saturated flat colors, cel-shaded, game-ready sprite art, "
    "consistent visual style, same art direction across all frames. "
    "4 cells in 2x2 grid, SAME character in ALL 4 cells, "
    "SAME bounding box, SAME pixel scale, SAME facing direction. "
    "Solid magenta #FF00FF background, NO background gradients, "
    "NO text, NO labels, NO borders between cells."
)

# ====== 行走方向 Sprite 全局风格锚（4x4 grid，4方向×4帧） ======
WALK_STYLE = (
    "CYBER BLADE top-down 2D game character sprite, bold outlines, "
    "saturated flat colors, cel-shaded, game-ready sprite art, "
    "consistent visual style, same art direction across all frames. "
    "16 cells in a 4x4 grid: 4 rows (DOWN, LEFT, RIGHT, UP) × 4 columns (walk frames). "
    "IDENTICAL character height and width in ALL 16 cells — same bounding box, same pixel scale. "
    "No zooming or cropping differently between cells. "
    "Character is CENTERED in each cell, fills ~60% of cell. "
    "Solid magenta #FF00FF background, NO gradients, "
    "NO text, NO labels, NO borders between cells, "
    "NO limbs or parts crossing cell edges."
)

# ====== Sprite Sheet 定义 ======

CHAR_SPRITES = [
    ("swordsman", "剑客",
     "Samurai warrior in red samurai armor with silver katana at hip. "
     "Black spiky anime hair, stern expression, red haori jacket over white kimono. "
     "Frame 1: idle standing, hand on katana hilt, relaxed but alert. "
     "Frame 2: subtle breathing, chest rises, armor plates shift slightly. "
     "Frame 3: weight shift onto back foot, shoulder drops, katana adjusts. "
     "Frame 4: idle accent — katana hilt twitch, head tilts slightly, "
     "readiest pose before returning to frame 1.",
     42),
    ("gunslinger", "枪手",
     "Cowboy gunslinger in long yellow duster coat, wide-brimmed brown hat, "
     "leather boots. Dual silver revolvers holstered at both hips. "
     "Sunglasses, confident smirk. "
     "Frame 1: idle standing with hands near holsters. "
     "Frame 2: alert posture, knees slightly bent, hands hovering over guns. "
     "Frame 3: slight crouch, coat flares out, gunfighter stance. "
     "Frame 4: idle accent — spins right revolver, catches it, returns to holster.",
     43),
    ("fire_mage", "火焰法师",
     "Fire mage in flowing orange and crimson robe with gold trim. "
     "Hood down, long white hair, glowing orange eyes. "
     "Left hand holds a floating fire orb, right hand at side. "
     "Frame 1: idle standing, fire orb steadily floating. "
     "Frame 2: flame flicker intensifies, orb grows slightly brighter. "
     "Frame 3: robe sways as if caught in heat updraft, orb pulse. "
     "Frame 4: fire pulse accent — orb expands, sparks trail, flame wave radiates.",
     44),
    ("archer", "弓箭游侠",
     "Forest ranger archer in green hooded cloak over brown leather armor. "
     "Long compound bow held in left hand, quiver of arrows on back. "
     "Mask pulled down, stern focused eyes. "
     "Frame 1: idle, bow held diagonally down, relaxed grip. "
     "Frame 2: reaches back to check arrows in quiver, head turns. "
     "Frame 3: pulls bowstring slightly to test tension, arms flex. "
     "Frame 4: idle accent — nocks invisible arrow, aims briefly, lowers bow.",
     45),
    ("mech", "重型机甲",
     "Bulky humanoid mech robot, dark gray and orange armor plating. "
     "Glowing orange optical visor for eyes. "
     "Right arm is a heavy cannon, left arm is a claw. "
     "Hydraulic pistons visible on legs, energy cables on torso. "
     "Frame 1: idle standing, cannon pointed down, heavy stance. "
     "Frame 2: hydraulics shift — torso rises slightly, vents open. "
     "Frame 3: cannon arm twitches, targeting sensors activate, claw flexes. "
     "Frame 4: energy core pulse — orange glow brightens in chest, vents steam.",
     46),
    ("assassin", "疾影刺客",
     "Stealthy assassin in tight-fitting purple and black ninja outfit. "
     "Hood pulled up, face obscured by dark veil. "
     "Dual curved daggers held in reverse grip. "
     "Lean athletic build, crouched posture. "
     "Frame 1: idle crouched, daggers crossed in front, low stance. "
     "Frame 2: shifts weight to left foot, right blade rotates. "
     "Frame 3: blade glint — both daggers catch light, ready to strike. "
     "Frame 4: ready stance — legs wider, daggers pulled back, explosive posture.",
     47),
    ("medic", "医疗兵",
     "Military medic in white tactical coat with green cross insignia. "
     "Medical goggles pushed up on forehead. "
     "Large healing syringe gun in right hand. "
     "Medical pouches on belt, red cross armband. "
     "Frame 1: idle holding syringe gun at ready, calm posture. "
     "Frame 2: checking handheld medical scanner, looking down. "
     "Frame 3: looking around alertly, syringe gun raised slightly. "
     "Frame 4: ready to heal — injector primed, stance wide, supportive pose.",
     48),
    ("paladin", "圣骑士",
     "Holy knight in gleaming gold and white plate armor. "
     "Tower shield in left hand with holy crest emblem. "
     "Longsword in right hand, blade pointed down. "
     "Helmet with golden visor, flowing white cape. "
     "Frame 1: idle, shield raised slightly, sword down, guardian stance. "
     "Frame 2: prayer stance — head bows, sword held vertically, holy light glows. "
     "Frame 3: shield shifts forward, feet adjust for weight, cape settles. "
     "Frame 4: sword salute accent — raises blade to visor, holy gleam, returns.",
     49),
    ("engineer", "工程师",
     "Tech engineer in blue mechanic jumpsuit with orange safety stripes. "
     "Welding goggles pulled down over eyes. "
     "Large wrench in right hand, tool belt with gadgets. "
     "Holstered plasma welder on thigh. "
     "Frame 1: idle with wrench resting on shoulder, casual confident pose. "
     "Frame 2: adjusts welding goggles, pushes them up, examines surroundings. "
     "Frame 3: checks tool belt, pats holster, counts equipment. "
     "Frame 4: ready with welder — draws plasma welder, aims, stance wide.",
     50),
    ("berserker", "狂战士",
     "Massive raging berserker warrior, bare chested with war paint. "
     "Blood-red eyes glowing with fury, veins bulging. "
     "Huge double-bladed battle axe in both hands. "
     "Fur mantle over shoulders, leather and iron pants. "
     "Frame 1: idle aggressive stance — axe held wide, teeth bared. "
     "Frame 2: muscle flex, blood aura pulses around body, eyes flare. "
     "Frame 3: axe swing anticipation — pulls axe back, torque in torso. "
     "Frame 4: roar idle accent — throws head back, roars, ground tremor effect.",
     51),
]

# ====== 4方向待机 Sprite Sheet 定义（4x4：4方向×4帧，带 idle- 前缀输出） ======

CHAR_IDLE_DIR_SPRITES = [
    ("swordsman", "剑客",
     "Samurai warrior in red samurai armor with silver katana at hip. "
     "Black spiky anime hair, stern expression, red haori jacket over white kimono. "
     "LAYOUT: Row1=DOWN (toward camera), Row2=LEFT, Row3=RIGHT, Row4=UP (away). "
     "Each row: C1=relaxed standing, C2=subtle breathing, C3=weight shift, C4=ready accent. "
     "Katana stays at hip in all frames. SAME bounding box, SAME pixel scale in all 16 cells. "
     "Character is CENTERED in each cell, fills ~60% of cell.",
     542),
    ("gunslinger", "枪手",
     "Cowboy gunslinger in long yellow duster coat, wide-brimmed brown hat, "
     "leather boots. Dual silver revolvers holstered at both hips. "
     "Sunglasses, confident smirk. "
     "LAYOUT: Row1=DOWN (toward camera), Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=relaxed standing, C2=alert posture, C3=weight shift, C4=casual accent. "
     "Revolvers stay holstered. SAME bounding box in all 16 cells.",
     543),
    ("fire_mage", "火焰法师",
     "Fire mage in flowing orange and crimson robe with gold trim. "
     "Hood down, long white hair, glowing orange eyes. "
     "Left hand holds a floating fire orb, right hand at side. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=idle standing, C2=flame flicker, C3=robe sways, C4=fire pulse. "
     "Fire orb floats in left hand. SAME bounding box in all 16 cells.",
     544),
    ("archer", "弓箭游侠",
     "Forest ranger archer in green hooded cloak over brown leather armor. "
     "Long compound bow held in left hand, quiver of arrows on back. "
     "Mask pulled down, stern focused eyes. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=idle standing, C2=check quiver, C3=bow test, C4=nock accent. "
     "Bow held in left hand. SAME bounding box in all 16 cells.",
     545),
    ("mech", "重型机甲",
     "Bulky humanoid mech robot, dark gray and orange armor plating. "
     "Glowing orange optical visor for eyes. "
     "Right arm is a heavy cannon, left arm is a claw. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=idle standing, C2=hydraulics shift, C3=cannon twitch, C4=core pulse. "
     "Heavy stance. SAME bounding box in all 16 cells.",
     546),
    ("assassin", "疾影刺客",
     "Stealthy assassin in tight-fitting purple and black ninja outfit. "
     "Hood pulled up, face obscured by dark veil. "
     "Dual curved daggers held in reverse grip. "
     "Lean athletic build, crouched posture. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=crouched idle, C2=weight shift, C3=blade glint, C4=ready stance. "
     "Daggers in reverse grip. SAME bounding box in all 16 cells.",
     547),
    ("medic", "医疗兵",
     "Military medic in white tactical coat with green cross insignia. "
     "Medical goggles pushed up on forehead. "
     "Large healing syringe gun in right hand. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=idle holding syringe gun, C2=check scanner, C3=alert look, C4=ready to heal. "
     "Syringe gun held at ready. SAME bounding box in all 16 cells.",
     548),
    ("paladin", "圣骑士",
     "Holy knight in gleaming gold and white plate armor. "
     "Tower shield in left hand with holy crest emblem. "
     "Longsword in right hand, blade pointed down. "
     "Helmet with golden visor, flowing white cape. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=idle guardian, C2=prayer stance, C3=shield shift, C4=sword salute. "
     "Shield forward, sword at side. SAME bounding box in all 16 cells.",
     549),
    ("engineer", "工程师",
     "Tech engineer in blue mechanic jumpsuit with orange safety stripes. "
     "Welding goggles pulled down over eyes. "
     "Large wrench in right hand, tool belt with gadgets. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=idle wrench on shoulder, C2=adjust goggles, C3=check tools, C4=ready stance. "
     "Wrench on shoulder. SAME bounding box in all 16 cells.",
     550),
    ("berserker", "狂战士",
     "Massive raging berserker warrior, bare chested with war paint. "
     "Blood-red eyes glowing with fury, veins bulging. "
     "Huge double-bladed battle axe in both hands. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=idle aggressive, C2=muscle flex aura, C3=axe anticipation, C4=roar accent. "
     "Axe held wide. SAME bounding box in all 16 cells.",
     551),
]

# ====== 行走方向 Sprite Sheet 定义（4x4：4方向×4帧） ======

CHAR_WALK_SPRITES = [
    ("swordsman", "剑客",
     "Samurai warrior in red samurai armor with silver katana at hip. "
     "Black spiky anime hair, stern expression, red haori jacket over white kimono. "
     "LAYOUT: Row1=DOWN (toward camera), Row2=LEFT, Row3=RIGHT, Row4=UP (away). "
     "Each row: C1=neutral feet together, C2=LEFT foot steps forward, "
     "C3=neutral again, C4=RIGHT foot steps forward. "
     "Katana stays at hip in all frames. Head/torso orientation changes by row direction. "
     "Character fills ~60% of each cell, identically sized in all 16 cells.",
     242),
    ("gunslinger", "枪手",
     "Cowboy gunslinger in long yellow duster coat, wide-brimmed brown hat, "
     "leather boots. Dual silver revolvers holstered at both hips. "
     "Sunglasses, confident smirk. "
     "LAYOUT: Row1=DOWN (toward camera), Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=LEFT foot forward, C3=neutral, C4=RIGHT foot forward. "
     "Revolvers stay holstered in all frames. Head/torso orientation changes per row direction. "
     "Identically sized in all 16 cells.",
     243),
    ("fire_mage", "火焰法师",
     "Fire mage in flowing orange and crimson robe with gold trim. "
     "Hood down, long white hair, glowing orange eyes. "
     "Left hand holds a floating fire orb, right hand at side. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Fire orb floats in left hand in all frames. Robe sways slightly with movement. "
     "Identically sized in all 16 cells.",
     244),
    ("archer", "弓箭游侠",
     "Forest ranger archer in green hooded cloak over brown leather armor. "
     "Long compound bow held in left hand, quiver of arrows on back. "
     "Mask pulled down, stern focused eyes. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Bow held in left hand in all frames, orientation adjusts per row. "
     "Identically sized in all 16 cells.",
     245),
    ("mech", "重型机甲",
     "Bulky humanoid mech robot, dark gray and orange armor plating. "
     "Glowing orange optical visor for eyes. "
     "Right arm is a heavy cannon, left arm is a claw. "
     "Hydraulic pistons visible on legs, energy cables on torso. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Cannon and claw arms stay in same position. Heavy stomping walk. "
     "Identically sized in all 16 cells.",
     246),
    ("assassin", "疾影刺客",
     "Stealthy assassin in tight-fitting purple and black ninja outfit. "
     "Hood pulled up, face obscured by dark veil. "
     "Dual curved daggers held in reverse grip. "
     "Lean athletic build, crouched posture. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Daggers in reverse grip in all frames. Crouched ninja walk. "
     "Identically sized in all 16 cells.",
     247),
    ("medic", "医疗兵",
     "Military medic in white tactical coat with green cross insignia. "
     "Medical goggles pushed up on forehead. "
     "Large healing syringe gun in right hand. "
     "Medical pouches on belt, red cross armband. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Syringe gun held at ready in all frames. Medical coat sways. "
     "Identically sized in all 16 cells.",
     248),
    ("paladin", "圣骑士",
     "Holy knight in gleaming gold and white plate armor. "
     "Tower shield in left hand with holy crest emblem. "
     "Longsword in right hand, blade pointed down. "
     "Helmet with golden visor, flowing white cape. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Shield forward, sword at side in all frames. Heavy knightly walk. "
     "Cape flows behind, orientation adjusts per row direction. "
     "Identically sized in all 16 cells.",
     249),
    ("engineer", "工程师",
     "Tech engineer in blue mechanic jumpsuit with orange safety stripes. "
     "Welding goggles pulled down over eyes. "
     "Large wrench in right hand, tool belt with gadgets. "
     "Holstered plasma welder on thigh. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Wrench on shoulder in all frames. Tool belt bounces with steps. "
     "Identically sized in all 16 cells.",
     250),
    ("berserker", "狂战士",
     "Massive raging berserker warrior, bare chested with war paint. "
     "Blood-red eyes glowing with fury, veins bulging. "
     "Huge double-bladed battle axe in both hands. "
     "Fur mantle over shoulders, leather and iron pants. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Axe held wide in both hands in all frames. Heavy aggressive walk. "
     "Fur mantle bounces. Identically sized in all 16 cells.",
     251),
]

ENEMY_WALK_SPRITES = [
    ("basic", "无人机兵",
     "Small flying robot drone, dark gray metal body with red LED eyes. "
     "Four small rotor blades on top, single searchlight on bottom. "
     "Compact chassis, antenna on top. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=hover neutral, C2=drift forward, C3=hover neutral, C4=drift backward. "
     "Rotors spin in all frames. Searchlight orientation changes per row. "
     "Identically sized in all 16 cells.",
     300),
    ("fast", "疾行者",
     "Sleek quadrupedal speedster robot, orange and black chassis. "
     "Streamlined body like a mechanical cheetah, long wheelbase. "
     "Four thin powerful legs with clawed feet. "
     "Single yellow optic scanner on a streamlined head. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral stride, C2=front legs extend, C3=neutral, C4=rear legs push. "
     "Body stays streamlined in all frames. Scanner orientation changes per row. "
     "Identically sized in all 16 cells.",
     301),
    ("tank", "重装机兵",
     "Heavy purple armored battle mech, thick reinforced plating. "
     "Short wide stubby body like a walking tank. "
     "Two massive tread-like feet, shoulder-mounted cannons. "
     "Single red visor slit, exhaust vents on back. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=tread LEFT forward, C3=neutral, C4=tread RIGHT forward. "
     "Cannons stay level. Heavy stomping walk. "
     "Identically sized in all 16 cells.",
     302),
    ("ranged", "狙击手",
     "Pink bi-pedal sniper machine, one oversized optical targeting eye. "
     "Long barrel sniper rifle integrated into right arm. "
     "Thin insect-like legs, radar dish on back. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Sniper rifle arm stays aimed down. Insect-like scuttling walk. "
     "Identically sized in all 16 cells.",
     303),
    ("elite", "精英猎手",
     "Golden elite hunter machine, humanoid upper body on four spider legs. "
     "Two curved horns on head, golden aura shimmering. "
     "Dual energy blades as arms. "
     "Chest has a glowing golden core. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=stride LEFT, C3=neutral, C4=stride RIGHT. "
     "Four spider legs move in alternating pairs. Energy blades stay crossed. "
     "Identically sized in all 16 cells.",
     304),
    ("boss", "BOSS",
     "Massive crimson boss monster — giant humanoid with demonic features. "
     "Two large curved horns, burning red eyes, fanged maw. "
     "Muscular body with dark red skin, black armor plates on shoulders. "
     "Huge energy axe in right hand, left hand crackling with red lightning. "
     "LAYOUT: Row1=DOWN, Row2=LEFT, Row3=RIGHT, Row4=UP. "
     "Each row: C1=neutral, C2=step LEFT, C3=neutral, C4=step RIGHT. "
     "Energy axe held ready in all frames. Heavy ground-shaking walk. "
     "Identically sized in all 16 cells.",
     305),
]

# ====== 攻击动画 Sprite Sheet 定义 ======

CHAR_ATTACK_SPRITES = [
    ("swordsman", "剑客",
     "Samurai warrior in red samurai armor with silver katana. "
     "Black spiky anime hair, red haori jacket over white kimono. "
     "Frame 1: ATTACK WIND-UP — katana drawn back above head, both hands on handle, "
     "body twisting for power, knees bent, eyes locked forward. "
     "Frame 2: ATTACK STRIKE — katana swung diagonally downward, blade mid-swing with "
     "motion lines, body leaning into the strike, momentum forward. "
     "Frame 3: ATTACK FOLLOW-THROUGH — katana at lowest point of swing arc, "
     "body rotated fully into the cut, arms extended, blade pointing down-right. "
     "Frame 4: ATTACK RECOVERY — pulling katana back to guard position, "
     "body straightening, blade angled up, returning to ready stance.",
     142),
    ("gunslinger", "枪手",
     "Cowboy gunslinger in long yellow duster coat, wide-brimmed brown hat. "
     "Dual silver revolvers. Sunglasses, confident smirk. "
     "Frame 1: ATTACK WIND-UP — right hand draws revolver from holster, "
     "left hand still near holster, body crouched, eyes aiming. "
     "Frame 2: ATTACK FIRE — right revolver extended forward firing, muzzle flash, "
     "recoil pushes shoulder back, left revolver still holstered. "
     "Frame 3: ATTACK FOLLOW-THROUGH — right arm still extended, left revolver now drawn "
     "and swinging up, coat flares from recoil momentum. "
     "Frame 4: ATTACK RECOVERY — both revolvers held in low ready position, "
     "smoke from barrels, returning to gunslinger stance.",
     143),
    ("fire_mage", "火焰法师",
     "Fire mage in flowing orange and crimson robe with gold trim. "
     "Long white hair, glowing orange eyes. Fire orb in left hand. "
     "Frame 1: ATTACK WIND-UP — left hand fire orb expands rapidly, "
     "right hand rises to meet it, flames swirl around both hands. "
     "Frame 2: ATTACK RELEASE — both hands thrust forward, flaming projectile "
     "launches from hands, robe blows back from heat force. "
     "Frame 3: ATTACK FOLLOW-THROUGH — hands still extended forward, "
     "flame trail from projectile, fire sparks around both hands. "
     "Frame 4: ATTACK RECOVERY — hands lowering, fire orb re-forming in left hand, "
     "embers floating around, returning to mage stance.",
     144),
    ("archer", "弓箭游侠",
     "Forest ranger archer in green hooded cloak over brown leather armor. "
     "Long compound bow, quiver of arrows on back. "
     "Frame 1: ATTACK WIND-UP — reaches over shoulder to nock arrow, "
     "bow held horizontally, eyes tracking target, cloak settles. "
     "Frame 2: ATTACK DRAW — bow pulled to full draw, string at cheek, "
     "body leaning back, bow arm extended fully forward, focused aim. "
     "Frame 3: ATTACK RELEASE — arrow released mid-flight, bowstring still vibrating, "
     "body shifts forward from release momentum, cloak flutters. "
     "Frame 4: ATTACK RECOVERY — bow lowering, hand moving back toward quiver, "
     "returning to neutral archer stance, scanning for next target.",
     145),
    ("mech", "重型机甲",
     "Bulky humanoid mech robot, dark gray and orange armor. "
     "Glowing orange optical visor. Right arm cannon, left arm claw. "
     "Frame 1: ATTACK WIND-UP — cannon arm swings up and back, "
     "chest vents open, orange energy glows in cannon barrel, hydraulics tense. "
     "Frame 2: ATTACK FIRE — cannon fires massive orange energy blast, "
     "recoil rocks mech back, feet slide on ground, bright flash from barrel. "
     "Frame 3: ATTACK FOLLOW-THROUGH — cannon arm still extended, "
     "smoke/steam venting from cannon and chest vents, claw arm braces. "
     "Frame 4: ATTACK RECOVERY — cannon arm lowering, vents closing, "
     "hydraulics resetting, energy glow fading from cannon, returning to idle.",
     146),
    ("assassin", "疾影刺客",
     "Stealthy assassin in purple and black ninja outfit. "
     "Hood up, face veiled. Dual curved daggers in reverse grip. "
     "Frame 1: ATTACK WIND-UP — crouches low, daggers crossed in front, "
     "coiled like a spring, weight on back foot, eyes locked on target. "
     "Frame 2: ATTACK LUNGE — explosive forward lunge, daggers uncross and slash "
     "outward in opposite arcs, body fully extended, momentum forward. "
     "Frame 3: ATTACK FOLLOW-THROUGH — daggers at end of slash arc, "
     "body rotated past target, one blade high one blade low, recovery position. "
     "Frame 4: ATTACK RECOVERY — rolls back into fighting crouch, "
     "daggers pulled back to guard, balanced and ready for next strike.",
     147),
    ("medic", "医疗兵",
     "Military medic in white tactical coat with red cross insignia. "
     "Large healing syringe gun in hand. Medical goggles on forehead. "
     "Frame 1: ATTACK WIND-UP — syringe gun chambered, pumping action, "
     "green healing fluid glows in chamber, feet planted, arm pulled back. "
     "Frame 2: ATTACK FIRE — syringe gun thrust forward, green healing beam "
     "or projectile fires, medical scanner on belt beeps, coat flaps. "
     "Frame 3: ATTACK FOLLOW-THROUGH — syringe gun still extended, "
     "healing glow at nozzle, green particles floating around. "
     "Frame 4: ATTACK RECOVERY — lowers syringe gun, checks chamber, "
     "returns to supportive medic stance, alert and scanning.",
     148),
    ("paladin", "圣骑士",
     "Holy knight in gold and white plate armor. Tower shield. "
     "Longsword. Golden visor, flowing white cape. "
     "Frame 1: ATTACK WIND-UP — sword raised high, shield held forward, "
     "holy light gathers on sword blade, cape billows behind, body braced. "
     "Frame 2: ATTACK SMITE — sword swings down with holy energy, "
     "golden light trails the blade, shield guards body, powerful overhead strike. "
     "Frame 3: ATTACK FOLLOW-THROUGH — sword at lowest point of swing, "
     "holy light dissipating from impact, shield still forward guarding. "
     "Frame 4: ATTACK RECOVERY — sword returns to guard position at side, "
     "shield lowered slightly, holy glow fading, returning to knightly stance.",
     149),
    ("engineer", "工程师",
     "Tech engineer in blue jumpsuit with orange safety stripes. "
     "Welding goggles. Wrench in hand, plasma welder holstered. "
     "Frame 1: ATTACK WIND-UP — draws plasma welder from holster, "
     "blue energy arcs from welder tip, wrench in other hand, tools ready. "
     "Frame 2: ATTACK FIRE — plasma welder fires a concentrated energy beam, "
     "bright blue-white, welding goggles polarized, recoil in arm. "
     "Frame 3: ATTACK FOLLOW-THROUGH — plasma beam continuing, "
     "sparks flying from welder tip, wrench raised defensively, body braced. "
     "Frame 4: ATTACK RECOVERY — plasma welder deactivated, cooling down, "
     "returning welder to holster, wrench back to shoulder, casual stance.",
     150),
    ("berserker", "狂战士",
     "Massive raging berserker, bare chested with war paint. "
     "Blood-red glowing eyes. Huge double-bladed battle axe. "
     "Frame 1: ATTACK WIND-UP — massive axe pulled back over shoulder, "
     "body twisted for maximum torque, blood aura flaring, teeth bared in fury. "
     "Frame 2: ATTACK MASSIVE SWING — axe swung in huge horizontal arc, "
     "body fully rotating with the swing, blood aura trailing the blade. "
     "Frame 3: ATTACK FOLLOW-THROUGH — axe at completion of swing arc, "
     "body over-rotated, momentum carrying through, fur mantle flying. "
     "Frame 4: ATTACK RECOVERY — pulls axe back to ready position, "
     "blood aura still pulsing, breathing heavily, ready to swing again.",
     151),
]

ENEMY_SPRITES = [
    ("basic", "无人机兵",
     "Small flying robot drone, dark gray metal body with red LED eyes. "
     "Four small rotor blades on top, single searchlight on bottom. "
     "Compact chassis, antenna on top. "
     "Frame 1: idle hovering steadily, rotors spinning. "
     "Frame 2: slight upward bob, searchlight sweeps. "
     "Frame 3: drifts left slightly, body tilts, rotors adjust. "
     "Frame 4: bob down accent, searchlight dims and brightens, return to frame 1.",
     100),
    ("fast", "疾行者",
     "Sleek quadrupedal speedster robot, orange and black chassis. "
     "Streamlined body like a mechanical cheetah, long wheelbase. "
     "Four thin powerful legs with clawed feet. "
     "Single yellow optic scanner on a streamlined head. "
     "Frame 1: idle ready to dash, crouched on all fours. "
     "Frame 2: leans forward, center of gravity shifts, rear legs coil. "
     "Frame 3: shifts weight to sprint, front legs extend. "
     "Frame 4: crouch race start — rear legs loaded, scanner brightens.",
     101),
    ("tank", "重装机兵",
     "Heavy purple armored battle mech, thick reinforced plating. "
     "Short wide stubby body like a walking tank. "
     "Two massive tread-like feet, shoulder-mounted cannons. "
     "Single red visor slit, exhaust vents on back. "
     "Frame 1: idle heavy stance, both feet planted, cannons level. "
     "Frame 2: armor plates shift, hydraulics hiss, vents open. "
     "Frame 3: tread roll — one foot shifts forward slightly. "
     "Frame 4: heavy stomp accent — lifts one foot, slams down, ground shake.",
     102),
    ("ranged", "狙击手",
     "Pink bi-pedal sniper machine, one oversized optical targeting eye. "
     "Long barrel sniper rifle integrated into right arm. "
     "Thin insect-like legs, radar dish on back. "
     "Frame 1: idle scanning — eye sweeps back and forth, rifle aimed down. "
     "Frame 2: aim adjustment — crouches, elbow rests on knee, eye zooms. "
     "Frame 3: eye glow pulse — lens glows pink, target acquired signal. "
     "Frame 4: lock-on target — rifle tracks, crosshair effect, ready to fire.",
     103),
    ("elite", "精英猎手",
     "Golden elite hunter machine, humanoid upper body on four spider legs. "
     "Two curved horns on head, golden aura shimmering. "
     "Dual energy blades as arms. "
     "Chest has a glowing golden core. "
     "Frame 1: idle majestic — stands tall, four legs at corners, golden aura steady. "
     "Frame 2: energy surge — core pulses brighter, aura flares, blades hum. "
     "Frame 3: horn glow accent — horn tips glow, electricity crackles between them. "
     "Frame 4: battle ready — crouches slightly, blades cross in front, aura intensifies.",
     104),
    ("boss", "BOSS",
     "Massive crimson boss monster — giant humanoid with demonic features. "
     "Two large curved horns, burning red eyes, fanged maw. "
     "Muscular body with dark red skin, black armor plates on shoulders. "
     "Huge energy axe in right hand, left hand crackling with red lightning. "
     "Frame 1: idle intimidating — stands at full height, red aura radiating. "
     "Frame 2: roar anticipation — inhales deeply, chest expands, aura pulses. "
     "Frame 3: ground shake — stomps one foot, red lightning strikes ground. "
     "Frame 4: energy explosion idle — throws arms wide, red energy burst, roar.",
     105),
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


def make_sprite_prompt(positive_text, seed=42, prefix="cb_sprite"):
    """
    构建 Z-Image-Turbo 工作流提示，生成 1024x1024 的 2x2 grid sprite sheet
    v2: 7 steps, CFG 2.0, 品红背景
    """
    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "z_image_turbo_bf16.safetensors",
                "weight_dtype": "default"
            }
        },
        "2": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {
                "model": ["1", 0],
                "shift": 3.0
            }
        },
        "3": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen_3_4b.safetensors",
                "type": "qwen_image"
            }
        },
        "4": {
            "class_type": "EmptySD3LatentImage",
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive_text,
                "clip": ["3", 0]
            }
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": (
                    "3d, photorealistic, realistic, blurry, low quality, ugly, "
                    "deformed, distorted, text, watermark, signature, complex, messy, "
                    "photoreal, oil painting, cell borders, grid lines, labels, numbers, "
                    "background gradients, shadow under character, multi-colored background, "
                    "asymmetric frames, different sizes between cells, "
                    "crossed cell edges, limbs outside cells"
                ),
                "clip": ["3", 0]
            }
        },
        "7": {
            "class_type": "ConditioningZeroOut",
            "inputs": {
                "conditioning": ["6", 0]
            }
        },
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
        "9": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": "ae.safetensors"
            }
        },
        "10": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["8", 0],
                "vae": ["9", 0]
            }
        },
        "11": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": prefix,
                "images": ["10", 0]
            }
        },
    }


def generate_sprites(category_name, items, prefix):
    """生成一类 sprite sheet"""
    count = len(items)
    print(f"\n{'='*55}")
    print(f"  [{category_name}] 正在生成 {count} 个 sprite sheet...")
    print(f"{'='*55}")

    for i, item in enumerate(items):
        item_id = item[0]
        item_name = item[1]
        item_desc = item[2]
        item_seed = item[3] if len(item) > 3 else 200
        prompt_prefix = f"{prefix}_{item_id}"

        # 组装完整提示词：全局风格 + 具体角色描述
        full_prompt = f"{GLOBAL_STYLE}\n\n{item_desc}"

        print(f"  [{i+1}/{count}] {item_name:<12} ({item_id})...", end=" ", flush=True)

        prompt = make_sprite_prompt(full_prompt, seed=item_seed, prefix=prompt_prefix)
        prompt_id = submit_prompt(prompt)

        if not prompt_id:
            print("FAIL")
            continue

        outputs = wait_for_completion(prompt_id)
        if outputs:
            print("OK")
        else:
            print("TIMEOUT")


def copy_sprites_to_assets():
    """将生成的 sprite sheets 复制到 assets/sprites/ 目录"""
    sprite_dir = os.path.join(ASSETS_DIR, "sprites")
    chars_dir = os.path.join(sprite_dir, "chars")
    enemies_dir = os.path.join(sprite_dir, "enemies")
    os.makedirs(chars_dir, exist_ok=True)
    os.makedirs(enemies_dir, exist_ok=True)

    # 读取 ComfyUI output 中的所有 PNG
    all_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.png')]

    from collections import defaultdict
    by_base = defaultdict(list)
    for f in all_files:
        if 'cb_sprite' not in f:
            continue
        base = f.rsplit('_', 2)[0]
        by_base[base].append(f)

    prefixed_dir = {
        'cb_sprite_char': 'chars',
        'cb_sprite_enemy': 'enemies',
        'cb_sprite_char_attack': 'chars',
        'cb_sprite_char_idle': 'chars',
        'cb_sprite_char_walk': 'chars',
        'cb_sprite_enemy_walk': 'enemies',
    }

    copied = 0
    for base, files in sorted(by_base.items()):
        matched_sub = None
        for prefix, subdir in prefixed_dir.items():
            if base.startswith(prefix):
                matched_sub = subdir
                break
        if not matched_sub:
            continue

        # 取最高计数变体
        files.sort(key=lambda x: int(x.rsplit('_', 2)[1]))
        newest = files[-1]

        # 构建文件名
        if 'attack' in base:
            new_name = f'{base}_00001_.png'
        elif 'walk' in base:
            new_name = f'{base}_00001_.png'
        else:
            parts = newest.rsplit('_', 2)
            new_name = f'{parts[0]}_00001_.png'

        src = os.path.join(OUTPUT_DIR, newest)
        dst = os.path.join(sprite_dir, matched_sub, new_name)
        shutil.copy2(src, dst)
        print(f"  [OK] {new_name}  ->  assets/sprites/{matched_sub}/")
        copied += 1

    return copied


def split_sprite_sheets():
    """使用 agent-sprite-forge 处理器分割 sprite sheets 为独立帧"""
    sprite_dir = os.path.join(ASSETS_DIR, "sprites")
    processor = os.path.join(
        "H:/ai_works/buffPrj1/agent-sprite-forge/skills/generate2dsprite/scripts/generate2dsprite.py"
    )

    # 处理角色 sprite sheets（待机）
    chars_dir = os.path.join(sprite_dir, "chars")
    if os.path.exists(chars_dir):
        for f in os.listdir(chars_dir):
            if f.endswith('.png') and 'cb_sprite_char_' in f and '00001_' in f and 'attack' not in f:
                input_path = os.path.join(chars_dir, f)
                output_dir = os.path.join(chars_dir, f.replace('_00001_.png', ''))
                os.makedirs(output_dir, exist_ok=True)

                # 获取角色ID
                parts = f.replace('cb_sprite_char_', '').split('_')
                char_id = parts[0]

                print(f"  待机分割: {char_id}...", end=" ", flush=True)
                cmd = (
                    f'python "{processor}" process '
                    f'--input "{input_path}" '
                    f'--target player '
                    f'--mode idle '
                    f'--output-dir "{output_dir}" '
                    f'--cell-size 128 '
                    f'--threshold 90 '
                    f'--edge-threshold 130 '
                    f'--align center '
                    f'--shared-scale '
                    f'--fit-scale 0.85 '
                    f'--component-mode largest '
                    f'--duration 300'
                )
                ret = os.system(cmd)
                if ret == 0:
                    print("OK")
                else:
                    print("FAIL")

    # 处理角色攻击 sprite sheets（攻击模式）
    if os.path.exists(chars_dir):
        for f in os.listdir(chars_dir):
            if f.endswith('.png') and 'cb_sprite_char_attack_' in f and '00001_' in f:
                input_path = os.path.join(chars_dir, f)
                # 提取角色ID: cb_sprite_char_attack_swordsman_00001_.png → swordsman
                char_id = f.replace('cb_sprite_char_attack_', '').replace('_00001_.png', '')
                output_dir = os.path.join(chars_dir, char_id)
                os.makedirs(output_dir, exist_ok=True)

                print(f"  攻击分割: {char_id}...", end=" ", flush=True)
                cmd = (
                    f'python "{processor}" process '
                    f'--input "{input_path}" '
                    f'--target player '
                    f'--mode attack '
                    f'--output-dir "{output_dir}" '
                    f'--cell-size 128 '
                    f'--threshold 90 '
                    f'--edge-threshold 130 '
                    f'--align center '
                    f'--shared-scale '
                    f'--fit-scale 0.85 '
                    f'--component-mode largest '
                    f'--duration 150'
                )
                ret = os.system(cmd)
                if ret == 0:
                    print("OK")
                else:
                    print("FAIL")

    # 处理角色4方向待机 sprite sheets — 使用 player_sheet 分割，然后重命名为 idle-{dir}-{frame}.png
    if os.path.exists(chars_dir):
        for f in os.listdir(chars_dir):
            if f.endswith('.png') and 'cb_sprite_char_idle_' in f and '00001_' in f:
                input_path = os.path.join(chars_dir, f)
                char_id = f.replace('cb_sprite_char_idle_', '').replace('_00001_.png', '')
                output_dir = os.path.join(chars_dir, char_id)
                os.makedirs(output_dir, exist_ok=True)

                print(f"  方向待机分割: {char_id}...", end=" ", flush=True)
                # 先分割到临时目录
                temp_dir = os.path.join(chars_dir, char_id, '__idle_temp__')
                os.makedirs(temp_dir, exist_ok=True)
                cmd = (
                    f'python "{processor}" process '
                    f'--input "{input_path}" '
                    f'--target player '
                    f'--mode player_sheet '
                    f'--output-dir "{temp_dir}" '
                    f'--cell-size 96 '
                    f'--threshold 90 '
                    f'--edge-threshold 130 '
                    f'--align center '
                    f'--shared-scale '
                    f'--fit-scale 0.75 '
                    f'--component-mode largest '
                    f'--duration 600'
                )
                ret = os.system(cmd)
                if ret == 0:
                    # 重命名: down-1.png -> idle-down-1.png, left-1.png -> idle-left-1.png, etc.
                    for d in ['down', 'left', 'right', 'up']:
                        for n in range(1, 5):
                            src = os.path.join(temp_dir, f'{d}-{n}.png')
                            dst = os.path.join(output_dir, f'idle-{d}-{n}.png')
                            if os.path.exists(src):
                                shutil.move(src, dst)
                    # 清理临时目录
                    if os.path.exists(temp_dir):
                        for leftover in os.listdir(temp_dir):
                            os.remove(os.path.join(temp_dir, leftover))
                        os.rmdir(temp_dir)
                    print("OK")
                else:
                    print("FAIL")
                    # 清理临时目录
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)

    # 处理角色行走方向 sprite sheets（4x4 grid，player_sheet模式）
    if os.path.exists(chars_dir):
        for f in os.listdir(chars_dir):
            if f.endswith('.png') and 'cb_sprite_char_walk_' in f and '00001_' in f:
                input_path = os.path.join(chars_dir, f)
                char_id = f.replace('cb_sprite_char_walk_', '').replace('_00001_.png', '')
                output_dir = os.path.join(chars_dir, char_id)
                os.makedirs(output_dir, exist_ok=True)

                print(f"  行走分割: {char_id}...", end=" ", flush=True)
                cmd = (
                    f'python "{processor}" process '
                    f'--input "{input_path}" '
                    f'--target player '
                    f'--mode player_sheet '
                    f'--output-dir "{output_dir}" '
                    f'--cell-size 96 '
                    f'--threshold 90 '
                    f'--edge-threshold 130 '
                    f'--align center '
                    f'--shared-scale '
                    f'--fit-scale 0.75 '
                    f'--component-mode largest '
                    f'--duration 180'
                )
                ret = os.system(cmd)
                if ret == 0:
                    print("OK")
                else:
                    print("FAIL")

    # 处理敌人 sprite sheets（待机）
    enemies_dir = os.path.join(sprite_dir, "enemies")
    if os.path.exists(enemies_dir):
        for f in os.listdir(enemies_dir):
            if f.endswith('.png') and '00001_' in f and 'walk' not in f:
                input_path = os.path.join(enemies_dir, f)
                output_dir = os.path.join(enemies_dir, f.replace('_00001_.png', ''))
                os.makedirs(output_dir, exist_ok=True)

                parts = f.replace('cb_sprite_enemy_', '').split('_')
                enemy_id = parts[0]

                print(f"  分割: {enemy_id}...", end=" ", flush=True)
                cmd = (
                    f'python "{processor}" process '
                    f'--input "{input_path}" '
                    f'--target creature '
                    f'--mode idle '
                    f'--output-dir "{output_dir}" '
                    f'--cell-size 128 '
                    f'--threshold 90 '
                    f'--edge-threshold 130 '
                    f'--align center '
                    f'--shared-scale '
                    f'--fit-scale 0.85 '
                    f'--component-mode largest '
                    f'--duration 300'
                )
                ret = os.system(cmd)
                if ret == 0:
                    print("OK")
                else:
                    print("FAIL")

    # 处理敌人行走方向 sprite sheets（4x4 grid，player_sheet模式）
    if os.path.exists(enemies_dir):
        for f in os.listdir(enemies_dir):
            if f.endswith('.png') and 'cb_sprite_enemy_walk_' in f and '00001_' in f:
                input_path = os.path.join(enemies_dir, f)
                enemy_id = f.replace('cb_sprite_enemy_walk_', '').replace('_00001_.png', '')
                output_dir = os.path.join(enemies_dir, enemy_id)
                os.makedirs(output_dir, exist_ok=True)

                print(f"  行走分割: {enemy_id}...", end=" ", flush=True)
                cmd = (
                    f'python "{processor}" process '
                    f'--input "{input_path}" '
                    f'--target player '
                    f'--mode player_sheet '
                    f'--output-dir "{output_dir}" '
                    f'--cell-size 96 '
                    f'--threshold 90 '
                    f'--edge-threshold 130 '
                    f'--align center '
                    f'--shared-scale '
                    f'--fit-scale 0.75 '
                    f'--component-mode largest '
                    f'--duration 180'
                )
                ret = os.system(cmd)
                if ret == 0:
                    print("OK")
                else:
                    print("FAIL")


def main():
    print("=" * 55)
    print("  CYBER BLADE - Sprite Sheet 生成器 v2")
    print("=" * 55)
    print("  模型: z_image_turbo_bf16 | 分辨率: 1024x1024")
    print("  参数: steps=7 | CFG=2.0 | 品红背景")
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

    # 生成角色待机 sprite sheets
    generate_sprites("角色 CHARS IDLE", CHAR_SPRITES, "cb_sprite_char")

    # 生成角色4方向待机 sprite sheets
    generate_sprites("角色 CHARS IDLE DIR", CHAR_IDLE_DIR_SPRITES, "cb_sprite_char_idle")

    # 生成角色攻击 sprite sheets
    generate_sprites("角色 CHARS ATTACK", CHAR_ATTACK_SPRITES, "cb_sprite_char_attack")

    # 生成角色行走方向 sprite sheets
    generate_sprites("角色 CHARS WALK", CHAR_WALK_SPRITES, "cb_sprite_char_walk")

    # 生成敌人 sprite sheets
    generate_sprites("敌人 ENEMIES", ENEMY_SPRITES, "cb_sprite_enemy")

    # 生成敌人行走方向 sprite sheets
    generate_sprites("敌人 ENEMIES WALK", ENEMY_WALK_SPRITES, "cb_sprite_enemy_walk")

    # 复制到 assets
    print(f"\n{'='*55}")
    print(f"  正在复制 sprite sheets 到 assets/sprites/...")
    print(f"{'='*55}")
    copied = copy_sprites_to_assets()
    print(f"  已复制 {copied} 个 sprite sheets")

    # 分割 sprite sheets
    print(f"\n{'='*55}")
    print(f"  使用 agent-sprite-forge 分割 sprite sheets...")
    print(f"{'='*55}")
    split_sprite_sheets()

    print(f"\n{'='*55}")
    print(f"  [DONE] Sprite sheet 生成完成！")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
