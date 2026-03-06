"""
Hlavni webovy dashboard pro PyProfit.
Vizualizuje zive obchody (Unrealized PnL) a historicke statistiky ze dvou listu Google Tabulky.
"""
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def setup_page():
    """
    Nastavi parametry stranky pro siroky format a vlozi hlavni titulek.
    """
    st.set_page_config(page_title="PyProfit | Live AI Trading", page_icon="📈", layout="wide")
    st.title("📈 PyProfit AI Trading Dashboard")
    st.markdown("---")

@st.cache_data(ttl=15)
def fetch_all_data():
    """
    Stahne data z obou listu (Live a History).
    Cache je nastavena na 15 sekund, aby se nerealizovany PnL aktualizoval velmi rychle.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet_live = client.open("PyProfit_Data").worksheet("Live")
        sheet_history = client.open("PyProfit_Data").worksheet("History")
        
        data_live = sheet_live.get_all_records()
        data_history = sheet_history.get_all_records()
        
        return pd.DataFrame(data_live), pd.DataFrame(data_history)
    except Exception as e:
        st.error(f"Chyba databaze: {e}")
        return pd.DataFrame(), pd.DataFrame()

def render_live_status(df_live):
    """
    Vykresli prominentni sekci s aktualne otevrenym obchodem.
    Pokud je stav FLAT, zobrazi informaci o cekani na signal.
    """
    st.subheader("🔴 Live Market Status")
    
    if df_live.empty:
        st.info("Zadne spojeni s botem.")
        return

    live_data = df_live.iloc[0]
    stav = live_data["Stav"]
    
    if stav == "FLAT":
        st.info(f"Bot je aktuálně bez pozice (FLAT). Čeká na další obchodní příležitost. Poslední ping: {live_data['Posledni_Aktualizace']}")
    else:
        col1, col2, col3, col4 = st.columns(4)
        unrealized_pnl = float(live_data["Unrealized_PnL"])
        
        col1.metric("Směr obchodu", f"{stav} {live_data['Lot']} Lot")
        col2.metric("Vstupní cena", str(live_data["Vstupni_Cena"]))
        col3.metric("Aktuální cena", str(live_data["Aktualni_Cena"]))
        col4.metric("Unrealized PnL", f"${unrealized_pnl:.2f}", f"{unrealized_pnl:.2f}")

    st.markdown("---")

def render_historical_metrics(df_history):
    """
    Vykresli celkove statistiky a historii uzavrenych obchodu.
    """
    st.subheader("📊 Celkové statistiky")
    
    if df_history.empty:
        st.warning("Zatim zadne dokoncene obchody.")
        return
        
    posledni_zustatek = float(df_history["Zustatek"].iloc[-1])
    celkovy_zisk = df_history["Zisk"].sum()
    uspesne_obchody = len(df_history[df_history["Zisk"] > 0])
    win_rate = (uspesne_obchody / len(df_history) * 100) if len(df_history) > 0 else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Aktuální zůstatek", f"${posledni_zustatek:.2f}", f"{celkovy_zisk:.2f} USD")
    col2.metric("Počet obchodů", str(len(df_history)))
    col3.metric("Win Rate", f"{win_rate:.1f} %")
    
    st.subheader("Vývoj účtu (Equity Curve)")
    st.line_chart(df_history.set_index("Cas")["Zustatek"])

    st.subheader("Historie obchodů")
    st.dataframe(df_history, use_container_width=True)

def main():
    """
    Spousteci bod webove aplikace.
    """
    setup_page()
    df_live, df_history = fetch_all_data()
    render_live_status(df_live)
    render_historical_metrics(df_history)

if __name__ == "__main__":
    main()
