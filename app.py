"""
Hlavni modul pro Streamlit Dashboard.
Konfigurace vzhledu stranky roztahne obsah na celou sirku obrazovky a nastavi titulek.
Automaticky refresh stranky zajistuje znovunacteni a prepsani metrik nejnovejsimi hodnotami.
"""
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time

st.set_page_config(page_title="PyProfit Live Trading", layout="wide")

def safe_float(val):
    """
    Bezpecne pretypuje textovou hodnotu z Google Tabulky na desetinne cislo.
    Automaticky nahradi ceske desetinne carky za tecky.
    Pokud prevod selze (napr. prazdna bunka), vrati bezpecnou nulu, aby aplikace nespadla.
    """
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def init_connection():
    """
    Inicializuje pripojeni ke Google Sheets pomoci servisniho uctu.
    Pouziva uloziste Streamlit Secrets pro bezpecne nacteni udaju.
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client

def render_dashboard():
    """
    Hlavni funkce pro stazeni dat a vykresleni obsahu webu.
    Nacita data z listu Live (radek 2) a historii z listu History.
    Hodnoty pravdepodobnosti formatuje striktne na 2 desetinna mista pro cisty webovy vystup.
    """
    st.title("📈 PyProfit AI Trading Dashboard")
    
    try:
        client = init_connection()
        sheet_live = client.open("PyProfit_Data").worksheet("Live")
        sheet_history = client.open("PyProfit_Data").worksheet("History")
    except Exception as e:
        st.error(f"Chyba pripojeni k databazi: {e}")
        return

    live_data = sheet_live.row_values(2)
    
    if not live_data or len(live_data) < 9:
        st.info("Cekam na prvni data od obchodniho bota...")
        return

    last_update = live_data[0]
    status = live_data[1]
    volume = live_data[2]
    open_price = live_data[3]
    current_price = live_data[4]
    profit = live_data[5]
    
    buy_pct = f"{safe_float(live_data[6]):.2f}"
    hold_pct = f"{safe_float(live_data[7]):.2f}"
    sell_pct = f"{safe_float(live_data[8]):.2f}"

    st.caption(f"Poslední aktualizace: {last_update}")

    st.subheader("🤖 Pohled Neuronové Sítě (Poslední Svíčka)")
    col_buy, col_hold, col_sell = st.columns(3)
    with col_buy:
        st.metric(label="🟢 BUY Signál", value=f"{buy_pct} %")
    with col_hold:
        st.metric(label="⚪ HOLD Signál", value=f"{hold_pct} %")
    with col_sell:
        st.metric(label="🔴 SELL Signál", value=f"{sell_pct} %")

    st.markdown("---")

    st.subheader("📊 Aktuální Otevřená Pozice")
    if status == "FLAT":
        st.success("Žádná otevřená pozice. Bot čeká na příležitost.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Směr", status)
        with col2:
            st.metric("Velikost (Lot)", volume)
        with col3:
            st.metric("Vstupní Cena", open_price)
        with col4:
            st.metric("Aktuální Profit ($)", profit)

    st.markdown("---")

    st.subheader("📚 Historie Obchodů")
    hist_data = sheet_history.get_all_values()
    
    if len(hist_data) > 1:
        headers = hist_data[0]
        rows = hist_data[1:]
        df_history = pd.DataFrame(rows, columns=headers)
        st.dataframe(df_history, use_container_width=True)
    else:
        st.info("Zatím nebyl uzavřen žádný obchod.")

if __name__ == "__main__":
    render_dashboard()
    time.sleep(30)
    st.rerun()
