import tkinter as tk
import pygetwindow as gw
import win32api
import win32con
import ctypes
from ctypes import wintypes

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
HIT_RADIUS = 24          # 点击命中范围，适当放大，拖动更顺手
BG_COLOR = "#000"

DRAW_INTERVAL = 16
FOLLOW_INTERVAL = 120
# ================================================

# ===================== Win32 常量 =====================
WM_NCHITTEST = 0x0084
HTCLIENT = 1
HTTRANSPARENT = -1
GWL_WNDPROC = -4

user32 = ctypes.windll.user32

if hasattr(user32, "SetWindowLongPtrW"):
    SetWindowLongPtr = user32.SetWindowLongPtrW
    GetWindowLongPtr = user32.GetWindowLongPtrW
else:
    SetWindowLongPtr = user32.SetWindowLongW
    GetWindowLongPtr = user32.GetWindowLongW

CallWindowProc = user32.CallWindowProcW

SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
SetWindowLongPtr.restype = ctypes.c_void_p
GetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int]
GetWindowLongPtr.restype = ctypes.c_void_p
CallWindowProc.argtypes = [ctypes.c_void_p, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
CallWindowProc.restype = ctypes.c_void_p

LRESULT = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

# ===================== 工具函数 =====================
def clamp(v, low, high):
    return max(low, min(high, v))

def get_game_window():
    windows = gw.getWindowsWithTitle(WINDOW_TITLE)
    if not windows:
        return None
    return windows[0]

def get_game_rect():
    game = get_game_window()
    if not game:
        return None

    try:
        if game.isMinimized:
            game.restore()
    except:
        pass

    return game.left, game.top, game.width, game.height

def is_key_down(vk):
    return bool(win32api.GetAsyncKeyState(vk) & 0x8000)

# ===================== 初始化 =====================
rect = get_game_rect()
if not rect:
    print(f"❌ 未找到游戏窗口：{WINDOW_TITLE}")
    raise SystemExit

win_x, win_y, win_w, win_h = rect

circle_x = win_w // 2
circle_y = win_h // 2

move_mode = False
dragging = False
drag_offset_x = 0
drag_offset_y = 0

last_f2 = False
last_q = False

# ===================== 创建窗口 =====================
root = tk.Tk()
root.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")
root.overrideredirect(True)
root.attributes("-topmost", True)
root.config(bg=BG_COLOR)
root.wm_attributes("-transparentcolor", BG_COLOR)

canvas = tk.Canvas(root, bg=BG_COLOR, highlightthickness=0, bd=0)
canvas.pack(fill=tk.BOTH, expand=True)

root.update_idletasks()
hwnd = root.winfo_id()

# ===================== 命中判断 =====================
def is_on_circle(local_x, local_y):
    dx = local_x - circle_x
    dy = local_y - circle_y
    return dx * dx + dy * dy <= HIT_RADIUS * HIT_RADIUS

# ===================== 拖拽逻辑 =====================
def start_drag(event):
    global dragging, drag_offset_x, drag_offset_y

    if not move_mode:
        return

    if is_on_circle(event.x, event.y):
        dragging = True
        drag_offset_x = event.x - circle_x
        drag_offset_y = event.y - circle_y

def on_drag(event):
    global circle_x, circle_y

    if not move_mode or not dragging:
        return

    circle_x = event.x - drag_offset_x
    circle_y = event.y - drag_offset_y

    circle_x = clamp(circle_x, CIRCLE_SIZE, win_w - CIRCLE_SIZE)
    circle_y = clamp(circle_y, CIRCLE_SIZE, win_h - CIRCLE_SIZE)

def stop_drag(event=None):
    global dragging
    dragging = False

# 左键拖
canvas.bind("<ButtonPress-1>", start_drag)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<ButtonRelease-1>", stop_drag)

# 右键拖
canvas.bind("<ButtonPress-3>", start_drag)
canvas.bind("<B3-Motion>", on_drag)
canvas.bind("<ButtonRelease-3>", stop_drag)

# ===================== 模式切换 =====================
def enter_move_mode():
    global move_mode, dragging
    move_mode = True
    dragging = False

    try:
        root.lift()
        root.focus_force()
        root.grab_set()   # 关键：进入调整模式后，整层抓取输入
    except:
        pass

    print("🛠 已进入调整模式：现在点不到游戏层，可丝滑拖动黄圈；再按 F2 返回游戏模式")

def exit_move_mode():
    global move_mode, dragging
    move_mode = False
    dragging = False

    try:
        root.grab_release()
    except:
        pass

    print("🎮 已退出调整模式：现在可以正常操作游戏")

def toggle_move_mode():
    if move_mode:
        exit_move_mode()
    else:
        enter_move_mode()

# ===================== 绘制 =====================
def draw():
    canvas.delete("all")

    for px, py in POCKETS:
        canvas.create_line(circle_x, circle_y, px, py, fill="#00FF00", width=1)

    if dragging:
        outline_color = "#FF6600"   # 拖动中
    elif move_mode:
        outline_color = "#FFD700"   # 调整模式
    else:
        outline_color = "#FFFF00"   # 普通显示

    canvas.create_oval(
        circle_x - CIRCLE_SIZE, circle_y - CIRCLE_SIZE,
        circle_x + CIRCLE_SIZE, circle_y + CIRCLE_SIZE,
        outline=outline_color, width=2
    )

    canvas.create_oval(
        circle_x - 2, circle_y - 2,
        circle_x + 2, circle_y + 2,
        fill=outline_color, outline=""
    )

    status_text = "调整模式(F2): 开" if move_mode else "调整模式(F2): 关"
    status_color = "#00FF00" if move_mode else "#AAAAAA"

    canvas.create_text(
        12, 16,
        text=status_text,
        anchor="w",
        fill=status_color,
        font=("Arial", 11, "bold")
    )

    root.after(DRAW_INTERVAL, draw)

# ===================== 跟随游戏窗口 =====================
def follow_game_window():
    global win_x, win_y, win_w, win_h, circle_x, circle_y

    rect = get_game_rect()
    if rect:
        new_x, new_y, new_w, new_h = rect

        if (new_x, new_y, new_w, new_h) != (win_x, win_y, win_w, win_h):
            win_x, win_y, win_w, win_h = new_x, new_y, new_w, new_h
            root.geometry(f"{win_w}x{win_h}+{win_x}+{win_y}")

            circle_x = clamp(circle_x, CIRCLE_SIZE, win_w - CIRCLE_SIZE)
            circle_y = clamp(circle_y, CIRCLE_SIZE, win_h - CIRCLE_SIZE)

    root.after(FOLLOW_INTERVAL, follow_game_window)

# ===================== 热键检查 =====================
def check_hotkeys():
    global last_f2, last_q

    f2_down = is_key_down(win32con.VK_F2)
    q_down = is_key_down(ord("Q"))

    if f2_down and not last_f2:
        toggle_move_mode()

    if q_down and not last_q:
        close_app()
        return

    last_f2 = f2_down
    last_q = q_down
    root.after(30, check_hotkeys)

# ===================== 命中穿透核心 =====================
old_wndproc = None
new_wndproc = None

def install_hit_test():
    global old_wndproc, new_wndproc

    @WNDPROC
    def wndproc(hWnd, msg, wParam, lParam):
        if msg == WM_NCHITTEST:
            # F2 关闭：整层完全穿透到游戏
            if not move_mode:
                return HTTRANSPARENT

            # F2 开启：整层都接收鼠标，彻底阻断游戏层
            return HTCLIENT

        return CallWindowProc(old_wndproc, hWnd, msg, wParam, lParam)

    new_wndproc = wndproc
    old_wndproc = GetWindowLongPtr(hwnd, GWL_WNDPROC)
    SetWindowLongPtr(hwnd, GWL_WNDPROC, ctypes.cast(new_wndproc, ctypes.c_void_p).value)

def uninstall_hit_test():
    global old_wndproc
    if old_wndproc:
        try:
            SetWindowLongPtr(hwnd, GWL_WNDPROC, old_wndproc)
        except:
            pass
        old_wndproc = None

# ===================== 关闭 =====================
def close_app():
    try:
        root.grab_release()
    except:
        pass

    uninstall_hit_test()
    root.destroy()
    print("✅ 已退出")

root.protocol("WM_DELETE_WINDOW", close_app)

# ===================== 启动 =====================
install_hit_test()
draw()
follow_game_window()
check_hotkeys()

print("✅ 启动成功")
print("🎮 默认状态：整层穿透，可正常玩游戏")
print("🛠 按 F2：进入调整模式，整层拦截鼠标，游戏不会响应拖动")
print("👉 调整模式下：左键或右键按住黄色圈都可以拖动")
print("🎮 再按一次 F2：退出调整模式，恢复游戏可点击")
print("❌ 按 Q 退出")

root.mainloop()

