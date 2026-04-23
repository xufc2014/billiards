import cv2
import numpy as np
import mss
import pygetwindow as gw
from ultralytics import YOLO

# -------------------------- 配置区 --------------------------
MODEL_PATH = r"I:\xclabel\runs\detect\train-2\weights\best.pt"
WINDOW_TITLE = "腾讯桌球"
CONFIDENCE_THRESHOLD = 0.5
LINE_EXTEND_LENGTH = 1000  # 延长线长度
SCALE = 0.5                # 推理缩放

# 新增配置：线过滤参数
MIN_LINE_LENGTH = 15       # 过滤掉比这更短的线（去除噪点）
ANGLE_TOLERANCE = 5        # 角度容差（度），如果两条线角度差小于这个值，视为重复
# -----------------------------------------------------------

model = YOLO(MODEL_PATH)
model.fuse()

def find_window_position(title):
    try:
        windows = gw.getWindowsWithTitle(title)
        if not windows:
            for w in gw.getAllWindows():
                if title in w.title:
                    windows = [w]
                    break
        window = windows[0]
        if window.isMinimized:
            window.restore()
        return window.left, window.top, window.width, window.height
    except Exception:
        return None

window_pos = find_window_position(WINDOW_TITLE)
if window_pos is None:
    print("未找到窗口")
    exit()

left, top, width, height = window_pos
monitor = {"top": top, "left": left, "width": width, "height": height}
sct = mss.mss()

while True:
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # 缩放推理
    small_frame = cv2.resize(frame, (0, 0), fx=SCALE, fy=SCALE)
    results = model(small_frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            # 还原坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            x1, y1, x2, y2 = int(x1/SCALE), int(y1/SCALE), int(x2/SCALE), int(y2/SCALE)

            # 截取ROI
            roi = frame[y1:y2, x1:x2]
            if roi.size == 0: continue

            # 预处理：二值化
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            # 提高阈值到220，只保留极亮的白线，过滤掉暗淡的背景
            _, binary = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)

            # 霍夫变换找线
            lines = cv2.HoughLinesP(binary, 1, np.pi/180, threshold=15,
                                    minLineLength=MIN_LINE_LENGTH, maxLineGap=5)
            if lines is None: continue

            # --- 核心优化：去重与过滤 ---
            valid_lines = []
            center_pt = ((x2-x1)//2, (y2-y1)//2) # 框中心

            for line in lines:
                lx1, ly1, lx2, ly2 = line[0]
                # 计算线段长度
                length = np.hypot(lx2-lx1, ly2-ly1)
                if length < MIN_LINE_LENGTH: continue

                # 计算角度
                angle = np.degrees(np.arctan2(ly2-ly1, lx2-lx1))

                # 判断是否离中心点太近（防止识别到球本身的圆边）
                # 这里简单处理，主要靠后面的去重

                is_duplicate = False
                for exist_line in valid_lines:
                    _, _, _, _, exist_angle = exist_line
                    # 如果角度非常接近，视为重复线
                    if abs(angle - exist_angle) < ANGLE_TOLERANCE:
                        is_duplicate = True
                        # 如果当前线比已存在的线更长，替换它
                        if length > exist_line[4]:
                            valid_lines.remove(exist_line)
                            valid_lines.append((lx1, ly1, lx2, ly2, angle))
                        break

                if not is_duplicate:
                    valid_lines.append((lx1, ly1, lx2, ly2, angle))

            # --- 绘制延长线 ---
            for lx1, ly1, lx2, ly2, _ in valid_lines:
                # 还原到原图坐标
                lx1 += x1; ly1 += y1; lx2 += x1; ly2 += y1

                # 计算哪个端点离框中心更近
                dist1 = np.hypot(lx1 - (x1+x2)//2, ly1 - (y1+y2)//2)
                dist2 = np.hypot(lx2 - (x1+x2)//2, ly2 - (y1+y2)//2)

                # 确定方向：从近端 -> 远端 -> 延长
                if dist1 < dist2:
                    start_x, start_y = lx1, ly1
                    end_x, end_y = lx2, ly2
                else:
                    start_x, start_y = lx2, ly2
                    end_x, end_y = lx1, ly1

                # 向量计算延长点
                dx = end_x - start_x
                dy = end_y - start_y
                norm = np.hypot(dx, dy) + 1e-6 # 防止除以0
                dx /= norm
                dy /= norm

                extend_x = int(end_x + dx * LINE_EXTEND_LENGTH)
                extend_y = int(end_y + dy * LINE_EXTEND_LENGTH)

                # 画线
                cv2.line(frame, (end_x, end_y), (extend_x, extend_y), (0, 0, 255), 2)

    cv2.imshow("Optimized Aim", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
sct.close()