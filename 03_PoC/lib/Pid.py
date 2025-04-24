import time

try:
    from lib import utils
except:
    pass

try:
    import utils
except:
    pass

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

        # delta timestamp
        self.dt_ts = 0

        # last speed
        self.old_speed = 0

        self.acceleration = 0


    def set_target_speed(self, set_speed):
        self.set_speed = set_speed

    def set_integral(self, integral):
        # set current moment as integral as init value
        self.integral = integral / self.I

    def init_pid(self, set_speed, current_moment, m_min, m_max):
        self.set_speed = set_speed
        self.integral = current_moment / self.I
        self.m_min = m_min
        self.m_max = m_max

        self.dt_ts = utils.ts_ms()

    def pid_calc(self, current_speed, overwrite=False):
        now_ts = utils.ts_ms()
        dt_s = (now_ts - self.dt_ts) / 1000

        error = self.set_speed - current_speed

        # calc acceleration
        delta_speed = current_speed - self.old_speed
        delta_speed_ms = delta_speed/3.6                # kph to m/s
        if dt_s > 0:
            self.acceleration = delta_speed_ms/dt_s

        # remember speed
        self.old_speed = current_speed

        old_integral = self.integral

        if not overwrite:
            self.integral += error * dt_s

        # is accelerating too fast
        if self.acceleration > self.config.acc_max_acceleration:
            # freeze integral
            self.integral = old_integral

        if self.acceleration < (self.config.acc_max_deceleration * -1):
            # freeze integral
            self.integral = old_integral

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

            self.acc_max_acceleration = 1
            self.acc_max_deceleration = 1


    config = Config(P=2.5, I=0.04, D=0.03)# soft
    #config = Config(P=4, I=0.1, D=0.03)
    # PID calibration
    # 1. P: set I and D to and P to a value with a positive effect
    # 2. I: increase I slowly. Too big steps results in swings and instability
    # 3. D: increase D slowly. D helps with against overshoots

    pid = PID(config)

    current_speed = 40

    pid.init_pid(100, 100, 100, 300)

    for i in range(1000):

        control = pid.pid_calc(current_speed)

        current_speed += (control - 150) / 10

        print(f"I {i} \tSpeed: {round(current_speed, 1)}, "
              f"\tv {round(pid.acceleration, 2)}"
              f"\tIntegral: {round(pid.integral, 1)}, "
              f"\tm: {round(control, 1)}")

        if i == 60:
            pid.set_target_speed(90)

        if i == 150:
            pid.set_target_speed(70)

        if i == 200:
            pid.set_target_speed(150)


        time.sleep(1)