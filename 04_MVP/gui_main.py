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

st.set_page_config(page_title="CAN-Signale Live", layout="wide")

st.title("Live CAN-Signale (10 Hz Polling)")
st.caption("Drücke Start, um die Abfrage zu beginnen. Stopp beendet die Schleife.")

# --- Konfiguration: lokale API-Adresse ---
api_url = "http://localhost:5001/data/can_c"

# Signale, die geplottet werden sollen
signals_to_plot = [
    #"V_MPH", 
    "VB", 
    #"T_MOT", 
    #"T_AUSSEN",
    "V_ANZ"
]

# Wahl der Fenstergröße (Anzahl Messpunkte, z.B. 10 Sekunden bei 10 Hz = 100)
window_size = st.sidebar.number_input("Fenstergröße (Messpunkte)", min_value=10, max_value=5000, value=200, step=10)

start_btn = st.button("Start")
stop_btn = st.button("Stop")

# Speicher für Zeitstempel und Signale (fixed-size rolling buffer)
buffers = {s: deque(maxlen=window_size) for s in signals_to_plot}
buffers["timestamp"] = deque(maxlen=window_size)

# Display fields for latest values
st.subheader("Aktuelle Werte")
value_cols = st.columns(len(signals_to_plot))
value_placeholders = {s: value_cols[i].empty() for i, s in enumerate(signals_to_plot)}

status_placeholder = st.empty()
plot_placeholder = st.empty()

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
    status_placeholder.info("Polling läuft... (≈10 Hz). Stopper drücken, um zu stoppen.")
    try:
        while st.session_state.get("running", False):
            t = pd.Timestamp.now()
            data = fetch_once(api_url)
            if "error" in data:
                status_placeholder.warning(f"Fehler bei API-Abfrage: {data['error']}")
                time.sleep(0.5)
                continue

            signals = data.get("signals", {})

            buffers["timestamp"].append(t)
            for s in signals_to_plot:
                val = signals.get(s, None)
                buffers[s].append(val if val is not None else float("nan"))

            df = pd.DataFrame({k: list(v) for k, v in buffers.items()})
            df_melt = df.melt(id_vars="timestamp", value_vars=signals_to_plot,
                              var_name="signal", value_name="value")

            fig = px.line(df_melt, x="timestamp", y="value", color="signal",
                          title="Signale über Zeit",
                          labels={"value": "Wert", "timestamp": "Zeit"})
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

            plot_placeholder.plotly_chart(fig, width="stretch")

            # ~10 Hz
            time.sleep(0.01)

    except Exception as e:
        status_placeholder.error(f"Unerwarteter Fehler: {e}")
else:
    status_placeholder.info("Polling gestoppt. Drücke Start, um zu beginnen.")
    empty_df = pd.DataFrame({"timestamp": [], "value": [], "signal": []})
    fig_empty = px.line(empty_df, x="timestamp", y="value")
    plot_placeholder.plotly_chart(fig_empty, width="stretch")