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

        self.kp = config.acc_kp
        self.ki = config.acc_ki
        self.kd = config.acc_kd

        self.set_speed = 0
        self.m_min = 0
        self.m_max = 0

        self.old_error = 0
        self.integral = 0
        self.derivative = 0

        # delta timestamp
        self.dt_ts = 0

        # last data
        self.old_speed = 0
        self.old_integral = 0
        self.old_output = 0
        self.old_m_fv = 0

        self.acceleration = 0

        # limitation active
        self.limitation = 0

    def set_target_speed(self, set_speed):
        self.set_speed = set_speed

    def set_integral(self, integral):
        # set current moment as integral as init value
        if self.ki != 0:
            self.integral = integral  # / self.I
        else:
            self.integral = 0

        # dont forget to set also the old_integral, otherwise the limiting function jump in
        self.old_integral = self.integral

    def init_pid(self, set_speed, current_moment, m_min, m_max):
        self.set_speed = set_speed

        self.old_output = current_moment

        # avoid division by 0
        if self.ki > 0:
            self.integral = current_moment  # / self.I
        else:
            self.integral = 0
        self.m_min = m_min
        self.m_max = m_max

        self.dt_ts = utils.ts_ms()

    def reset(self):
        self.old_error = 0
        self.integral = 0
        self.derivative = 0

        self.set_speed = 0
        self.old_m_fv = 0
        self.old_output = 0
        self.acceleration = 0
        self.limitation = 0

    def pid_calc(self,
                 current_speed,
                 acc_long,
                 set_speed,
                 overwrite,
                 m_fv,
                 m_min,
                 m_max
                 ):

        now_ts = utils.ts_ms()
        # delta time in second 0.1 = 10Hz
        #dt_s = (now_ts - self.dt_ts) / 1000
        # Todo fixed for testing
        dt_s = 0.1

        self.dt_ts = now_ts

        # set current settings
        self.set_speed = set_speed
        self.m_max = m_max
        self.m_min = m_min

        current_speed = round(current_speed, 1)

        self.acceleration = acc_long

        self.limitation = 0

        # calc acceleration
        #delta_speed = current_speed - self.old_speed
        #delta_speed_ms = delta_speed/3.6                # kph to m/s

        #if dt_s > 0:
        #    self.acceleration = delta_speed_ms/dt_s

        # remember old data
        integral = self.integral
        old_integral = self.integral

        # P - ERROR
        error = self.set_speed - current_speed

        # Error Limit
        if self.config.pid_error_limit:
            # max limit
            if error > self.config.pid_error_max:
                error = self.config.pid_error_max
                self.limitation = 7
            # min limit
            if error < self.config.pid_error_min:
                error = self.config.pid_error_min
                self.limitation = 8

        # I - INTEGRAL
        integral += error * dt_s * self.ki

        # D - DERIVATIVE
        # derivative = round(((self.old_error - error) / dt_s), 2)
        derivative = round(((error - self.old_error) / dt_s), 2)

        # Integral limiter to m_max
        if integral > self.m_max:       # (integral * self.I)
            self.set_integral(self.m_max)

        # Integral limit to m_min
        if -integral > self.config.max_dec_moment:
            self.set_integral(-self.config.max_dec_moment)

        # OVERWRITE
        # freeze integral if overwrite is active (clamping)
        if overwrite:
            self.limitation = 10

            # freez integral
            integral = old_integral

            # follow only on rising torque
            if m_fv > self.old_m_fv:
                # integrate driver moment request for better adaptation
                # integral = m_fv
                # integral = driver moment

                self.set_integral(m_fv)
                self.limitation = 11

        # PID CALC
        output = (self.kp * error) + integral + (self.kd * derivative)
        # I-factor is added to integral already ( integral += error * dt_s * self.I)
        # to have an realistic integral value

        # Output MIN MAX limit
        # M_MAX limitation
        if self.m_max > 0:
            output = min(self.m_max, output)
            integral = min(self.m_max, integral)

        # todo M_MIN limitation ??? output can go below m_min for braking
        # output = max(self.m_min, output)

        # ANTI WIND UP method integral limitations
        if self.config.acc_acceleration_limit:
            # is accelerating too fast clamp integral
            if self.acceleration > self.config.acc_max_acceleration:
                self.limitation = 1
                # clamp integral
                integral = old_integral
                # clamp output
                output = self.old_output

            if (self.acceleration * -1) > self.config.acc_max_deceleration:
                self.limitation = 2
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
                self.limitation = 3
                # limit output
                output = self.old_output + self.config.acc_max_acc_rate * dt_s

            # to high deceleration delta
            if -delta_output > self.config.acc_max_dec_rate:
                self.limitation = 4
                # limit output
                output = self.old_output - self.config.acc_max_dec_rate * dt_s

        # todo
        # derivative filter

        # MOMENT LIMITER acceleration
        if output > self.config.max_acc_moment:
            self.limitation = 5
            # limit output
            output = self.config.max_acc_moment
            # adapt integral
            self.integral = self.config.max_acc_moment  # - error

        # MOMENT LIMITER deceleration
        if -output > self.config.max_dec_moment:
            self.limitation = 6
            # limit output
            output = -self.config.max_dec_moment
            # adapt integral
            self.integral = -(self.config.max_dec_moment)  # - error)

        # remember values
        self.old_speed = current_speed
        self.old_output = output
        self.old_m_fv = m_fv
        self.old_error = error
        self.integral = round(integral, 2)  # reduce digits
        self.derivative = derivative

        # reduce digits
        output = round(output, 2)

        return output


    # try a new acc controller with loss torque and only acceleration
    def pid_calc2(self,
                 current_speed,
                 acc_long,
                 set_speed,
                 overwrite,
                 m_fv,
                 m_min,
                 m_max,
                 m_verl
                 ):

        # PID parameter TODO: read from config
        # todo add a speed factor to kP to have a higher kP at higher Speeds
        self.kp = 3
        self.ki = 0.15
        self.kd = 0

        # set current settings
        self.set_speed = set_speed
        self.m_max = m_max
        self.m_min = m_min

        current_speed = round(current_speed, 1)

        # self.acceleration = acc_long

        # error code
        self.limitation = 0

        # remember old data
        integral = self.integral
        old_integral = self.integral

        # P - SPEED ERROR
        error = self.set_speed - current_speed

        # Anti wind up
        # Error Limiter TODO: read parameters from config
        # 20kph difference * kp = 40Nm
        if self.config.pid_error_limit:
            # max limit
            if error > 20:
                error = 20
                self.limitation = 7
            # min limit
            if error < -20:
                error = -20
                self.limitation = 8

        break_factor = 1
        if error < -5:
            break_factor = 2

        # I - INTEGRAL
        integral += error * self.ki * break_factor

        # D - DERIVATIVE
        # derivative = round(((self.old_error - error) / dt_s), 2)
        derivative = round((error - self.old_error), 2)

        # Integral limiter to m_max
        if integral > self.m_max:       # (integral * self.I)
            self.set_integral(self.m_max)

        # Integral limit to m_min
        if -integral > self.config.max_dec_moment:
            self.set_integral(-self.config.max_dec_moment)

        # PID CALC + loss torque + 160Nm basic
        output = (self.kp * error) + integral + (self.kd * derivative) + m_verl + 160
        # I-factor is added to integral already ( integral += error * dt_s * self.I)
        # to have an realistic integral value

        # TODO FMRAD Factor Moment Wheel signal['FMRAD'] ???

        # OVERWRITE
        # freeze integral if overwrite is active (clamping)
        if overwrite:
            self.limitation = 10

            output = 0

            # freez integral
            integral = old_integral
            """
            # follow only on rising torque
            if m_fv > self.old_m_fv:
                # integrate driver moment request for better adaptation
                # integral = m_fv
                # integral = driver moment

                self.set_integral(m_fv)
                self.limitation = 11
            """

        # speed is too high
        #if error < -5:
            # reset integral
        #    integral = 0

            # set torque to min
        #    output = 160

        # Output MIN MAX limit
        # M_MAX limitation
        if self.m_max > 0:
            output = min(self.m_max, output)
            integral = min(self.m_max, integral)

        # ANTI WIND UP INTEGRAL
        # max limitation
        integral = min(integral, 60)
        # min limitation
        integral = max(integral, -60)

        # M_MIN limitation -> output >= 0
        output = max(output, 0)

        # remember values
        self.old_speed = current_speed
        self.old_output = output
        self.old_m_fv = m_fv
        self.old_error = error
        self.integral = round(integral, 1)  # reduce digits
        self.derivative = derivative

        # reduce digits
        output = round(output, 2)

        return output

"""
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

"""