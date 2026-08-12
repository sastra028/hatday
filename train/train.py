import glob
import json
import os
from ultralytics import YOLO

# --------------------------------------------------
# 1. ระบุชื่อ Class ให้ตรงกับที่ตั้งใน AnyLabeling
# --------------------------------------------------
CLASSES = ["empty plot", "empty_plot"]  # ใส่ดักไว้ทั้งแบบมี space และ underscore

# ดึงโฟลเดอร์ปัจจุบันที่ไฟล์ run.py ตั้งอยู่
working_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(working_dir)

print(f"📂 กำลังทำงานอยู่ในโฟลเดอร์: {working_dir}")

# --------------------------------------------------
# 2. แปลงไฟล์ JSON เป็น YOLO (.txt)
# --------------------------------------------------
json_files = glob.glob("*.json")
print(f"🔍 พบไฟล์ .json ทั้งหมด: {len(json_files)} ไฟล์")

converted_count = 0
total_boxes = 0

for json_file in json_files:
    txt_file = os.path.splitext(json_file)[0] + ".txt"

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    img_w = data.get("imageWidth")
    img_h = data.get("imageHeight")

    yolo_lines = []
    for shape in data.get("shapes", []):
        label = shape.get("label").strip()  # ตัด space หัวท้าย

        # หา index ของ class
        class_id = -1
        if label in CLASSES:
            class_id = 0  # ให้เป็น class 0 (empty_plot)

        if class_id == -1:
            print(f"⚠️ พบ label ชื่อ '{label}' แต่ไม่อยู่ในรายการ CLASSES")
            continue

        points = shape.get("points")
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)

        x_center = ((xmin + xmax) / 2.0) / img_w
        y_center = ((ymin + ymax) / 2.0) / img_h
        w = (xmax - xmin) / img_w
        h = (ymax - ymin) / img_h

        yolo_lines.append(
            f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}"
        )
        total_boxes += 1

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(yolo_lines))
    converted_count += 1

print(
    f"✅ แปลงสำเร็จ {converted_count} ไฟล์ (รวมทั้งหมด {total_boxes} Bounding Boxes)"
)

if total_boxes == 0:
    print(
        "\n❌ ไม่พบ Bounding Box เลย! กรุณาเช็คว่าชื่อ Label ใน AnyLabeling ตรงกับตัวแปร CLASSES หรือไม่"
    )
    exit()

# --------------------------------------------------
# 3. สร้างไฟล์ data.yaml
# --------------------------------------------------
path_str = working_dir.replace("\\", "/")
yaml_content = f"""path: {path_str}
train: .
val: .

names:
  0: empty_plot
"""

with open("data.yaml", "w", encoding="utf-8") as f:
    f.write(yaml_content)

# --------------------------------------------------
# 4. เริ่มเทรนโมเดล YOLOv8
# --------------------------------------------------
if __name__ == "__main__":
    print("\n🚀 กำลังเริ่มเทรนโมเดล...")
    model = YOLO("yolov8n.pt")

    results = model.train(
        data="data.yaml",
        epochs=50,
        imgsz=640,
    )

    print(
        "\n🎉 เทรนเสร็จสมบูรณ์! ไฟล์ best.pt อยู่ที่: runs/detect/train/weights/best.pt"
    )