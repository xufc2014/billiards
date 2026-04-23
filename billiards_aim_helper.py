import cv2
import numpy as np
import mss
import pygetwindow as gw

# -------------------------- 配置区 --------------------------
WINDOW_TITLE = "腾讯桌球"
# 你修正后的精准洞口坐标
POCKETS = [
    (142, 184),
    (530, 186),
    (912, 190),
    (912, 561),
    (530, 570),
    (142, 561)
]
CIRCLE_RADIUS = 15  # 圆圈大小
# -----------------------------------------------------------


# 全局变量
circle_pos = [300, 300]
dragging = False

# 鼠标拖动
def mouse_callback(event, x, y, flags, param):
    global circle_pos, dragging
    if event == cv2.EVENT_LBUTTONDOWN:
        dist = np.hypot(x - circle_pos[0], y - circle_pos[1])
        if dist < CIRCLE_RADIUS:
            dragging = True
    elif event == cv2.EVENT_MOUSEMOVE and dragging:
        circle_pos[0] = x
        circle_pos[1] = y
    elif event == cv2.EVENT_LBUTTONUP:
        dragging = False

# 找窗口
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
    except IndexError:
        return None

# 初始化
window_pos = find_window_position(WINDOW_TITLE)
if not window_pos:
    exit()
left, top, width, height = window_pos
monitor = {"top": top, "left": left, "width": width, "height": height}
sct = mss.mss()

cv2.namedWindow("台球辅助线", cv2.WINDOW_AUTOSIZE)
cv2.setMouseCallback("台球辅助线", mouse_callback)

print("✅ 超细线瞄准圈已启动！")

while True:
    img = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # ========== 画 6 条瞄准线 ==========
    for (px, py) in POCKETS:
        cv2.line(frame, (circle_pos[0], circle_pos[1]), (px, py), (0, 255, 0), 1)

    # ========== 超细线圆圈（核心修改） ==========
    cx, cy = circle_pos[0], circle_pos[1]
    
    # 只画一条细到几乎看不见的线，空心圆圈，完全不挡球
    cv2.circle(frame, (cx, cy), CIRCLE_RADIUS, (0, 255, 255), 1)

    # 可选：加个中心点，对准更方便（不想要可以删掉这行）
    cv2.circle(frame, (cx, cy), 1, (0, 255, 255), -1)

    # 显示
    cv2.imshow("台球辅助线", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
sct.close()