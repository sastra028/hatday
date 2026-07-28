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

# 1. URL สำหรับอ่าน Whitelist หลัก
GITHUB_WHITELIST_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}/whitelist.json"


# ==========================================
# 🔍 HARDWARE KEY FUNCTIONS
# ==========================================


def load_config():
    # กำหนด path ของไฟล์ config.json
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")

    if not os.path.exists(config_path):
        # รองรับกรณีวาง config.json ไว้ในโฟลเดอร์เดียวกับ main.py
        config_path = "config.json"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: ไม่พบไฟล์ config.json กรุณาสร้างไฟล์และใส่ github_token")
        return {}


def get_mac_address():
    """ดึง MAC Address ของเครื่องในรูปแบบ XX:XX:XX:XX:XX:XX"""
    mac_num = hex(uuid.getnode())[2:].zfill(12)
    mac_str = ":".join(mac_num[i : i + 2] for i in range(0, 11, 2)).upper()
    return mac_str


def generate_hardware_key():
    """สร้าง Key ผูกเครื่อง: ComputerName_MACAddress"""
    computer_name = socket.gethostname().upper()
    mac_address = get_mac_address()
    return f"{computer_name}_{mac_address}"


# ==========================================
# 📝 AUTO-REGISTER FUNCTION
# ==========================================
def register_pending_license(my_key):
    """ส่ง Hardware Key ไปสร้างเป็นไฟล์ JSON ใหม่ในโฟลเดอร์ requests/ บน GitHub"""
    print("\n⏳ Auto-registering this machine to GitHub...")

    computer_name = socket.gethostname().upper()
    file_name = f"requests/{my_key}.json"
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{file_name}"
    config = load_config()
    GITHUB_TOKEN = config.get("github_token", "")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }

    # เช็กก่อนว่าเคยส่ง Request ไปหรือยัง เพื่อป้องกันการยิงซ้ำ
    check_req = requests.get(api_url, headers=headers, timeout=10)
    if check_req.status_code == 200:
        print(
            "📌 Registration Request already submitted! Waiting for Admin approval."
        )
        return

    # สร้าง Payload ข้อมูลเครื่องลงทะเบียน
    payload_data = {
        "key": my_key,
        "hostname": computer_name,
        "mac": get_mac_address(),
        "request_date": datetime.date.today().strftime("%d-%m-%Y"),
        "status": "pending_approval",
    }

    # แปลง JSON เป็น Base64 ตามข้อกำหนดของ GitHub API
    json_str = json.dumps(payload_data, indent=2)
    encoded_content = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")

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
            print(
                f"📝 Successfully registered key ({my_key}) to GitHub requests/"
            )
            print("📣 Please inform the Admin to approve your license.")
        else:
            print(
                f"⚠️ Auto-register failed (GitHub API HTTP {response.status_code})"
            )
    except Exception as e:
        print(f"⚠️ Failed to send registration request: {e}")


# ==========================================
# 🛡️ LICENSE CHECK FUNCTION
# ==========================================
def check_license():
    """ตรวจสอบ License กับไฟล์ JSON บน GitHub"""
    my_key = generate_hardware_key()
    print(f"🔍 Your Hardware Key: {my_key}")
    print("⏳ Checking license status with GitHub...")

    try:
        # เติม Timestamp ใน Query Param เพื่อกันปัญหา Cache ของ GitHub Raw
        cache_buster_url = f"{GITHUB_WHITELIST_URL}?t={int(time.time())}"
        response = requests.get(cache_buster_url, timeout=10)

        if response.status_code != 200:
            print("❌ Error: Cannot fetch whitelist from GitHub server.")
            return False

        whitelist = response.json()

        # ค้นหา Key ใน Whitelist
        user_license = next(
            (item for item in whitelist if item.get("key") == my_key), None
        )

        # หากไม่พบ Key ให้ทำการส่งเรื่องขออนุมัติ Auto-Register ทันที
        if not user_license:
            print(
                "❌ Access Denied: This machine is not registered in the Whitelist."
            )
            register_pending_license(my_key)
            return False

        # เช็กสถานะ Status
        if user_license.get("status") != "active":
            print(
                "❌ Access Denied: Your license has been suspended/disabled."
            )
            return False

        # เช็กวันหมดอายุ (รูปแบบ DD-MM-YYYY)
        expire_str = user_license.get("expire")
        expire_date = datetime.datetime.strptime(expire_str, "%d-%m-%Y").date()
        today = datetime.date.today()

        if today > expire_date:
            print(f"❌ Access Denied: Your license expired on {expire_str}.")
            return False

        # คำนวณวันคงเหลือ
        days_left = (expire_date - today).days
        print(
            f"✅ License Verified! Status: Active (Expires: {expire_str} | Remaining: {days_left} days)"
        )
        return True

    except requests.exceptions.RequestException:
        print("⚠️ Connection Error: Please check your internet connection.")
        return False
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


# เปิดระบบ Safety: สะบัดเมาส์ไปมุมซ้ายบนสุดของจอคอมเพื่อหยุดทันที
pyautogui.FAILSAFE = True

# --- ตั้งค่าชื่อไฟล์รูปภาพแม่แบบ ---
IMAGE_WHEAT_RIPE = "wheat_ripe.png"  # รูปแปลงข้าวสาลีสุก (สีเหลืองทอง)
IMAGE_SICKLE = "sickle.png"  # รูปไอคอนเคียว
IMAGE_SEED = (
    "wheat_seed.png"  # รูปไอคอนพืชที่จะปลูก (ถุงข้าวสาลี หรือ ข้าวโพด)
)

# รายชื่อไฟล์แปลงดินว่าง (รองรับ 2 ลายทแยง)
SOIL_TEMPLATES = ["empty_soil1.png", "empty_soil2.png"]


def resource_path(relative_path):
    """ดึง Absolute Path ของไฟล์ รองรับทั้งรัน .py ปกติ และรันผ่าน PyInstaller .exe"""
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


def load_image_safe_gray(relative_path):
    """อ่านรูปภาพและแปลงเป็น ขาวดำ (Grayscale) ทันที
    เพื่อแก้ปัญหาแสงสะท้อนโปร่งใสและสีเพี้ยน
    """
    full_path = resource_path(relative_path)

    if not os.path.exists(full_path):
        print(f"❌ File not found: {full_path}")
        return None

    try:
        with open(full_path, "rb") as f:
            file_bytes = bytearray(f.read())

        img_array = np.asarray(file_bytes, dtype=np.uint8)

        # โหลดเป็น BGR ปกติก่อน
        img_bgr = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img_bgr is None:
            print(f"⚠️ Warning: Could not decode image at {full_path}")
            return None

        # ⚡ แปลงเป็นภาพขาวดำ (Grayscale)
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        return img_gray

    except Exception as e:
        print(f"❌ Error loading template ({full_path}): {e}")
        return None


# ==========================================
# 🎯 MAIN MATCHING FUNCTIONS (GRAYSCALE)
# ==========================================
def apply_ui_mask(screenshot_gray):
    """ฟังก์ชันถมสีดำ (Mask Out) ปิดมุมจอและ UI ทั้งหมด 
    เพื่อบีบพื้นที่สแกนให้เหลือแค่โซนแปลงผักกลางจอเท่านั้น
    """
    h_scr, w_scr = screenshot_gray.shape

    # 🚫 1. มุมขวาบน (ขยายพิกัดครอบคลุม เหรียญ/เพชร/เตาอบ/โปรโมชัน)
    cv2.rectangle(screenshot_gray, (int(w_scr * 0.65), 0), (w_scr, int(h_scr * 0.50)), (0), -1)

    # 🚫 2. มุมซ้ายบน + ถนน + รถส่งของ
    cv2.rectangle(screenshot_gray, (0, 0), (int(w_scr * 0.50), int(h_scr * 0.55)), (0), -1)

    # 🚫 3. มุมซ้ายล่าง (ปุ่มร้านค้า)
    cv2.rectangle(screenshot_gray, (0, int(h_scr * 0.75)), (int(w_scr * 0.20), h_scr), (0), -1)

    # 🚫 4. มุมขวาล่าง (ปุ่มเพื่อน + ม้านั่ง/พุ่มไม้)
    cv2.rectangle(screenshot_gray, (int(w_scr * 0.75), int(h_scr * 0.70)), (w_scr, h_scr), (0), -1)

    return screenshot_gray


def find_and_get_center(template_path, confidence=0.75):
    """ค้นหารูปแปลงดิน / ข้าวสุก (ปิด UI รอบนอก)"""
    template_gray = load_image_safe_gray(template_path)
    if template_gray is None:
        return None

    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

    # 🛡️ ตัดมุมจอออกด้วย Mask ใหม่
    screenshot_masked = apply_ui_mask(screenshot_gray)

    result = cv2.matchTemplate(screenshot_masked, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        h, w = template_gray.shape
        center_x = max_loc[0] + w // 2 + random.randint(-3, 3)
        center_y = max_loc[1] + h // 2 + random.randint(-3, 3)
        return (center_x, center_y)

    return None


def find_template_clean_gray(template_path, confidence=0.55):
    """ค้นหาเคียว / เมล็ดพันธุ์ (ครอบ Mask ป้องกันไม่ให้ไปสแกนเจอขวาบน)"""
    template_gray = load_image_safe_gray(template_path)
    if template_gray is None:
        return None

    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    screenshot_gray = cv2.cvtColor(screenshot_bgr, cv2.COLOR_BGR2GRAY)

    # 🛡️ ถมสีดำตัดมุมขวาบนออกด้วยเช่นกัน
    screenshot_masked = apply_ui_mask(screenshot_gray)

    result = cv2.matchTemplate(screenshot_masked, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= confidence:
        h, w = template_gray.shape
        center_x = max_loc[0] + w // 2 + random.randint(-2, 2)
        center_y = max_loc[1] + h // 2 + random.randint(-2, 2)
        return (center_x, center_y)

    return None


def find_any_empty_soil(confidence=0.65):
    """สแกนหาแปลงดินว่างจากรูปทั้ง 2 ลาย"""
    for soil_img in SOIL_TEMPLATES:
        pos = find_and_get_center(soil_img, confidence=confidence)
        if pos:
            print(f"🤎 เจอแปลงดินว่าง (ลาย: {soil_img}) ที่พิกัด {pos}")
            return pos
    return None


def plant_crops(soil_pos):
    """ฟังก์ชันกระบวนการปลูกพืช"""
    print(f" 🌱 เริ่มกระบวนการปลูกพืชที่พิกัดดินว่าง {soil_pos}...")

    # 1. คลิกที่พิกัดแปลงดินว่างเพื่อเปิดเมนูพืช
    pyautogui.click(soil_pos[0], soil_pos[1])
    time.sleep(0.8)  # รอเมนูพืชเด้ง

    # 2. ค้นหาภาพไอคอนพืชแบบ Clean Grayscale (ลด confidence ลงเหลือ 0.55 เพื่อรองรับแสงสะท้อน)
    seed_pos = find_template_clean_gray(IMAGE_SEED, confidence=0.55)

    if not seed_pos:
        seed_x = soil_pos[0] - 80
        seed_y = soil_pos[1] - 50
        seed_pos = (seed_x, seed_y)
        print(
            f" ⚠️ สแกนหาภาพพืชไม่พบ -> ใช้พิกัดไอคอนอ้างอิงจากแปลงดิน: {seed_pos}"
        )
    else:
        print(f" 🌾 พบภาพพืชที่พิกัด: {seed_pos}")

    # 3. จังหวะลากปลูก
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


def harvest_and_plant_process():
    """ตรรกะหลัก: เช็กข้าวสุกก่อนเกี่ยว -> ถ้าไม่มี ให้สแกนหาดินว่างเพื่อสั่งปลูก"""
    print("\n🔍 กำลังสแกนฟาร์ม...")

    # --- CASE 1: ตรวจหาข้าวสาลีสุก ---
    ripe_pos = find_and_get_center(IMAGE_WHEAT_RIPE, confidence=0.70)

    if ripe_pos:
        print(f"✅ เจอแปลงข้าวสาลีสุกที่พิกัด {ripe_pos}!")

        # คลิกเปิดเมนูเคียว
        pyautogui.click(ripe_pos[0], ripe_pos[1])
        time.sleep(0.6)

        # ⛏️ ค้นหาเคียวด้วยวิธี Clean Grayscale (ไม่ทับ Mask + ทนแสงสะท้อน)
        sickle_pos = find_template_clean_gray(IMAGE_SICKLE, confidence=0.55)

        if sickle_pos:
            print(f" ⛏️ เจอเคียวที่ {sickle_pos}! กำลังลากเคียวเกี่ยวข้าว...")
            pyautogui.moveTo(sickle_pos[0], sickle_pos[1])
            pyautogui.drag(200, 250, duration=1.2, button="left")  # ลากเฉียงลง
            time.sleep(1.5)  # รอแอนิเมชันเกี่ยวเสร็จ
        else:
            print(" ⚠️ ไม่พบไอคอนเคียว")

        # เกี่ยวเสร็จ -> สั่งปลูกต่อทันที
        plant_crops(ripe_pos)

    else:
        # --- CASE 2: สแกนหาแปลงดินว่าง ---
        print("❌ ไม่พบข้าวสุก... กำลังสแกนหา 'แปลงดินว่าง'...")
        empty_soil_pos = find_any_empty_soil(confidence=0.65)

        if empty_soil_pos:
            plant_crops(empty_soil_pos)
        else:
            print("⏳ ไม่พบทั้งข้าวสุกและดินว่าง... รอรอบถัดไป")



def harvest_and_plant_process_2():
    """ตรรกะหลัก: เช็กข้าวสุกก่อนเกี่ยว -> ถ้าไม่มี ให้สแกนหาดินว่างเพื่อสั่งปลูก"""
    print("\n🔍 กำลังสแกนฟาร์ม...")

    # --- CASE 2: สแกนหาแปลงดินว่าง ---
    empty_soil_pos = find_any_empty_soil(confidence=0.65)

    if empty_soil_pos:
        print("❌ ไม่พบข้าวสุก... กำลังสแกนหา 'แปลงดินว่าง'...")
        plant_crops(empty_soil_pos)
    else:
        # --- CASE 1: ตรวจหาข้าวสาลีสุก ---
        ripe_pos = find_and_get_center(IMAGE_WHEAT_RIPE, confidence=0.70)

        if ripe_pos:
            print(f"✅ เจอแปลงข้าวสาลีสุกที่พิกัด {ripe_pos}!")

            # คลิกเปิดเมนูเคียว
            pyautogui.click(ripe_pos[0], ripe_pos[1])
            time.sleep(0.6)

            # ⛏️ ค้นหาเคียวด้วยวิธี Clean Grayscale (ไม่ทับ Mask + ทนแสงสะท้อน)
            sickle_pos = find_template_clean_gray(IMAGE_SICKLE, confidence=0.55)

            if sickle_pos:
                print(f" ⛏️ เจอเคียวที่ {sickle_pos}! กำลังลากเคียวเกี่ยวข้าว...")
                pyautogui.moveTo(sickle_pos[0], sickle_pos[1])
                pyautogui.drag(200, 250, duration=1.2, button="left")  # ลากเฉียงลง
                time.sleep(1.5)  # รอแอนิเมชันเกี่ยวเสร็จ
            else:
                print(" ⚠️ ไม่พบไอคอนเคียว")

            # เกี่ยวเสร็จ -> สั่งปลูกต่อทันที
            plant_crops(ripe_pos)

        else:
            # --- CASE 2: สแกนหาแปลงดินว่าง ---
            print("❌ ไม่พบข้าวสุก... กำลังสแกนหา 'แปลงดินว่าง'...")

# --- Main Program Loop ---
if __name__ == "__main__":
    print("=" * 60)
    print(
        " 🤖 บอท Hay Day (ระบบ Grayscale Matching ทนแสงสะท้อนโปร่งใส 100%)"
    )
    print(" 💡 วิธีหยุดบอท:")
    print("    1. กดปุ่ม 'Q' บนคีย์บอร์ด ได้ตลอดเวลา")
    print("    2. สะบัดเมาส์ไปที่ 'มุมซ้ายบนสุดของหน้าจอ'")
    print("=" * 60)

    print("\nบอทจะเริ่มทำงานใน 5 วินาที...")
    time.sleep(5)

    try:
        while True:
            if keyboard.is_pressed("q"):
                print("\n🛑 ตรวจพบการกดปุ่ม 'Q' -> หยุดบอททันที!")
                break

            # รันกระบวนการทำฟาร์ม
            harvest_and_plant_process_2()

            # เวลารอ
            wait_seconds = random.randint(5, 10)
            print(f"⏳ รอนาน {wait_seconds} วินาที...")

            for _ in range(wait_seconds):
                if keyboard.is_pressed("q"):
                    raise KeyboardInterrupt
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nระบบหยุดการทำงานเรียบร้อยครับ.")