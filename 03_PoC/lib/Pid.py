import time
#from lib import utils
import utils
#from . import utils


class PID:

    def __init__(self, config):
        self.config = config

        self.P = config.acc_p
        self.I = config.acc_i
        self.D = config.acc_d

        self.set_speed = 0
        self.m_min = 0
        self.m_max = 0

        self.integral = 0
        self.old_error = 0

        self.dt_ts = 0

    def set_target_speed(self, set_speed):
        self.set_speed = set_speed

    def set_integral(self, integral):
        # set current moment as integral as init value
        self.integral = integral / self.I

    def init_pid(self, set_speed, current_moment, m_min, m_max):
        self.set_speed = set_speed
        self.integral = current_moment
        self.m_min = m_min
        self.m_max = m_max

        self.dt_ts = utils.ts_ms()

    def pid_calc(self, current_speed, overwrite=False):
        now_ts = utils.ts_ms()
        dt_s = (now_ts - self.dt_ts) / 1000

        error = self.set_speed - current_speed

        if not overwrite:
            self.integral += error * dt_s

        derivative = error - self.old_error
        self.old_error = error

        response = self.P * error + self.I * self.integral + self.D * derivative

        # max limitation
        response = min(self.m_max, response)
        # min limitation
        response = max(self.m_min, response)

        return response


if __name__ == "__main__":
    class Config:
        def __init__(self, P, I, D):
            self.acc_p = P
            self.acc_i = I
            self.acc_d = D


    config = Config(P=2.5, I=0.04, D=0.03)
    # PID calibration
    # 1. P: set I and D to and P to a value with a positive effect
    # 2. I: increase I slowly. Too big steps results in swings and instability
    # 3. D: increase D slowly. D helps with against overshoots

    pid = PID(config)

    current_speed = 40

    pid.init_pid(100, 150, 100, 300)

    for i in range(1000):

        control = pid.pid_calc(current_speed)

        current_speed += (control - 150) / 10

        print(f"I {i} \tSpeed: {round(current_speed, 1)}, "
              f"\tIntegral: {round(pid.integral, 1)}, "
              f"\tm: {round(control, 1)}")

        if i == 100:
            pid.set_target_speed(90)

        if i == 200:
            pid.set_target_speed(70)

        if i == 300:
            pid.set_target_speed(150)


        time.sleep(1)