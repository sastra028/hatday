import json
import os
import sys
import time
import keyboard
from pynput import mouse
import pyautogui

# ป้องกัน pyautogui ช้าเกินไป
pyautogui.PAUSE = 0.01

MACRO_FILE = "hayday_macro.json"
events = []
recording = False
start_time = 0
drag_start_pos = None


# ==========================================
# 🔴 1. RECORDING SYSTEM (ระบบบันทึก)
# ==========================================
def on_click(x, y, button, pressed):
    global recording, start_time, drag_start_pos
    if not recording:
        return

    current_time = time.time() - start_time

    if pressed:
        # บันทึกจุดที่เริ่มกดเมาส์ลง
        drag_start_pos = (x, y, current_time)
    else:
        # เมื่อปล่อยเมาส์
        if drag_start_pos:
            start_x, start_y, start_t = drag_start_pos
            duration = current_time - start_t

            # เช็กว่าเป็น "การลาก" หรือ "การคลิกธรรมดา"
            if abs(x - start_x) > 5 or abs(y - start_y) > 5:
                # การลาก (Drag)
                events.append(
                    {
                        "type": "drag",
                        "start_x": start_x,
                        "start_y": start_y,
                        "end_x": x,
                        "end_y": y,
                        "delay": start_t,
                        "duration": max(duration, 0.2),
                    }
                )
                print(
                    f" 📝 [Record Drag] จาก ({start_x}, {start_y}) ไป ({x}, {y}) [ระยะเวลา: {duration:.2f}s]"
                )
            else:
                # การคลิก (Click)
                events.append(
                    {"type": "click", "x": x, "y": y, "delay": start_t}
                )
                print(f" 📝 [Record Click] ที่ ({x}, {y})")

            drag_start_pos = None


def start_recording():
    global recording, start_time, events
    events = []
    recording = True
    start_time = time.time()
    print("\n🔴 [REC] เริ่มบันทึกการเล่นแล้ว! ทำการเกี่ยวข้าว/ปลูกผักได้เลย...")


def stop_recording():
    global recording
    if recording:
        recording = False
        print("⏹️ [STOP] หยุดบันทึก!")
        # บันทึกลงไฟล์ JSON
        with open(MACRO_FILE, "w") as f:
            json.dump(events, f, indent=2)
        print(
            f"💾 เซฟ Action ทั้งหมด {len(events)}รายการ ลงใน {MACRO_FILE} เรียบร้อย!"
        )


# ==========================================
# ▶️ 2. PLAYBACK SYSTEM (ระบบรันซ้ำ)
# ==========================================
def play_macro():
    if not os.path.exists(MACRO_FILE):
        print(f"❌ ไม่พบไฟล์ {MACRO_FILE} ! กรุณากดบันทึกก่อน (F8)")
        return

    with open(MACRO_FILE, "r") as f:
        macro_events = json.load(f)

    print("\n▶️ [PLAY] เริ่มรันการเล่นซ้ำ... (กด 'ESC' เพื่อหยุดโปรแกรม)")

    last_time = 0
    for action in macro_events:
        if keyboard.is_pressed("esc"):
            print("🛑 หยุดการรัน Macro")
            break

        # คำนวณเวลารอ (Delay) ระหว่าง Action
        delay = action["delay"] - last_time
        if delay > 0:
            time.sleep(delay)
        last_time = action["delay"]

        # ทำตาม Action
        if action["type"] == "click":
            pyautogui.click(action["x"], action["y"])
        elif action["type"] == "drag":
            pyautogui.moveTo(action["start_x"], action["start_y"])
            pyautogui.dragTo(
                action["end_x"],
                action["end_y"],
                duration=action["duration"],
                button="left",
            )


# ==========================================
# 🚀 MAIN LOOP
# ==========================================
if __name__ == "__main__":
    print("==========================================")
    print("🎮 HayDay Macro Recorder & Player")
    print("==========================================")
    print(" [F8]  : เริ่ม / หยุด บันทึกการเล่น (Record/Stop)")
    print(" [F9]  : รันการเล่นซ้ำ 1 รอบ (Play Once)")
    print(" [F10] : รันวนลูปไปเรื่อยๆ (Loop Play)")
    print(" [ESC] : ปิดโปรแกรม")
    print("==========================================\n")

    # เริ่ม Listener ฟังเสียงเมาส์ใน Background
    listener = mouse.Listener(on_click=on_click)
    listener.start()

    try:
        while True:
            # กด F8 สลับ เริ่ม/หยุด บันทึก
            if keyboard.is_pressed("f8"):
                if not recording:
                    start_recording()
                else:
                    stop_recording()
                time.sleep(0.5)  # กันกดเบิ้ล

            # กด F9 เล่นซ้ำ 1 รอบ
            elif keyboard.is_pressed("f9"):
                play_macro()
                time.sleep(0.5)

            # กด F10 เล่นซ้ำวนลูปเรื่อยๆ
            elif keyboard.is_pressed("f10"):
                print("🔄 [LOOP MODE] เริ่มทำงานวนลูปไร้ขีดจำกัด...")
                while not keyboard.is_pressed("esc"):
                    play_macro()
                    time.sleep(1)  # หน่วงเวลาก่อนเริ่มรอบใหม่
                print("🛑 หยุด Loop")
                time.sleep(0.5)

            elif keyboard.is_pressed("esc"):
                print("👋 ปิดโปรแกรม")
                sys.exit()

            time.sleep(0.05)

    except KeyboardInterrupt:
        pass