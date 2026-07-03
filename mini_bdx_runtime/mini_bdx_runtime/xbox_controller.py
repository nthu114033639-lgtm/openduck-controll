import pygame
from threading import Thread
from queue import Queue
import time
import numpy as np
from mini_bdx_runtime.buttons import Buttons

#調整搖桿上的控制指令速度
X_RANGE = [-0.1, 0.1]
Y_RANGE = [-0.2, 0.2]
YAW_RANGE = [-1.0, 1.0]

# rads
NECK_PITCH_RANGE = [-0.34, 1.1]
HEAD_PITCH_RANGE = [-0.78, 0.3]
HEAD_YAW_RANGE = [-0.5, 0.5]
HEAD_ROLL_RANGE = [-0.5, 0.5]


class XBoxController:
    def __init__(self, command_freq, only_head_control=False):
        self.command_freq = command_freq
        self.head_control_mode = only_head_control
        self.only_head_control = only_head_control

        self.last_commands = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.last_left_trigger = 0.0
        self.last_right_trigger = 0.0
        pygame.init()
        self.p1 = pygame.joystick.Joystick(0)
        self.p1.init()
        print(f"Loaded joystick with {self.p1.get_numaxes()} axes.")
        self.cmd_queue = Queue(maxsize=1)

        self.A_pressed = False
        self.B_pressed = False
        self.X_pressed = False
        self.Y_pressed = False
        self.LB_pressed = False
        self.RB_pressed = False

        self.buttons = Buttons()

        Thread(target=self.commands_worker, daemon=True).start()

    def commands_worker(self):
        while True:
            self.cmd_queue.put(self.get_commands())
            time.sleep(1 / self.command_freq)

    def get_commands(self):
            last_commands = self.last_commands
            left_trigger = self.last_left_trigger
            right_trigger = self.last_right_trigger
    
            # 【精準讀取：當羅技 F710 的 MODE 燈亮起（類比模式）時的真實 Axis 號碼】
            l_x = -1 * self.p1.get_axis(0)  # 左蘑菇頭 左右 (平移)
            l_y = -1 * self.p1.get_axis(1)  # 左蘑菇頭 上下 (前進/後退)
            r_x = -1 * self.p1.get_axis(3)  # 右蘑菇頭 左右 (羅技 F710 真正的旋轉是 Axis 3)
            r_y = -1 * self.p1.get_axis(4)  # 右蘑菇頭 上下 (Axis 4)
    
            # 讀取左右後側類比扣鍵 (LT / RT 分別是 Axis 2 和 Axis 5)
            left_trigger  = np.around((self.p1.get_axis(2) + 1) / 2, 3)
            right_trigger = np.around((self.p1.get_axis(5) + 1) / 2, 3)
    
            if left_trigger < 0.1:
                left_trigger = 0
            if right_trigger < 0.1:
                right_trigger = 0
    
            # ---- 1. 走路與旋轉核心控制 (永遠開啟，聽從蘑菇頭命令) ----
            lin_vel_y = l_x
            lin_vel_x = l_y
            ang_vel = r_x
    
            if lin_vel_x >= 0:
                lin_vel_x *= np.abs(X_RANGE[1])
            else:
                lin_vel_x *= np.abs(X_RANGE[0])
    
            if lin_vel_y >= 0:
                lin_vel_y *= np.abs(Y_RANGE[1])
            else:
                lin_vel_y *= np.abs(Y_RANGE[0])
    
            if ang_vel >= 0:
                ang_vel *= np.abs(YAW_RANGE[1])
            else:
                ang_vel *= np.abs(YAW_RANGE[0])
    
            last_commands[0] = lin_vel_x
            last_commands[1] = lin_vel_y
            last_commands[2] = ang_vel
    
            # ---- 2. 獨立十字鍵控制：點頭與歪頭表情 (與模式無關，隨時隨地能用) ----
            # 讀取最左邊的實體十字鍵 (按上是 1, 按下是 -1)
            hat_left_right = self.p1.get_hat(0)[0]
            hat_up_down = self.p1.get_hat(0)[1] 
            
            last_commands[3] = 0.0  
            last_commands[4] = 0.0
            last_commands[5] = hat_up_down * -0.4    # 十字鍵上下控制點頭 (Pitch)
            last_commands[6] = hat_left_right * -0.4  # 十字鍵左右控制轉頭 (Yaw)
    
            # 處理 Pygame 按鍵事件 (維持手把按鍵偵測)
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN:
                    if self.p1.get_button(0):  # A button
                        self.A_pressed = True
                    if self.p1.get_button(3):  # B button
                        self.B_pressed = True
                    if self.p1.get_button(2):  # X button
                        self.X_pressed = True
                    if self.p1.get_button(1):  # Y button
                        self.Y_pressed = True
                    if self.p1.get_button(6):  # LB button
                        self.LB_pressed = True
                    if self.p1.get_button(7):  # RB button
                        self.RB_pressed = True
    
                if event.type == pygame.JOYBUTTONUP:
                    self.A_pressed = False
                    self.B_pressed = False
                    self.X_pressed = False
                    self.Y_pressed = False
                    self.LB_pressed = False
                    self.RB_pressed = False
    
            pygame.event.pump()  # 刷新事件
    
            return (
                np.around(last_commands, 3),
                self.A_pressed,
                self.B_pressed,
                self.X_pressed,
                self.Y_pressed,
                self.LB_pressed,
                self.RB_pressed,
                left_trigger,
                right_trigger,
                (hat_left_right, hat_up_down),
            )

    def get_last_command(self):
        A_pressed = False
        B_pressed = False
        X_pressed = False
        Y_pressed = False
        LB_pressed = False
        RB_pressed = False
        up_down = 0
        left_right = 0
        try:
            (
                self.last_commands,
                A_pressed,
                B_pressed,
                X_pressed,
                Y_pressed,
                LB_pressed,
                RB_pressed,
                self.last_left_trigger,
                self.last_right_trigger,
                (left_right, up_down),
            ) = self.cmd_queue.get(
                False
            )  # non blocking
        except Exception:
            pass

        self.buttons.update(
            A_pressed,
            B_pressed,
            X_pressed,
            Y_pressed,
            LB_pressed,
            RB_pressed,
            up_down == 1,
            up_down == -1,
        )

        return (
            self.last_commands,
            self.buttons,
            self.last_left_trigger,
            self.last_right_trigger,
        )

if __name__ == "__main__":
    controller = XBoxController(20)

    while True:
        (
            commands,
            _,
            _,
            _,
        ) = controller.get_last_command()
        print(commands)
        time.sleep(0.05)
