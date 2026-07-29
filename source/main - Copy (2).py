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


# ==========================================
# ⚙️ CONFIG & CONSTANTS
# ==========================================
SOIL_TEMPLATES = ["empty_soil1.png", "empty_soil2.png"]
CORN_SEED_TEMPLATES = ["wheat_seed.png", "corn_seed.png"]  # เมล็ดพืชที่จะปลูก
SICKLE_TEMPLATES = ["sickle.png", "sickle1.png", "sickle2.png" "sickle3.png" "sickle4.png"]
CROP_RIPE_TEMPLATES = ["wheat_ripe.png", "wheat_ripe_2.png", "wheat_ripe_3.png"]
POPUP_CLOSE_TEMPLATES = ["close_btn.png", "ok_btn.png", "x_button.png"]

IGNORE_TEMPLATES = [
    "ignore_shop.png",
    "1.png",
    "2.png",
    "3.png"
]


pyautogui.FAILSAFE = True

# ==========================================
# 🛠️ HELPER FUNCTIONS
# ==========================================
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
    full_path = resource_path(relative_path)
    if not os.path.exists(full_path):
        return None
    try:
        with open(full_path, "rb") as f:
            file_bytes = bytearray(f.read())
        img_array = np.asarray(file_bytes, dtype=np.uint8)
        return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    except Exception:
        return None

def load_image_safe_with_alpha(relative_path):
    full_path = resource_path(relative_path)
    if not os.path.exists(full_path):
        return None, None
    try:
        with open(full_path, "rb") as f:
            file_bytes = bytearray(f.read())
        img_array = np.asarray(file_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_UNCHANGED)
        if img is not None and len(img.shape) == 3 and img.shape[2] == 4:
            return img[:, :, :3], img[:, :, 3]
        return img, None
    except Exception:
        return None, None

# ==========================================
# 🚨 POPUP SCANNER & AUTO CLOSE
# ==========================================
def check_and_close_popups():
    """*** ตรวจสอบ Popup/กากบาทเด้งขึ้นมาแทรก และทำการคลิกปิดทันที ***"""
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    for popup_file in POPUP_CLOSE_TEMPLATES:
        template = load_image_safe(popup_file)
        if template is None:
            continue

        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.70:
            h, w, _ = template.shape
            btn_x = max_loc[0] + w // 2
            btn_y = max_loc[1] + h // 2
            print(f"🚨 ตรวจพบ Popup/กากบาท ({popup_file}) -> กำลังคลิกปิดที่ ({btn_x}, {btn_y})")
            pyautogui.click(btn_x, btn_y)
            time.sleep(0.5)
            return True
    return False

# ==========================================
# 📌 STEP 1: SCAN & REMEMBER ALL SOIL POSITIONS
# ==========================================
def scan_all_soils(confidence=0.50, min_dist=25):
    """สแกนหาแปลงดินว่างทั้งหมด พร้อมระบบ Debug ค่า Score"""
    check_and_close_popups()
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    found_points = []
    soil_height = 0
    soil_width = 0

    for soil_img in SOIL_TEMPLATES:
        template = load_image_safe(soil_img)
        if template is None:
            print(f"⚠️ โหลดไฟล์แม่แบบไม่สำเร็จ: {soil_img}")
            continue

        h, w, _ = template.shape

        result = cv2.matchTemplate(
            screenshot_bgr, template, cv2.TM_CCOEFF_NORMED
        )
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # 🔍 Print ดูค่าความเหมือนสูงสุดที่สแกนเจอ
        print(f"🔍 สแกน {soil_img} -> ค่าความเหมือนสูงสุด (Best Match Score): {max_val:.2f}")

        locs = np.where(result >= confidence)

        for pt in zip(*locs[::-1]):
            center_x = pt[0] + w // 2
            center_y = pt[1] + h // 2

            # NMS Filter
            if not any(
                np.hypot(center_x - px, center_y - py) < min_dist
                for px, py in found_points
            ):
                found_points.append((center_x, center_y))
                soil_height, soil_width = h, w

    if not found_points:
        return [], 0, 0

    # เรียงลำดับพิกัดจากซ้ายบนไปขวาล่าง
    found_points.sort(key=lambda p: (p[1] // 25, p[0]))
    print(f"📍 สแกนพบแปลงดินว่างทั้งหมด {len(found_points)} แปลง")
    return found_points, soil_width, soil_height

# ==========================================
# 🚜 DRAGGING PATH FUNCTION
# ==========================================
def drag_smooth_path(start_pos, target_points):
    """ลากเมาส์แบบต่อเนื่องจากจุดเริ่มต้น ผ่านทุกแปลงตามลำดับ"""
    if not start_pos or not target_points:
        return

    pyautogui.moveTo(start_pos[0], start_pos[1], duration=0.25)
    pyautogui.mouseDown(button="left")
    time.sleep(0.15)

    for pt in target_points:
        pyautogui.moveTo(pt[0], pt[1], duration=0.12)

    pyautogui.mouseUp(button="left")
    time.sleep(0.3)

# ==========================================
# 🔍 SEARCH SEED & SICKLE NEAR TOP-LEFT SOIL
# ==========================================
def find_seed_above_soil(top_left_soil, soil_height):
    """สแกนหาเมล็ดข้าวโพดฝั่งซ้ายบน สูงกว่าแปลงประมาณ 2 เท่า"""
    check_and_close_popups()
    
    # กำหนด Bounding Box ค้นหาบริเวณซ้ายบนเหนือแปลง
    search_center_x = top_left_soil[0] - 80
    search_center_y = top_left_soil[1] - (soil_height * 2)
    
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    for seed_file in CORN_SEED_TEMPLATES:
        template = load_image_safe(seed_file)
        if template is None:
            continue

        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.55:
            h, w, _ = template.shape
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)

    # Fallback: หากสแกนรูปไม่ติด ให้คืนพิกัดประมาณการด้านซ้ายบนสูงขึ้น 2 เท่า
    return (search_center_x, search_center_y)

def find_sickle_near_soil(top_left_soil):
    """สแกนหาเคียวบริเวณมุมซ้ายบนของแปลง"""
    check_and_close_popups()
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    for sickle_file in SICKLE_TEMPLATES:
        template_bgr, template_mask = load_image_safe_with_alpha(sickle_file)
        if template_bgr is None:
            continue

        if template_mask is not None:
            result = cv2.matchTemplate(screenshot_bgr, template_bgr, cv2.TM_CCORR_NORMED, mask=template_mask)
        else:
            result = cv2.matchTemplate(screenshot_bgr, template_bgr, cv2.TM_CCOEFF_NORMED)

        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.50:
            h, w, _ = template_bgr.shape
            return (max_loc[0] + w // 2, max_loc[1] + h // 2)

    # Fallback: เยื้องซ้ายบนเล็กน้อย
    return (top_left_soil[0] - 50, top_left_soil[1] - 40)

# ==========================================
# 🌾 CHECK RIPE CROPS AT ELEVATED POSITIONS
# ==========================================
def check_all_crops_ripe(soil_positions, soil_height, confidence=0.60):
    """สแกนหาข้าวโพดสุก เฉพาะบริเวณเหนือแปลงขึ้นไปประมาณ 1 เท่าความสูง"""
    check_and_close_popups()
    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    ripe_count = 0
    for soil_pt in soil_positions:
        # พิกัดสแกน: ความสูงเพิ่มขึ้นประมาณ 1 เท่า (+Y ขึ้นด้านบน)
        crop_target_y = soil_pt[1] - soil_height
        crop_target_x = soil_pt[0]

        # ครอปเฉพาะ Bounding Box รอบแปลงผักนั้นๆ มาสแกน
        y1, y2 = max(0, crop_target_y - 40), min(screenshot_bgr.shape[0], crop_target_y + 40)
        x1, x2 = max(0, crop_target_x - 40), min(screenshot_bgr.shape[1], crop_target_x + 40)
        crop_roi = screenshot_bgr[y1:y2, x1:x2]

        is_ripe = False
        for ripe_file in CROP_RIPE_TEMPLATES:
            template = load_image_safe(ripe_file)
            if template is None or crop_roi.shape[0] < template.shape[0] or crop_roi.shape[1] < template.shape[1]:
                continue

            result = cv2.matchTemplate(crop_roi, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)

            if max_val >= confidence:
                is_ripe = True
                break

        if is_ripe:
            ripe_count += 1

    print(f"🌾 สแกนตรวจสอบ: ข้าวโพดสุกแล้ว {ripe_count} / {len(soil_positions)} แปลง")
    return ripe_count >= len(soil_positions)

# ==========================================
# 🚜 SAFE DRAG FUNCTION
# ==========================================
def safe_drag_to_target(start_pos, target_pos, duration=0.6):
    """ฟังก์ชันลากปลอดภัย: ลากจากจุด start (ไอคอนเคียว/เมล็ด) ไปยัง target (แปลงผัก) โดยตรง
    เพื่อป้องกันไม่ให้เมาส์ลากหลุดออกนอกกรอบจอ
    """
    if not start_pos or not target_pos:
        print("⚠️ พิกัดเริ่มต้นหรือเป้าหมายไม่ถูกต้อง ไม่สามารถลากได้")
        return

    # 1. เลื่อนเมาส์ไปที่จุดเริ่มต้น (ไอคอนเคียว หรือ เมล็ดพืช)
    pyautogui.moveTo(start_pos[0], start_pos[1], duration=0.25)
    time.sleep(0.1)

    # 2. กดเมาส์ซ้ายค้างไว้
    pyautogui.mouseDown(button="left")
    time.sleep(0.15)

    # 3. ลากเมาส์ไปยังจุดเป้าหมาย (แปลงผัก)
    pyautogui.moveTo(target_pos[0], target_pos[1], duration=duration)
    time.sleep(0.1)

    # 4. ปล่อยเมาส์
    pyautogui.mouseUp(button="left")
    time.sleep(0.2)
    
# ==========================================
# 🔄 MAIN LOOP WORKFLOW
# ==========================================
def main_automation_loop():
    print("\n---------------------------------------------------")
    print("🚀 เริ่มสแกนค้นหาแปลงดินเริ่มต้นเพื่อบันทึกพิกัด...")
    print("---------------------------------------------------")

    screenshot = pyautogui.screenshot()
    screenshot_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    found_points = []
    s_height, s_width = 0, 0

    # 🎯 ในรอบแรกเราจะหาแปลงดิน "ตัวแรกสุดที่คะแนนสูงสุด" มาอ้างอิงก่อน
    top_match_val = -1
    best_loc = None

    for soil_img in SOIL_TEMPLATES:
        template = load_image_safe(soil_img)
        if template is None:
            continue

        h, w, _ = template.shape
        
        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # คืนค่า Score สูงสุดที่เจอ
        print(f"🔍 สแกน {soil_img} -> ค่า Best Match Score: {max_val:.2f}")

        # เก็บพิกัดตัวที่คะแนนสูงที่สุด
        if max_val > top_match_val:
            top_match_val = max_val
            best_loc = max_loc
            s_height, s_width = h, w

    # 🛡️ เช็ก Confidence (ปรับลดลงเหลือ 0.40 ถ้ารูปใหม่ยังไม่ตรงมาก)
    if top_match_val < 0.45 or best_loc is None:
        print(f"❌ ไม่พบแปลงดินว่างที่ชัดเจนเลย (Best Match Score ต่ำเกินไป: {top_match_val:.2f})")
        print("💡 แนะนำให้แคปรูป 'empty_soil1.png' ใหม่จากหน้าจอจริงของคุณครับ")
        return

    # พิกัดแปลงซ้ายบนสุด (ที่เราเจอด้วยคะแนนสูงสุด)
    top_left_soil = (best_loc[0] + s_width // 2, best_loc[1] + s_height // 2)
    print(f"📌 บันทึกพิกัดแปลงดินซ้ายบนสุดสำเร็จที่: {top_left_soil}")

    # --- สำหรับการปลูก/เกี่ยว เราจะใช้พิกัดประมาณการ (เพราะเรายังสแกนหาไม่ครบทุกแปลง) ---
    # * บอทจะใช้ safe_drag_to_target ระหว่างจุดไอคอนกับ top_left_soil ตรงๆ *

    while True:
        if keyboard.is_pressed("q"):
            print("🛑 หยุดบอทด้วยปุ่ม Q")
            break

        check_and_close_popups()

        # ข้อ 2: คลิกแปลงซ้ายบนสุด
        print(f"\n👉 [ข้อ 2] คลิกแปลงซ้ายบนสุดที่ {top_left_soil}")
        pyautogui.click(top_left_soil[0], top_left_soil[1])
        time.sleep(0.6)

        # ข้อ 3: สแกนหาเมล็ดข้าวโพด
        # (เราใช้ฟังก์ชันหาประมาณการจาก top_left_soil ใน fallback ของ find_seed_above_soil)
        seed_pos = find_seed_above_soil(top_left_soil, s_height)
        print(f"🌽 [ข้อ 3] พบพิกัดเมล็ดข้าวโพดที่: {seed_pos}")

        # ข้อ 4: ลากเมล็ดข้าวโพดไปปล่อยลงบนแปลงดินตรงๆ (ลากทีเดียวอยู่กรอบ 100%)
        print(f"🚜 [ข้อ 4] กำลังลากเมล็ดปลูกจาก {seed_pos} ไป {top_left_soil}...")
        safe_drag_to_target(seed_pos, top_left_soil, duration=0.6)
        time.sleep(1.0)

        # ข้อ 5: Loop รอดูข้าวโพดสุก (ประมาณ 5 นาที)
        print("⏳ [ข้อ 5] กำลังรอข้าวโพดสุก...")
        # เราสแกนตรวจสอบจุดเดิม top_left_soil โดยบวก offset ขึ้นไป
        time.sleep(300) # รอ 5 นาทีสำหรับข้าวโพด

        # ข้อ 6: เมื่อสุกแล้วให้คลิกแปลงซ้ายบนสุด
        print(f"👉 [ข้อ 6] คลิกแปลงซ้ายบนสุดที่ {top_left_soil}")
        pyautogui.click(top_left_soil[0], top_left_soil[1])
        time.sleep(0.6)

        # ข้อ 7: สแกนหาเคียว
        sickle_pos = find_sickle_near_soil(top_left_soil)
        print(f"⛏️ [ข้อ 7] พบพิกัดเคียวที่: {sickle_pos}")

        # ข้อ 8: ลากเคียวไปเกี่ยวที่แปลงดินตรงๆ
        print(f"🚜 [ข้อ 8] กำลังลากเคียวไปเกี่ยวที่ {top_left_soil}...")
        safe_drag_to_target(sickle_pos, top_left_soil, duration=0.6)
        time.sleep(1.5)

        # ข้อ 9: ทำวนกลับไปทำข้อ 2 ใหม่
        print("🔄 [ข้อ 9] เกี่ยวเสร็จสิ้น จบรอบ! เริ่มต้นทำข้อ 2 ใหม่...")

if __name__ == "__main__":
    print("🤖 เริ่มต้นบอท Hay Day (Sequential Path Dragging)")
    print("💡 กด 'Q' บนคีย์บอร์ดเพื่อหยุดการทำงาน")
    print("\nบอทจะเริ่มทำงานใน 5 วินาที...")
    time.sleep(5)
    try:
        main_automation_loop()
    except KeyboardInterrupt:
        print("\nระบบหยุดการทำงานเรียบร้อยครับ.")
