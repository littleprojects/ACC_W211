"""
This Class display the Data for Debugging reason.
It works with matplotlib

"""
import time

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.animation as animation
import numpy as np

# load utils from lib folder
try:
    from lib import utils
except:
    pass

# log util direct for testing
try:
    import utils
except:
    pass


class Viewer:
    def __init__(self):

        self.start_ts = utils.ts_ms()

        self.signal_data = {
            'ART_REG': 0,
            'LIM_REG': 0,
            'ART_UEBERSP': 0,
            'ART_ERROR': 0,

            'GMAX_ART': 0,
            'GIC': 0,
            'GMIN_ART': 0,

            'M_FV': 0,  # Fahrervorgabe
            'M_ART': 0,
            'MBRE_ART': 0,

            'V_ANZ': 0,
            'V_ART': 0,
            'V_ZIEL': 0,
            # '': 0,

            # PID ERROR
            # PID Integral
        }

        # dict of time data
        self.time_data = {
            'x': [],
            'ART_REG': [],
            'LIM_REG': [],
            'ART_UEBERSP': [],
            'ART_ERROR': [],

            'GMAX_ART': [],
            'GIC': [],
            'GMIN_ART': [],

            'M_FV': [],  # Fahrervorgabe
            'M_ART': [],
            'MBRE_ART': [],

            'V_ANZ': [],
            'V_ART': [],
            'V_ZIEL': [],
        }

        # Create a figure
        self.fig = plt.figure(figsize=(12, 7))

        plt.title('ACC W211')
        plt.gca().axis('off') # no frame

        # Create a GridSpec with 3 rows and 3 columns
        gs = GridSpec(3, 3)

        # Add subplots to the grid
        self.ax1 = self.fig.add_subplot(gs[0, :-1])
        self.ax2 = self.fig.add_subplot(gs[1, :-1])
        self.ax3 = self.fig.add_subplot(gs[2, :-1])
        axR = self.fig.add_subplot(gs[:, 2])

        # clean axR
        axR.set_xticks([])
        axR.set_yticks([])
        # axR.set_axis_off() # delete all axis

        #ax1
        self.plot_art_reg, = self.ax1.plot([], [], label='ART_REG', color='red', linestyle='-')
        self.plot_lim_reg, = self.ax1.plot([], [], label='LIM_REG', color='blue', linestyle='--')
        self.plot_art_ueb, = self.ax1.plot([], [], label='ART_UEBERSP')
        self.ax1.set_ylim(-0.2, 1.2)
        self.ax1.legend(loc="upper left")


        # ax2
        self.ax2_m_fv, = self.ax2.plot([], [], label='M_FV')
        self.ax2_m_art, = self.ax2.plot([], [], label='M_ART')
        self.ax2_m_bre, = self.ax2.plot([], [], label='MBRE_ART')
        self.ax2.set_ylim(0, 400)
        self.ax2.legend(loc="upper left")

        # ax3
        self.ax3_1, = self.ax3.plot([], [], label='V_ANZ')
        self.ax3_2, = self.ax3.plot([], [], label='V_ART')
        self.ax3_3, = self.ax3.plot([], [], label='V_ZIEL')
        self.ax3.set_ylim(0, 160)
        self.ax3.legend(loc="upper left")


        # axR.clear()
        self.text_l = axR.text(0.05, 0.5, "ART_REG:\nLIM_REG:", fontsize=12, color='blue')
        self.text_r = axR.text(0.5, 0.5, "0", fontsize=12, color='blue')
        # text.update(1,2,"TEst")

        self.ani = animation.FuncAnimation(self.fig, self.update_ani, interval=10, save_count=1000)

        plt.show(block=False)

    def update_time_data(self):
        #print(self.signal_data)
        #print(self.time_data)

        now = round(utils.ts_ms() - self.start_ts) / 1000

        self.time_data['x'].append(now)

        oversize = False

        if now > 100:
            oversize = True
            self.time_data['x'].pop(0)

        for item in self.time_data:
            if item == 'x':
                continue

            #print(item + ' add: ' + str(self.signal_data[item]))

            self.time_data[item].append(self.signal_data[item])

            if oversize:
                self.time_data[item].pop(0)

        # ax1
        self.plot_art_reg.set_data(self.time_data['x'], self.time_data['ART_REG'])
        self.plot_lim_reg.set_data(self.time_data['x'], self.time_data['LIM_REG'])
        self.plot_art_ueb.set_data(self.time_data['x'], self.time_data['ART_UEBERSP'])

        # ax2
        self.ax2_m_fv.set_data(self.time_data['x'], self.time_data['M_FV'])
        self.ax2_m_art.set_data(self.time_data['x'], self.time_data['M_ART'])
        self.ax2_m_bre.set_data(self.time_data['x'], self.time_data['MBRE_ART'])

        # ax3
        self.ax3_1.set_data(self.time_data['x'], self.time_data['V_ANZ'])
        self.ax3_2.set_data(self.time_data['x'], self.time_data['V_ART'])
        self.ax3_3.set_data(self.time_data['x'], self.time_data['V_ZIEL'])

        #update timeline
        self.ax1.set_xlim(max(0, now - 20), now + 1)
        self.ax2.set_xlim(max(0, now - 20), now + 1)
        self.ax3.set_xlim(max(0, now - 20), now + 1)

        # text
        #print(self.signal_data['ART_REG'])
        #self.text_r.update( "1")
        self.text_r.set_text(f"""{self.signal_data['ART_REG']}
{self.signal_data['LIM_REG']}""")

    def run(self):
        #plt.show(block=False)
        #plt.draw()
        #plt.pause(0.01)
        #self.update_data(self.x)
        #self.update_time_data()
        plt.pause(0.0001)

    def get_data(self, t):
        return np.sin(self.x * t)  # + np.random.normal(0, 0.05)

    def update_ani(self, frame):
        #print('update' + str(frame))
        self.update_time_data()
        pass

    def update_data(self, frame):
        now = round(utils.ts_ms() - self.start_ts) / 1000
        self.x = self.x+1
        self.x_data.append(now)
        self.y_data.append(self.get_data(now))
        self.line0.set_data(self.x_data, self.y_data)
        self.line1.set_data(self.x_data, self.y_data)
        self.ax[0].set_xlim(max(0, now - 20), now + 1)
        self.ax[1].set_xlim(max(0, now - 20), now + 1)

        return self.line0

    def update_plot(self, x):
        pass

    def update_signals(self, msg_signals, art_signals):

        #signals = {}
        # combine and update all signals
        self.signal_data.update(msg_signals)
        self.signal_data.update(art_signals)

        #self.update_time_data()




if __name__ == "__main__":

    dv = Viewer()
    dv.run()

    msg_signals = {
        'SFB': 1,
        'V_ANZ': 30,
        'GIC': 2,
        'M_FV': 223,
        'ART_REG': 1,
        #'': 0,
        #'': 0,
        #'': 0,
        #'': 0,
    }

    art_signals = {
        # ART_250
        'DYN_UNT': 0,  # dynamic downshift suppression
        'BL_UNT': 0,  # breathtaking suppression
        'ART_BRE': 0,  # ART breaks
        'ART_OK': 0,  # ART ok
        'SLV_ART': 0,  # shift lines adaptation
        'CAS_REG': 0,  # City assist is active
        'MDYN_ART': 0,  # dynamic engine moment
        'MPAR_ART': 0,  # parity
        'ART_REG': 0,  # ART is active
        'LIM_REG': 0,  # limiter is activ
        'M_ART': 0,  # [Nm] engine moment
        'BZ250h': 0,  # msg counter 4bit = 0-15
        'MBRE_ART': 0,  # [Nm] break moment
        'GMIN_ART': 0,  # minimum gear
        'GMAX_ART': 0,  # maximum gear
        'AKT_R_ART': 0,  # shift down request from art

        # ART_258
        'ART_ERROR': 0,  # ART error code
        'ART_INFO': 0,  # ART info light
        'ART_WT': 0,  # ART warning sound
        'S_OBJ': 0,  # standing object detected
        'ART_DSPL_EIN': 0,  # ART display on
        'V_ART': 0,  # [kph] ART set speed
        'ABST_R_OBJ': 0,  # [m] distance to relevant object
        'SOLL_ABST': 0,  # [m] distance to relevant object
        'TM_EIN_ART': 0,  # ART cruise control activ
        'ART_DSPL_BL': 0,  # blink speed control
        'ART_SEG_EIN': 0,  # show speed segments on display
        'OBJ_ERK': 0,  # object detected
        'ART_EIN': 0,  # ART on
        'ART_DSPL_LIM': 0,  # show: --- on display
        'ART_VFBR': 0,  # show: ART off
        'ART_DSPL_PGB': 0,  # show: winter tire speed reached
        'V_ZIEL': 0,  # [kph] target speed on segment display
        'ASSIST_FKT_AKT': 0,  # active function - always 0
        'AAS_LED_BL': 0,  # LED blinking
        'OBJ_AGB': 0,  # object offer adaptive cc - always 0
        'ART_ABW_AKT': 0,  # warnings are switched on TODO load from memory
        'ART_REAKT': 0,  # reactivation of ART after error
        'ART_UEBERSP': 0,  # ART passive
        'ART_DSPL_NEU': 0,  # show ART display again for a short time
        'ASSIST_ANZ_V2': 0,  # assist display request - always 0
        'CAS_ERR_ANZ_V2': 0,  # CAS display request - always 0
    }

    for i in range(1000):
        # 10 Hz sleep
        time.sleep(0.1)

        dv.update_signals(msg_signals, art_signals)

        #dv.update_data(i)
        dv.run()

        print(i)

