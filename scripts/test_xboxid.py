import pygame
import time # <--- 就是這裡少了一行！

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    print("找不到手把，請確認手把電源並已連接至樹莓派！")
else:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"成功連接手把: {joystick.get_name()}")
    print("請按下 X、B、Y 鍵，我會顯示 ID...")

    try:
        while True:
            pygame.event.pump() # 處理所有事件
            for i in range(joystick.get_numbuttons()):
                if joystick.get_button(i):
                    print(f"現在按下的按鍵 ID 是: {i}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n測試結束")