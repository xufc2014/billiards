import time
from datetime import datetime
from pathlib import Path

import cv2
import mss
import numpy as np
import pygetwindow as gw
import keyboard

# ===================== 配置 =====================
WINDOW_TITLE = "腾讯桌球"                         # 游戏窗口标题关键字
SAVE_FOLDER = Path(r"I:\billiards\img")
IMG_FORMAT = "png"
FILE_PREFIX = "billiard"

# 主热键
SHOT_KEYS = ("space", "f8")   # 空格不行就按 F8
EXIT_KEYS = ("q", "f9")       # Q 不行就按 F9

POLL_INTERVAL = 0.03          # 轮询间隔，越小越灵敏，越大越省CPU
DEBOUNCE_DELAY = 0.20         # 防连触
# =================================================

SAVE_FOLDER.mkdir(parents=True, exist_ok=True)


def is_any_pressed(keys):
    """判断多个按键里是否有任意一个被按下"""
    try:
        return any(keyboard.is_pressed(k) for k in keys)
    except Exception:
        return False


def get_window_rect(title):
    """获取游戏窗口坐标"""
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        print(f"❌ 找不到窗口：{title}")
        return None

    win = windows[0]

    try:
        if win.isMinimized:
            win.restore()
            time.sleep(0.2)
    except Exception as e:
        print(f"❌ 窗口恢复失败：{e}")
        return None

    left = win.left
    top = win.top
    width = win.width
    height = win.height

    if width < 100 or height < 100:
        print("❌ 窗口尺寸异常，截图已跳过")
        return None

    return {
        "left": left,
        "top": top,
        "width": width,
        "height": height
    }


def build_filename(counter):
    """生成带时间戳的文件名"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 毫秒
    return f"{FILE_PREFIX}_{timestamp}_{counter:03d}.{IMG_FORMAT.lower()}"


def save_screenshot(counter):
    """截图并保存"""
    rect = get_window_rect(WINDOW_TITLE)
    if not rect:
        return counter

    try:
        with mss.mss() as sct:
            img = np.array(sct.grab(rect))
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

        filename = build_filename(counter)
        save_path = SAVE_FOLDER / filename

        ok = cv2.imwrite(str(save_path), img)
        if ok:
            print(f"✅ 截图已保存：{filename}")
            return counter + 1
        else:
            print(f"❌ 保存失败：{filename}")
            return counter

    except Exception as e:
        print(f"❌ 截图失败：{e}")
        return counter


def main():
    print("=== 桌球截图工具 ===")
    print(f"🎯 截图热键：{' / '.join(SHOT_KEYS)}")
    print(f"🚪 退出热键：{' / '.join(EXIT_KEYS)}")
    print(f"💾 保存目录：{SAVE_FOLDER}")
    print("提示：如果空格在游戏里没反应，请直接试 F8；如果游戏是管理员运行，脚本也尽量用管理员权限启动。\n")

    img_count = 1
    last_shot_state = False
    last_exit_state = False

    while True:
        shot_pressed = is_any_pressed(SHOT_KEYS)
        exit_pressed = is_any_pressed(EXIT_KEYS)

        # 截图：只在“刚按下”的瞬间触发一次
        if shot_pressed and not last_shot_state:
            print("⌨️ 检测到截图按键")
            img_count = save_screenshot(img_count)
            time.sleep(DEBOUNCE_DELAY)

        # 退出：只在“刚按下”的瞬间触发一次     
        if exit_pressed and not last_exit_state:       
            print("\n👋 退出程序")
            break

        last_shot_state = shot_pressed
        last_exit_state = exit_pressed

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

