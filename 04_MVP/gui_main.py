"""
AI generated Streamlit app

To have a UX for displaying the data and do some changes

pip install streamlit plotly

run with:
streamlit.exe run gui_main.py

"""

# streamlit_app.py
import time
import requests
import streamlit as st
import pandas as pd
from collections import deque
import plotly.express as px

st.set_page_config(page_title="ACC Live", layout="wide")

#st.title("Live CAN-Signale (10 Hz Polling)")
#st.caption("Drücke Start, um die Abfrage zu beginnen. Stopp beendet die Schleife.")

# --- Konfiguration: lokale API-Adresse ---
can_api_url = "http://localhost:5001/data/can_c"
art_api_url = "http://localhost:5001/data/art"
radar_api_url = "http://localhost:5001/data/radar"

# API response
# can
_ = """
{
    "msgs":{"0x200":1787045085435,"0x210":1787045085383,"0x212":1787045085391,"0x218":1787045085383,"0x236":1787045085414,"0x238":1787045085341,"0x240":1787045085362,"0x300":1787045085340,"0x308":1787045085404,"0x312":1787045085425,"0x328":1787045085340,"0x408":1787045085404,"0x412":1787045085391,"0x418":1787045085383,"0x608":1787045085119},
    "signals":{
        "ABST_S":0,
        "ABS_KL":0,
        "ANL_LFT":0,
        "ART_ABSTAND":100,
        "ART_ABW_BET":0,
        "ART_E":1,
        "ART_VH":1,        
        "AY_S":13.0,
        "BLS":0,
        "BN_NTLF":0,
        "BRE_AKT_E":0,
        "BRE_KL":0,
        "BTRBSART_UMSCH":0,
        "BZ236h":8,
        "BZ238h":3,
        "CRASH":0,
        "CRASH_CNF":0,
        "CRC_236h":18,
        "DANZ":81,
        "DRTGANZ":1,
        "DRTGTM":1,
        "DVL":81,
        "ESP_BET":0,"ESP_INFO_BL":0,"ESP_INFO_DL":0,"ESP_KL":0,
        "FMRAD":278,"FPC":67,"FSC":68,
        "GET_OK":0,
        "GIC":1,
        "GIER_ROH":-0.0026999999999999247,
        "GS_NOTL":0,
        "HAS_KL":0,
        "IST_ABST":0,
        "KLA_VH":1,"KL_58D":0,"KL_61E":1,"KM16":35843,
        "LRW":4.0,"LRWS_ID":0,"LRWS_ST":0,"LW":4.0,"LW_CF":0,"LW_INI":0,"LW_OV":0,"LW_PA":1,"LW_VZ":0,
        "MAZ":254,"MAZ_NEU":1440,
        "M_ART_E":1,
        "M_FEV":9.5,
        "M_FV":159.60000000000002,
        "M_MAX":260.1,
        "M_MAX_ATL":212.60000000000002,
        "M_MIN":211.4,
        "M_STA":211.4,
        "M_VERL":22,
        "NMOT":795,
        "NOTL":0,
        "OEL_FS":141,
        "OEL_KL":0,
        "OEL_QUAL":60,
        "OPT_WARN_AUS":0,
        "PRW_ANF":1,
        "PTS_TON_AUS":0,"PWG_ERR":0,      

        "SGT_VH":1,"ST3_BET":0,"TACHO_SYM":0,"TANK_FS":49,"TEMP_KL":0,
        "TFSM":0,"TF_AUF":0,"TM_DL":81,"TM_REG":0,"T_AUSSEN":13.5,"T_GET":12.0,
        "T_LUFT":5.0,"T_MOT":8.5,"T_OEL":5.5,"UEHITZ":0,"UEHITZ_GET":0,"VB":8.15,"VGL_KL_DEF":0,
        "VMAX_AKT":0,"V_DSPL_AKT":0,"V_DSPL_AUS":0,"V_MAX_FIX":250,"V_MPH":0,
        "WHST":4,"WH_PA":0,"WH_UP":0,"WRC":0,"WRC3":0,"ZH_FREIG":1,"vLRW":0.0

        # vehicle
        "V_ANZ":6.1,

        # driver
        "SFB":0, # brake
        "Pedalwert":0.0,

        #lever
        "SBCSH_AKT":1,
        "AUS":0, # off
        "WA":0,
        "S_MINUS_B":0,
        "S_PLUS_B":0,   
        "V_MAX_EIN":0,
        "AKU_WARN_AUS":0, 
        "BLI_LI":0,
        "BLI_RE":0,   
    }
}
"""
# art
_ = """
{
    "AAS_LED_BL":0,
    "ABST_R_OBJ":0,
    "AKT_R_ART":0,
    "ART_ABW_AKT":0,
    "ART_BRE":0,
    "ART_DSPL_BL":0,
    "ART_DSPL_EIN":0,
    "ART_DSPL_LIM":0,
    "ART_DSPL_NEU":0,
    "ART_DSPL_PGB":0,
    "ART_EIN":1,
    "ART_ERROR":0,
    "ART_INFO":0,
    "ART_OK":1,
    "ART_REAKT":0,
    "ART_REG":0,
    "ART_SEG_EIN":0,
    "ART_UEBERSP":0,
    "ART_VFBR":1,
    "ART_WT":0,
    "ASSIST_ANZ_V2":0,
    "ASSIST_FKT_AKT":0,
    "BL_UNT":0,
    "BZ250h":15,
    "CAS_ERR_ANZ_V2":0,
    "CAS_REG":0,
    "DYN_UNT":0,
    "GMAX_ART":0,
    "GMIN_ART":0,
    "LIM_REG":0,
    "MBRE_ART":0,
    "MDYN_ART":0,
    "MPAR_ART":0,
    "M_ART":0,
    "OBJ_AGB":0,
    "OBJ_ERK":0,
    "SLV_ART":0,
    "SOLL_ABST":16,
    "S_OBJ":0,
    "TM_EIN_ART":1,
    "V_ART":0,
    "V_ZIEL":0}
"""
# radar

signals_to_display = [
    "AUS", # off
    "WA",
    "S_MINUS_B",
    "S_PLUS_B",   
    "V_MAX_EIN",
    "ART_ABSTAND",
    "AKU_WARN_AUS",
    "ART_REG",
    "ART_UEBERSP",
    "SFB", # brake
]

# Signale, die geplottet werden sollen
signals_to_plot = [
    #"VB", 
    "V_ANZ",
    "V_ART",
    "V_ZIEL"
]

signals_to_list = [
    "V_ANZ",
    "V_ART",
    "V_ZIEL",
    "",
    "GIC",
    "GMAX_ART",
    "GMIN_ART",
    " ",
    "M_FV",
    "M_ART",
    "MBRE_ART",
]

signals_to_display2 = [
    "ART_OK",
]

st.markdown(''' 
    <style>
    [data-testid="stAlertContainer"] {
    #outline: 2px solid red;
    //border-radius: 2px;
    padding: 8px;
} 
    </style>
    ''', unsafe_allow_html=True)

# main signal list
signals = {}

# Wahl der Fenstergröße (Anzahl Messpunkte, z.B. 10 Sekunden bei 10 Hz = 100)
window_size = st.sidebar.number_input("Fenstergröße (Messpunkte)", min_value=10, max_value=5000, value=200, step=10)

# top bar
with st.container(horizontal=True):
    start_btn = st.button('GO', shortcut="g")
    stop_btn= st.button('Stop', shortcut="s")
    status_placeholder = st.empty()

# Speicher für Zeitstempel und Signale (fixed-size rolling buffer)
buffers = {s: deque(maxlen=window_size) for s in signals_to_plot}
buffers["timestamp"] = deque(maxlen=window_size)

# Display fields for latest values
#st.subheader("Aktuelle Werte")
#value_cols = st.columns(len(signals_to_list))
#value_placeholders = {s: value_cols[i].empty() for i, s in enumerate(signals_to_list)}

# display signal values
info_list = {}
with st.container(horizontal=True, border=True):
    for s in signals_to_display:
        info_list[s] = st.info(f"{s}: ---")

left_col, right_col = st.columns([3, 1], vertical_alignment="center")

# plot
with left_col:
    plot_placeholder = st.empty()

# table
with right_col:
    right_col_placeholder = st.empty()

table_data = {}
for s in signals_to_list:
    table_data[s] = None #signals.get(s, '---')

with right_col_placeholder: 
    st.table(
    table_data,
    border="horizontal",
    width="content",
    )

# display signal values
info_list2 = {}
with st.container(horizontal=True, border=True):
    for s in signals_to_display2:
        info_list2[s] = st.info(f"{s}: ---")

#info_list = {}
#with st.container(horizontal=True, border=True):
#    for s in signals_to_display:
#        info_list[s] = st.info(f"{s}: ---")
    

#def plot_signal_values(placeholder, signals, signals_to_plot):
#    """Plot signals to a line chart in the given placeholder"""
#    # TODO: buffering is data is needed
#    pass

json_view = st.sidebar.empty()

def fetch_once(url):
    try:
        resp = requests.get(url, timeout=1.0)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

running = False
if start_btn:
    running = True
    st.session_state["running"] = True
if stop_btn:
    st.session_state["running"] = False

if "running" in st.session_state:
    running = st.session_state["running"]

if running:
    status_placeholder.success("Running...")
    try:
        while st.session_state.get("running", False):
            t = pd.Timestamp.now()

            can_data = fetch_once(can_api_url)
            art_data = fetch_once(art_api_url)
            #radar_data = fetch_once(radar_api_url)

            if "error" in can_data or "error" in art_data:
                status_placeholder.warning(f"Fehler bei API-Abfrage: {can_data['error']}")
                time.sleep(0.5)
                continue

            # update signal list
            signals.update(can_data.get("signals", {}))
            signals.update(art_data)

            #signal_status.empty()
            #display_signal_values(signals, signals_to_display)
            for s in signals_to_display:
                    sig = signals.get(s, '---')
                    if sig > 0:
                        info_list[s].success(f"{s}: {sig}")
                    else:
                        info_list[s].info(f"{s}: {sig}")

            # plot
            buffers["timestamp"].append(t)

            for s in signals_to_plot:
                val = signals.get(s, None)
                buffers[s].append(val if val is not None else float("nan"))

            df = pd.DataFrame({k: list(v) for k, v in buffers.items()})
            df_melt = df.melt(id_vars="timestamp", value_vars=signals_to_plot,
                              var_name="signal", value_name="value")

            fig = px.line(df_melt, 
                          x="timestamp", y="value", color="signal",
                          #title="Signale über Zeit",
                          labels={"value": "Wert", "timestamp": "Zeit"}
                          )
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

            plot_placeholder.plotly_chart(fig, width="stretch")

            # table
            table_data = {}
            for s in signals_to_list:
                table_data[s] = signals.get(s, None)

            with right_col_placeholder: 
                st.table(
                    table_data,
                    border="horizontal",
                    width="content",
                )

            # display signals 2
            for s in signals_to_display2:
                sig = signals.get(s, '---')
                if sig > 0:
                    info_list2[s].success(f"{s}: {sig}")
                else:
                    info_list2[s].info(f"{s}: {sig}")

            # json viewer
            with json_view:
                json_view.json(signals, expanded=True)

            # ~10 Hz
            time.sleep(0.005)

    except Exception as e:
        status_placeholder.error(f"Unerwarteter Fehler: {e}")
else:
    status_placeholder.info("Stopped")
    # clear
    #empty_df = pd.DataFrame({"timestamp": [], "value": [], "signal": []})
    #fig_empty = px.line(empty_df, x="timestamp", y="value")
    #plot_placeholder.plotly_chart(fig_empty, width="stretch")