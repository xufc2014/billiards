import cv2
import numpy as np
import mss
import pygetwindow as gw

# ====================== 配置 ======================
WINDOW_TITLE = "腾讯桌球"
# ===================================================

points = []
display_window = "Pocket Point Picker"

def mouse_click(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"📌 已记录第 {len(points)} 个洞口坐标：({x}, {y})")

# 找窗口
def get_game_window(title):
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        for w in gw.getAllWindows():
            if title in w.title:
                return w.left, w.top, w.width, w.height
    else:
        w = windows[0]
        return w.left, w.top, w.width, w.height
    return None

win_rect = get_game_window(WINDOW_TITLE)
if not win_rect:
    print("❌ 未找到游戏窗口，请确认窗口标题正确")
    exit()

left, top, ww, hh = win_rect
monitor = {"top": top, "left": left, "width": ww, "height": hh}
sct = mss.mss()

# 强制创建窗口并绑定鼠标
cv2.namedWindow(display_window, cv2.WINDOW_AUTOSIZE)
cv2.setMouseCallback(display_window, mouse_click)

print("\n🎱 点击游戏洞口即可记录坐标，按 q 退出\n")

while True:
    frame = np.array(sct.grab(monitor))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # 画出已点的点
    for i, (x, y) in enumerate(points):
        cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)
        cv2.putText(frame, str(i+1), (x+12, y+10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    cv2.imshow(display_window, frame)

    # 按 q 退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n📤 所有记录的坐标：", points)
        break

cv2.destroyAllWindows()