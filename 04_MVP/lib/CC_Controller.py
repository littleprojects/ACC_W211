"""
CC (CriuseControl) Controller

Simpler speed controller get the target speed

"""

from lib.Logger import Log

class CC_Controller:

    def __init__(self, config):

        self.config = config

        # log
        self.log = Log('CC', config=config).get_logger()

        self.log.info("Init CC")

        # speeds
        self.target_speed = 0
        self.speed = 0

        # moments
        self.m_old = 0

        # limits
        self.m_min = 0
        self.m_max = 0

        # limitation active
        self.limitation = 0
        # 1 - is over m_max (vehicle limit)
        # 2 - is under m_min (vehicle limit)
        # 3 - is over config max_acc_moment
        # 4 - is under config max_dec_moment

    def set_target_speed(self, target_speed):

        # clean input signal
        target_speed = round(target_speed)

        # limit target speed
        if target_speed < self.config.acc_min_speed:
            target_speed = self.config.acc_min_speed
            self.log.info(f"Target Speed {target_speed} under limit {self.config.acc_min_speed}. Set to {self.config.acc_min_speed}")

        if target_speed > self.config.acc_max_speed:
            target_speed = self.config.acc_max_speed
            self.log.info(f"Target Speed {target_speed} over limit {self.config.acc_max_speed}. Set to {self.config.acc_max_speed}")

        self.log.debug(f"Set Target Speed to: {target_speed}")
        self.target_speed = target_speed

    def start(self, target_speed, current_speed, current_moment, m_min, m_max):

        self.set_target_speed(target_speed)

        self.speed = current_speed

        self.m_old = current_moment

        self.m_min = m_min
        self.m_max = m_max

        self.limitation = 0

    def reset(self):
        self.target_speed = 0
        self.speed = 0

        self.m_old = 0

        self.m_min = 0
        self.m_max = 0

        self.limitation = 0

    def calc(self, current_speed, m_fev, m_min, m_max):

        m_out = 0

        acceleration = True

        # clear limitation
        self.limitation = 0

        # clean input signal
        current_speed = round(current_speed, 1)

        speed_delta = self.target_speed - current_speed

        m_out = speed_delta

        # TODO: smooth rampup
        
        if speed_delta > 0:
            acceleration = True

            # add car resitend
            m_out += m_fev

        else:
            acceleration = False

            # no braking at low delta
            if m_out > -20:
                m_out = 0
            
        
        # m_max vehicle limit
        if m_max > 0 and m_out > m_max:
            m_out = m_max
            self.limitation = 1

        # m_min vehicle limit
        # can be 0 and also negativ for breaking
        # self.limitation = 2

        # config limits
        if m_out > self.config.max_acc_moment:
            m_out = self.config.max_acc_moment
            self.limitation = 3

        if m_out < -self.config.max_dec_moment:
            m_out = self.config.max_dec_moment
            self.limitation = 4
        
        self.m_old = m_out

        return m_out

