"""
Hlavni soubor pro webovy dashboard PyProfit.
Tento skript bezi na Streamlit Cloud a vizualizuje data o obchodech z Google Sheets.
"""
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def setup_page():
    """
    Nastavi zakladni parametry stranky a hlavicku aplikace.
    Rozlozeni 'wide' zajisti, ze grafy vyuziji celou sirku monitoru.
    """
    st.set_page_config(page_title="PyProfit | Live Trading", page_icon="📈", layout="wide")
    st.title("📈 PyProfit AI Trading Dashboard")
    st.markdown("---")

@st.cache_data(ttl=60)
def fetch_data():
    """
    Pripoji se ke Google Sheets pomoci tajnych klicu (secrets) a stahne data.
    Ocekava tabulku se sloupci: Cas, Akce, Cena, Lot, Duvera, Zisk, Zustatek.
    Cache ttl=60 zajisti, ze se data stahuji maximalne jednou za minutu, 
    aby se nevycerpal limit Google API.
    """
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        sheet = client.open("PyProfit_Data").sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Chyba pripojeni k databazi: {e}")
        return pd.DataFrame()

def calculate_metrics(df):
    """
    Vypocita a zobrazi hlavni statistiky nad stazenymi daty.
    Zahrnuje aktualni zustatek, celkovy profit, pocet obchodu a Win Rate.
    """
    if df.empty:
        st.warning("Zatim zadna data k zobrazeni. Ceka se na prvni obchod.")
        return

    posledni_zustatek = float(df["Zustatek"].iloc[-1])
    pocatecni_zustatek = float(df["Zustatek"].iloc[0])
    celkovy_zisk = posledni_zustatek - pocatecni_zustatek
    
    uspesne_obchody = len(df[df["Zisk"] > 0])
    vsechny_ukoncene_obchody = len(df[df["Zisk"] != 0])
    win_rate = (uspesne_obchody / vsechny_ukoncene_obchody * 100) if vsechny_ukoncene_obchody > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Aktualni zustatek", f"${posledni_zustatek:.2f}", f"{celkovy_zisk:.2f} USD")
    col2.metric("Celkem obchodu", str(len(df)))
    col3.metric("Win Rate", f"{win_rate:.1f} %")
    col4.metric("Posledni akce", str(df["Akce"].iloc[-1]))
    
    st.markdown("---")

def render_charts(df):
    """
    Vykresli interaktivni graf vyvoje zustatku (Equity krivka) 
    a zobrazi tabulku s podrobnou historii vsech obchodu.
    """
    if df.empty:
        return

    st.subheader("Vývoj účtu (Equity Curve)")
    st.line_chart(df.set_index("Cas")["Zustatek"])

    st.subheader("Historie obchodů")
    st.dataframe(df, use_container_width=True)

def main():
    """
    Hlavni ridici funkce webove aplikace.
    Volana pri spusteni skriptu.
    """
    setup_page()
    df = fetch_data()
    calculate_metrics(df)
    render_charts(df)

if __name__ == "__main__":
    main()
