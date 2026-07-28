import base64
import datetime
import json
import os
import random
import socket
import sys
import time
import uuid
import cv2
import keyboard
import numpy as np
import pyautogui
import requests

# ==========================================
# ⚙️ GITHUB CONFIGURATION
# ==========================================
GITHUB_USER = "sastra028"
GITHUB_REPO = "hatday"
GITHUB_BRANCH = "main"

GITHUB_WHITELIST_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/whitelist.json"


# ==========================================
# 🔍 HARDWARE KEY FUNCTIONS
# ==========================================
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
    if not os.path.exists(config_path):
        config_path = "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: ไม่พบไฟล์ config.json")
        return {}


def get_mac_address():
    mac_num = hex(uuid.getnode())[2:].zfill(12)
    return ":".join(mac_num[i : i + 2] for i in range(0, 11, 2)).upper()


def generate_hardware_key():
    computer_name = socket.gethostname().upper()
    return f"{computer_name}_{get_mac_address()}"


# ==========================================
# 📝 AUTO-REGISTER & LICENSE CHECK
# ==========================================
def register_pending_license(my_key):
    print("\n⏳ Auto-registering this machine to GitHub...")
    computer_name = socket.gethostname().upper()
    file_name = f"requests/{my_key}.json"
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_name}"
    config = load_config()
    headers = {
        "Authorization": f"token {config.get('github_token', '')}",
        "Accept": "application/vnd.github.v3+json",
    }

    check_req = requests.get(api_url, headers=headers, timeout=10)
    if check_req.status_code == 200:
        print("📌 Registration Request already submitted!")
        return

    payload_data = {
        "key": my_key,
        "hostname": computer_name,
        "mac": get_mac_address(),
        "request_date": datetime.date.today().strftime("%d-%m-%Y"),
        "status": "pending_approval",
    }

    encoded_content = base64.b64encode(
        json.dumps(payload_data, indent=2).encode("utf-8")
    ).decode("utf-8")
    body = {
        "message": f"Auto-register request: {my_key}",
        "content": encoded_content,
        "branch": GITHUB_BRANCH,
    }

    try:
        response = requests.put(
            api_url, headers=headers, json=body, timeout=10
        )
        if response.status_code in [200, 201]:
            print(f"📝 Successfully registered key ({my_key})")
        else:
            print(f"⚠️ Auto-register failed (HTTP {response.status_code})")
    except Exception as e:
        print(f"⚠️ Failed to send registration request: {e}")


def check_license():
    my_key = generate_hardware_key()
    print(f"🔍 Your Hardware Key: {my_key}")
    print("⏳ Checking license status with GitHub...")

    try:
        cache_buster_url = f"{GITHUB_WHITELIST_URL}?t={int(time.time())}"
        response = requests.get(cache_buster_url, timeout=10)

        if response.status_code != 200:
            print("❌ Error: Cannot fetch whitelist from GitHub server.")
            return False

        whitelist = response.json()
        user_license = next(
            (item for item in whitelist if item.get("key") == my_key), None
        )

        if not user_license:
            print("❌ Access Denied: Machine not registered.")
            register_pending_license(my_key)
            return False

        if user_license.get("status") != "active":
            print("❌ Access Denied: License suspended.")
            return False

        expire_str = user_license.get("expire")
        expire_date = datetime.datetime.strptime(expire_str, "%d-%m-%Y").date()
        today = datetime.date.today()

        if today > expire_date:
            print(f"❌ Access Denied: License expired on {expire_str}.")
            return False

        days_left = (expire_date - today).days
        print(
            f"✅ License Verified! Status: Active (Expires: {expire_str} | Remaining: {days_left} days)"
        )
        return True

    except Exception as e:
        print(f"⚠️ License Verification Error: {e}")
        return False


# ==========================================
# 🚀 MAIN APPLICATION ENTRY POINT
# ==========================================
if __name__ == "__main__":
    if not check_license():
        print("🛑 Program shutting down...")
        input("\nPress Enter to exit...")
        sys.exit()

    print("\n-------------------------------------------")
    print("🚀 License Authorized! Starting Bot Engine...")
    print("-------------------------------------------\n")


pyautogui.FAILSAFE = True

# --- ตั้งค่าชื่อไฟล์รูปภาพแม่แบบ ---
IMAGE_WHEAT_RIPE = "wheat_ripe.png"
IMAGE_SICKLE = "sickle.png"
IMAGE_SEED = "wheat_seed.png"
SOIL_TEMPLATES = ["empty_soil1.png", "empty_soil2.png"]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    full_path = os.path.join(base_path, relative_path)
    if not os.path.exists(full_path):
        filename_only = os.path.basename(relative_path)
        img_in_images = os.path.join(base_path, "images", filename_only)
        if os.path.exists(img_in_images):
            return img_in_images

    return full_path


def load_image_safe(relative_path):
    """อ่านรูปภาพแบบภาพสี BGR ปกติ"""
    full_path = resource_path(relative_path)
    if not os.path.exists(full_path):
        print(f"❌ File not found: {full_path}")
        return None

    try:
        with open(full_path, "rb") as f:
            file_bytes = bytearray(f.read())
        img_array = np.asarray(file_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            print(f"⚠️ Warning: Could not decode image at {full_path}")

        return img
    except Exception as e:
        print(f"❌ Error loading template ({full_path}): {e}")
        return None


# ==========================================
# 🛡️ SYSTEM MASKING (ระบบถมสีดำปิดมุมจอภาพสี)
# ==========================================
def apply_ui_mask_color(screenshot_bgr):
    """ถมสีดำ (0, 0, 0) บนภาพสี เพื่อปิดมุมขวาบนและ UI รอบนอกอย่างเด็ดขาด"""
    h_scr, w_scr, _ = screenshot_bgr.shape

    # 🚫 1. มุมขวาบน (ขยายลงมาลึกครอบคลุม เหรียญ/เพชร/เตาอบ/โปรโมชัน)
    cv2.rectangle(
        screenshot_bgr,
        (int(w_scr * 0.60), 0),
        (w_scr, int(h_scr * 0.55)),
        (0, 0, 0),
        -1,
    )

    # 🚫 2. มุมซ้ายบน + ถนน + รถส่งของ
    cv2.rectangle(
        screenshot_bgr,
        (0, 0),
        (int(w_scr * 0.50), int(h_scr * 0.55)),
        (0, 0, 0),
        -1,
    )

    # 🚫 3. มุมซ้ายล่าง (ปุ่มร้านค้า)
    cv2.rectangle(
        screenshot_bgr,
        (0, int(h_scr * 0.75)),
        (int(w_scr * 0.20), h_scr),
        (0, 0, 0),
        -1,
    )

    # 🚫 4. มุมขวาล่าง (ปุ่มเพื่อน + พุ่มไม้)
    cv2.rectangle(
        screenshot_bgr,
        (int(w_scr * 0.75), int(h_scr * 0.70)),
        (w_scr, h_scr),
        (0, 0, 0),
        -1,
    )

    return screenshot_bgr


# ==========================================
# 🎯 MATCHING FUNCTIONS (COLOR)
# ==========================================
# เพิ่มรายการรูปภาพที่ต้องการ Ignore ข้าม ไม่ให้บอทไปยุ่ง
IGNORE_TEMPLATES = [
    "ignore_shop.png",
    "1.png",
    "2.png",
    "3.png"
]


def is_ignored_zone(check_x, check_y, threshold_distance=40):
    """เช็กว่าพิกัดที่เจอ อยู่ใกล้กับวัตถุใน IGNORE_TEMPLATES หรือไม่"""
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    for ignore_img_name in IGNORE_TEMPLATES:
        ignore_template = load_image_safe(ignore_img_name)
        if ignore_template is None:
            continue

        result = cv2.matchTemplate(
            screenshot_bgr, ignore_template, cv2.TM_CCOEFF_NORMED
        )
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.70:
            h, w, _ = ignore_template.shape
            ign_x = max_loc[0] + w // 2
            ign_y = max_loc[1] + h // 2

            # คำนวณระยะห่าง ถ้าระยะใกล้กันเกินไป ถือว่าเป็นจุดที่ไม่ต้องการ
            distance = np.hypot(check_x - ign_x, check_y - ign_y)
            if distance < threshold_distance:
                print(
                    f"⚠️ พบจุด matching ใกล้กับไอคอนที่ต้องการ Ignore ({ignore_img_name}) -> ข้าม!"
                )
                return True
    return False


WHEAT_RIPE_TEMPLATES = ["wheat_ripe.png", "wheat_ripe_2.png", "wheat_ripe_3.png"]
def find_any_ripe_crop(confidence=0.68):
    """🌾 สแกนหาพืชสุกจาก List รูปภาพ WHEAT_RIPE_TEMPLATES"""
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screenshot_masked = apply_ui_mask_color(screenshot_bgr)

    for crop_img in WHEAT_RIPE_TEMPLATES:
        template = load_image_safe(crop_img)
        if template is None:
            continue

        result = cv2.matchTemplate(
            screenshot_masked, template, cv2.TM_CCOEFF_NORMED
        )
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            h, w, _ = template.shape
            center_x = max_loc[0] + w // 2 + random.randint(-2, 2)
            center_y = max_loc[1] + h // 2 + random.randint(-2, 2)

            if is_ignored_zone(center_x, center_y):
                continue

            print(
                f"✅ พบพืชสุกด้วยรูป: {crop_img} (Score: {max_val:.2f}) ที่พิกัด ({center_x}, {center_y})"
            )
            return (center_x, center_y)

    return None

def find_and_get_center(template_path, confidence=0.75):
    """ค้นหารูปภาพ และเช็กข้ามไอคอนที่ Ignore"""
    template = load_image_safe(template_path)
    if template is None:
        return None

    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # ถมสีดำปิดขอบมุมรอบนอก
    screenshot_masked = apply_ui_mask_color(screenshot_bgr)

    result = cv2.matchTemplate(
        screenshot_masked, template, cv2.TM_CCOEFF_NORMED
    )
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        h, w, _ = template.shape
        center_x = max_loc[0] + w // 2 + random.randint(-3, 3)
        center_y = max_loc[1] + h // 2 + random.randint(-3, 3)

        # 🛡️ เช็กว่าจุดที่เจอตรงกับไอคอนที่ต้องการ Ignore หรือไม่
        if is_ignored_zone(center_x, center_y):
            return None

        return (center_x, center_y)

    return None


def find_any_empty_soil(confidence=0.65):
    """สแกนหาแปลงดินว่าง"""
    for soil_img in SOIL_TEMPLATES:
        pos = find_and_get_center(soil_img, confidence=confidence)
        if pos:
            print(f"🤎 เจอแปลงดินว่าง (ลาย: {soil_img}) ที่พิกัด {pos}")
            return pos
    return None


def plant_crops(soil_pos):
    """กระบวนการปลูกพืช"""
    print(f" 🌱 เริ่มกระบวนการปลูกพืชที่พิกัดดินว่าง {soil_pos}...")

    pyautogui.click(soil_pos[0], soil_pos[1])
    time.sleep(0.8)

    # ค้นหาภาพไอคอนพืชแบบภาพสี
    seed_pos = find_and_get_center(IMAGE_SEED, confidence=0.60)

    if not seed_pos:
        seed_x = soil_pos[0] - 80
        seed_y = soil_pos[1] - 50
        seed_pos = (seed_x, seed_y)
        print(
            f" ⚠️ สแกนหาภาพพืชไม่พบ -> ใช้พิกัดไอคอนอ้างอิงจากแปลงดิน: {seed_pos}"
        )
    else:
        print(f" 🌾 พบภาพพืชที่พิกัด: {seed_pos}")

    print(
        f" 🚜 กำลังเลื่อนเมาส์ไปที่พิกัดพืช {seed_pos} เพื่อเริ่มลากปลูก..."
    )

    pyautogui.moveTo(seed_pos[0], seed_pos[1], duration=0.3)
    time.sleep(0.2)

    pyautogui.mouseDown(button="left")
    time.sleep(0.2)

    pyautogui.moveTo(soil_pos[0] + 250, soil_pos[1] + 120, duration=0.8)
    pyautogui.moveTo(soil_pos[0] - 100, soil_pos[1] - 50, duration=0.8)

    pyautogui.mouseUp(button="left")
    time.sleep(0.3)

    print("✨ สั่งปลูกเรียบร้อย!")


SICKLE_TEMPLATES = ["sickle.png", "sickle1.png", "sickle2.png" "sickle3.png" "sickle4.png"]
def find_sickle(confidence=0.50):
    """⛏️ สแกนหาเคียวเกี่ยวข้าว รองรับ Alpha Channel โปร่งใส"""
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    # ปิดเฉพาะขอบจอด้านขวา เพื่อให้เปิดโล่งโซนแปลงผัก/เคียวฝั่งซ้าย
    h_scr, w_scr, _ = screenshot_bgr.shape
    cv2.rectangle(
        screenshot_bgr,
        (int(w_scr * 0.70), 0),
        (w_scr, int(h_scr * 0.50)),
        (0, 0, 0),
        -1,
    )

    for sickle_file in SICKLE_TEMPLATES:
        template_bgr, template_mask = load_image_safe_with_alpha(sickle_file)
        if template_bgr is None:
            continue

        if template_mask is not None:
            result = cv2.matchTemplate(
                screenshot_bgr,
                template_bgr,
                cv2.TM_CCORR_NORMED,
                mask=template_mask,
            )
        else:
            result = cv2.matchTemplate(
                screenshot_bgr, template_bgr, cv2.TM_CCOEFF_NORMED
            )

        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= confidence:
            h, w, _ = template_bgr.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            print(
                f" ⛏️ พบเคียวด้วยรูป: {sickle_file} (Score: {max_val:.2f}) ที่พิกัด ({center_x}, {center_y})"
            )
            return (center_x, center_y)

    return None
def load_image_safe_with_alpha(relative_path):
    """โหลดภาพคงค่า Alpha Channel ไว้สำหรับสแกนภาพโปร่งใส (เคียว)"""
    full_path = resource_path(relative_path)
    if not os.path.exists(full_path):
        return None, None

    try:
        with open(full_path, "rb") as f:
            file_bytes = bytearray(f.read())
        img_array = np.asarray(file_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)

        if img is None:
            return None, None

        if len(img.shape) == 3 and img.shape[2] == 4:
            bgr = img[:, :, :3]
            alpha = img[:, :, 3]
            return bgr, alpha
        else:
            return img, None
    except Exception as e:
        print(f"❌ Error loading image with alpha ({full_path}): {e}")
        return None, None

def harvest_and_plant_process():
    """ตรรกะหลัก: เกี่ยวข้าว -> ปลูกซ่อม"""
    print("\n🔍 กำลังสแกนฟาร์ม...")

    # 1. ตรวจหาข้าวสาลีสุก (ภาพสี)
    #ripe_pos = find_and_get_center(IMAGE_WHEAT_RIPE, confidence=0.72)

    ripe_pos = find_any_ripe_crop(confidence=0.68)

    if ripe_pos:
        print(f"✅ เจอแปลงข้าวสาลีสุกที่พิกัด {ripe_pos}!")

        pyautogui.click(ripe_pos[0], ripe_pos[1])
        time.sleep(0.6)

        # 2. ค้นหาเคียวแบบภาพสี (เปิด Mask ขวาบนป้องกันการคลิกหลุดไปขวาบน)
        #sickle_pos = find_and_get_center(IMAGE_SICKLE, confidence=0.60)
        sickle_pos = find_sickle(confidence=0.50)

        if sickle_pos:
            print(f" ⛏️ เจอเคียวที่ {sickle_pos}! กำลังลากเคียวเกี่ยวข้าว...")
            pyautogui.moveTo(sickle_pos[0], sickle_pos[1])
            pyautogui.drag(200, 250, duration=1.2, button="left")
            time.sleep(1.5)
        else:
            print(" ⚠️ ไม่พบไอคอนเคียว")

        plant_crops(ripe_pos)

    else:
        print("❌ ไม่พบข้าวสุก... กำลังสแกนหา 'แปลงดินว่าง'...")
        empty_soil_pos = find_any_empty_soil(confidence=0.65)

        if empty_soil_pos:
            plant_crops(empty_soil_pos)
        else:
            print("⏳ ไม่พบทั้งข้าวสุกและดินว่าง... รอรอบถัดไป")


# --- Main Program Loop ---
if __name__ == "__main__":
    print("=" * 60)
    print(" 🤖 บอท Hay Day (ระบบภาพสี RGB + ปิด Mask มุมขวาบนหนาแน่น)")
    print(" 💡 วิธีหยุดบอท: กดปุ่ม 'Q' หรือ สะบัดเมาส์ไปที่มุมซ้ายบนสุด")
    print("=" * 60)

    print("\nบอทจะเริ่มทำงานใน 5 วินาที...")
    time.sleep(5)

    try:
        while True:
            if keyboard.is_pressed("q"):
                print("\n🛑 ตรวจพบการกดปุ่ม 'Q' -> หยุดบอททันที!")
                break

            harvest_and_plant_process()

            wait_seconds = random.randint(5, 10)
            print(f"⏳ รอนาน {wait_seconds} วินาที...")

            for _ in range(wait_seconds):
                if keyboard.is_pressed("q"):
                    raise KeyboardInterrupt
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nระบบหยุดการทำงานเรียบร้อยครับ.")