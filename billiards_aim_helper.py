import tkinter as tk
import pygetwindow as gw
import keyboard
import win32gui
import win32con

# ===================== 配置 =====================
WINDOW_TITLE = "腾讯桌球"
POCKETS = [
    (142, 184),
    (530, 186),
    (912, 190),
    (912, 561),
    (530, 570),
    (142, 561)
]
CIRCLE_SIZE = 14
BG_COLOR = "#000000"
# ================================================

circle_x, circle_y = 300, 300
dragging = False
drag_offset_x = 0
drag_offset_y = 0

game = gw.getWindowsWithTitle(WINDOW_TITLE)[0]
gx, gy = game.left, game.top
ww, hh = game.width, game.height
game_hwnd = win32gui.FindWindow(None, WINDOW_TITLE)

root = tk.Tk()
root.geometry(f"{ww}x{hh}+{gx}+{gy}")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.config(bg=BG_COLOR)

# ✅ 这一行是关键！tkinter 原生透明色，黑色背景全部穿透
root.wm_attributes("-transparentcolor", BG_COLOR)

canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0)
canvas.pack(fill=tk.BOTH, expand=True)

# ─────────────────────────────────────────────
# 穿透控制（只控制鼠标事件穿不穿透，不管透明色）
# ─────────────────────────────────────────────
def get_hwnd():
    return root.winfo_id()

def set_click_through():
    hwnd = get_hwnd()
    ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex |= win32con.WS_EX_TRANSPARENT
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)

def unset_click_through():
    hwnd = get_hwnd()
    ex = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    ex &= ~win32con.WS_EX_TRANSPARENT
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex)

# ─────────────────────────────────────────────
# 拖拽（只绑定 canvas，避免重复触发）
# ─────────────────────────────────────────────
def on_press(e):
    global dragging, drag_offset_x, drag_offset_y
    dx = e.x - circle_x
    dy = e.y - circle_y
    if dx * dx + dy * dy <= CIRCLE_SIZE * CIRCLE_SIZE:
        drag_offset_x = dx
        drag_offset_y = dy
        dragging = True
        unset_click_through()

def on_drag(e):
    global circle_x, circle_y
    if dragging:
        circle_x = e.x - drag_offset_x
        circle_y = e.y - drag_offset_y
        circle_x = max(CIRCLE_SIZE, min(ww - CIRCLE_SIZE, circle_x))
        circle_y = max(CIRCLE_SIZE, min(hh - CIRCLE_SIZE, circle_y))

def on_release(e):
    global dragging
    if dragging:
        dragging = False
        set_click_through()
        if game_hwnd:
            win32gui.SetForegroundWindow(game_hwnd)

canvas.bind("<ButtonPress-1>",   on_press)
canvas.bind("<B1-Motion>",       on_drag)
canvas.bind("<ButtonRelease-1>", on_release)

# ─────────────────────────────────────────────
# 绘制
# ─────────────────────────────────────────────
def draw():
    canvas.delete("all")
    for px, py in POCKETS:
        canvas.create_line(
            circle_x, circle_y, px, py,
            fill="#00FF00", width=1
        )
    canvas.create_oval(
        circle_x - CIRCLE_SIZE, circle_y - CIRCLE_SIZE,
        circle_x + CIRCLE_SIZE, circle_y + CIRCLE_SIZE,
        outline="#FFFF00", width=2
    )
    canvas.create_oval(
        circle_x - 2, circle_y - 2,
        circle_x + 2, circle_y + 2,
        fill="#FFFF00", outline=""
    )
    root.after(16, draw)

# ─────────────────────────────────────────────
# Q 退出
# ─────────────────────────────────────────────
def check_quit():
    if keyboard.is_pressed("q"):
        root.destroy()
        return
    root.after(10, check_quit)

# ─────────────────────────────────────────────
# 启动（等窗口渲染完再设穿透）
# ─────────────────────────────────────────────
root.after(200, set_click_through)
draw()
check_quit()

print("✅ 启动成功！拖动黄圈 | 圆圈外正常玩游戏 | Q退出")
root.mainloop()

