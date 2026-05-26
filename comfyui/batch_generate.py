#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ComfyUI batch icon generator for CYBER BLADE game"""

import json
import time
import os
import sys
import urllib.request
import urllib.error

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = "H:/AI/ComfyUI_windows_portable/ComfyUI/output"
ASSETS_DIR = "H:/ai_works/buffPrj1/assets"
MODEL = "sd_xl_base_1.0.safetensors"

# ====== All icon definitions (no emoji) ======

WEAPONS = [
    ("pistol",   "Pistol",    "futuristic neon pistol, glowing cyan, small simple gun shape, top down game icon"),
    ("shotgun",  "Shotgun",   "futuristic shotgun, short wide barrel, glowing orange, top down game icon"),
    ("sniper",   "Sniper",    "futuristic sniper rifle, long barrel, glowing green, top down game icon"),
    ("gatling",  "Gatling",   "futuristic gatling gun, rotating multi-barrel, glowing gold, top down game icon"),
    ("laser",    "Laser",     "futuristic laser cannon, rectangular with lens, glowing magenta, top down game icon"),
    ("shock",    "Shock",     "futuristic shock gun, tesla coil shape, glowing blue electricity, top down game icon"),
    ("plasma",   "Plasma",    "futuristic plasma sword, energy blade, glowing red, top down game icon"),
    ("rocket",   "Rocket",    "futuristic rocket launcher, tube shape, glowing red-orange, top down game icon"),
    ("frost",    "Frost",     "futuristic frost gun, crystal shape, glowing ice blue, top down game icon"),
    ("homing",   "Homing",    "futuristic homing missile launcher, angled tube, glowing amber, top down game icon"),
]

ITEMS = [
    ("hpUp",      "HP Core",       "floating red heart crystal, glowing, simple game icon, dark bg"),
    ("regen",     "Regen Chip",    "green cross healing icon, glowing, simple game icon, dark bg"),
    ("armorUp",   "Armor Plate",   "gray shield plate icon, armored, simple game icon, dark bg"),
    ("dodgeUp",   "Dodge Module",  "cyan wind swirl motion icon, simple game icon, dark bg"),
    ("critUp",    "Crit Scope",    "red crosshair targeting icon, simple game icon, dark bg"),
    ("critDmg",   "Crit Damage",   "orange explosion burst icon, simple game icon, dark bg"),
    ("speedUp",   "Speed Boost",   "yellow lightning bolt speed icon, simple game icon, dark bg"),
    ("lifesteal", "Life Steal",    "dark red blood drop icon, simple game icon, dark bg"),
    ("rangeUp",   "Range Scope",   "gray magnifying glass scope icon, simple game icon, dark bg"),
    ("harvestUp", "Harvest",       "gold coin stack icon, simple game icon, dark bg"),
    ("pickupUp",  "Pickup Field",  "purple magnetic field waves icon, simple game icon, dark bg"),
    ("luckUp",    "Luck Star",     "golden four-point star icon, simple game icon, dark bg"),
]

CHARS = [
    ("ranger",   "Ranger",  "cyber ranger character portrait, futuristic soldier with visor, neon cyberpunk style, simple game icon"),
    ("mech",     "Mech",    "heavy mech robot portrait, bulky armored war machine, orange eyes, cyberpunk, simple game icon"),
    ("assassin", "Assassin","cyber assassin portrait, sleek stealthy figure, purple neon, cyberpunk, simple game icon"),
]

ENEMIES = [
    ("basic",  "Basic",  "basic mutant creature icon, small red eyes, top down game sprite, simple shape"),
    ("fast",   "Fast",   "fast sleek creature icon, streamlined, orange trail, top down game sprite"),
    ("tank",   "Tank",   "heavy armored creature icon, thick shell, purple, top down game sprite"),
    ("ranged", "Ranged", "ranged shooter creature icon, one large eye, pink, top down game sprite"),
    ("elite",  "Elite",  "elite powerful creature icon, golden aura, horned, top down game sprite"),
    ("boss",   "Boss",   "boss giant creature icon, menacing, crimson red aura, top down game sprite"),
]


def submit_prompt(prompt_data):
    data = json.dumps({"prompt": prompt_data}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result.get("prompt_id")
    except Exception as e:
        print(f"  FAILED: {e}")
        return None


def wait_for_completion(prompt_id, timeout=60):
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
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": MODEL}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 128, "height": 128, "batch_size": 1}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {
            "text": f"game icon pixel art style, simple flat top down 2D game icon, {positive_text}, dark background, clean simple shape, high contrast, minimalist game sprite icon, centered",
            "clip": ["1", 1]
        }},
        "3": {"class_type": "CLIPTextEncode", "inputs": {
            "text": "3d, photorealistic, blurry, low quality, ugly, text, watermark, complex, detailed, messy, human, realistic, cluttered, noisy",
            "clip": ["1", 1]
        }},
        "5": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 6, "cfg": 2.0,
            "sampler_name": "euler", "scheduler": "simple",
            "denoise": 1.0, "model": ["1", 0],
            "positive": ["2", 0], "negative": ["3", 0],
            "latent_image": ["4", 0]
        }},
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"filename_prefix": prefix, "images": ["6", 0]}},
    }


def generate_category(category_name, items, prefix):
    count = len(items)
    print(f"\n{'=' * 55}")
    print(f"  [{category_name}] generating {count} icons...")
    print(f"{'=' * 55}")

    for i, item in enumerate(items):
        item_id = item[0]
        item_name = item[1]
        item_desc = item[2]
        prompt_prefix = f"{prefix}_{item_id}"

        print(f"  [{i+1}/{count}] {item_name:<15} ({item_id})...", end=" ", flush=True)

        prompt = make_prompt(item_desc, seed=42 + i, prefix=prompt_prefix)
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
    print(f"CYBER BLADE - ComfyUI Batch Icon Generator")
    print(f"  Model: {MODEL}")
    print(f"  Output: {OUTPUT_DIR}")
    print()

    generate_category("WEAPONS", WEAPONS, "cb_weapon")
    generate_category("ITEMS", ITEMS, "cb_item")
    generate_category("CHARACTERS", CHARS, "cb_char")
    generate_category("ENEMIES", ENEMIES, "cb_enemy")

    print(f"\n{'=' * 55}")
    print(f"  ALL DONE! Check output directory:")
    print(f"    {OUTPUT_DIR}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
