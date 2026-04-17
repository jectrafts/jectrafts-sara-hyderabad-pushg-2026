import pyautogui
import time
while True:
    position = pyautogui.position()
    x = position.x
    y = position.y
    print(f"Mouse position: ({x}, {y})")
    time.sleep(0.2)