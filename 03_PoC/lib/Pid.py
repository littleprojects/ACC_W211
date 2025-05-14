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

        # last data
        self.old_speed = 0
        self.old_integral = 0
        self.old_output = 0

        self.acceleration = 0

    def set_target_speed(self, set_speed):
        self.set_speed = set_speed

    def set_integral(self, integral):
        # set current moment as integral as init value
        self.integral = integral / self.I

    def init_pid(self, set_speed, current_moment, m_min, m_max):
        self.set_speed = set_speed
        # avoid division by 0
        if self.I > 0:
            self.integral = current_moment / self.I
        else:
            self.integral = 0
        self.m_min = m_min
        self.m_max = m_max

        self.dt_ts = utils.ts_ms()

    def pid_calc(self,
                 current_speed,
                 set_speed,
                 overwrite,
                 m_fv,
                 m_min,
                 m_max
                 ):
        now_ts = utils.ts_ms()
        # delta time in second 0.1 = 10Hz
        dt_s = (now_ts - self.dt_ts) / 1000

        self.dt_ts = now_ts

        # set current settings
        self.set_speed = set_speed
        self.m_max = m_max
        self.m_min = m_min

        # calc acceleration
        delta_speed = current_speed - self.old_speed
        delta_speed_ms = delta_speed/3.6                # kph to m/s

        if dt_s > 0:
            self.acceleration = delta_speed_ms/dt_s

        # remember old data
        integral = self.integral
        old_integral = self.integral

        # P - ERROR
        error = self.set_speed - current_speed

        # I - INTEGRAL
        integral += error * dt_s

        # D - DERIVATIVE
        derivative = error - self.old_error

        # OVERWRITE
        # freeze integral if overwrite is active (clamping)
        if overwrite:
            if m_fv > self.m_min:
                integral = m_fv
            else:
                # freez integral
                integral = old_integral

            # integrate driver moment request for better adaptation
            # integral = m_fv
            # M_ART follows driver moment in overwrite mode
            # integral = driver moment

        # PID CALC
        output = self.P * error + self.I * integral + self.D * derivative

        # Output MIN MAX limit
        # M_MAX limitation
        if self.m_max > 0:
            output = min(self.m_max, output)

        # todo M_MIN limitation
        # output = max(self.m_min, output)

        # ANTI WIND UP method integral limitations
        if self.config.acc_acceleration_limit:
            # is accelerating too fast clamp integral
            if self.acceleration > self.config.acc_max_acceleration:
                #print('Limit acceleration')
                # clamp integral
                integral = old_integral
                # freeze output
                output = self.old_output

            if (self.acceleration * -1) > self.config.acc_max_deceleration:
                #print('Limit deceleration')
                # clamp integral
                integral = old_integral
                # clamp output
                output = self.old_output

        # Rate Limit by Nm - Anti wind up function - limit output
        if self.config.acc_rate_limit:
            # delta output per second
            delta_output = (output - self.old_output) / dt_s
            # to high acceleration delta
            if delta_output > self.config.acc_max_acc_rate:
                #print('Limit Rate up')
                # limit output
                output = self.old_output + self.config.acc_max_acc_rate * dt_s

            # to high deceleration delta
            if delta_output * -1 > self.config.acc_max_dec_rate:
                #print('Limit Rate down')
                # limit output
                output = self.old_output - self.config.acc_max_dec_rate * dt_s

        # todo
        # derivative filter

        # MOMENT LIMITER acceleration
        if output > self.config.max_acc_moment:
            # limit output
            output = self.config.max_acc_moment
            # adapt integral
            self.integral = self.config.max_acc_moment - error

        # MOMENT LIMITER deceleration
        if -output > self.config.max_dec_moment:
            # limit output
            output = -self.config.max_dec_moment
            # adapt integral
            self.integral = -self.config.max_dec_moment + error

        # remember values
        self.old_error = error
        self.old_speed = current_speed
        self.old_output = output
        self.integral = round(integral, 2)  # reduce digits

        # reduce digits
        output = round(output, 2)

        return output


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