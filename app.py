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

SYMBOLS = ["EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCAD"]

def safe_float(val):
    """
    Bezpecne pretypuje textovou hodnotu z Google Tabulky na desetinne cislo.
    Automaticky nahradi ceske desetinne carky za tecky.
    """
    try:
        if isinstance(val, str):
            val = val.replace(',', '.')
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def init_connection():
    """
    Inicializuje pripojeni ke Google Sheets pomoci servisniho uctu z uloziste Secrets.
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    return client

def render_dashboard():
    """
    Hlavni funkce pro stazeni dat a vykresleni obsahu webu napric 5 trhy.
    Vyuziva zalozky (tabs) pro ciste a prehledne UI.
    """
    st.title("📈 PyProfit AI Trading Dashboard")
    
    try:
        client = init_connection()
        sheet_live = client.open("PyProfit_Data").worksheet("Live")
        sheet_history = client.open("PyProfit_Data").worksheet("History")
    except Exception as e:
        st.error(f"Chyba pripojeni k databazi: {e}")
        return

    # Stazeni vsech 5 radku naráz (bunky A2 az I6) setri kvoty Google API
    live_data_rows = sheet_live.get("A2:I6")
    
    if not live_data_rows:
        st.info("Cekam na prvni data od obchodniho bota...")
        return

    # Vytvoreni zalozek pro kazdy menovy par
    tabs = st.tabs(SYMBOLS)

    for i, tab in enumerate(tabs):
        with tab:
            if i < len(live_data_rows):
                row = live_data_rows[i]
                
                # Bezpecnostni vycpavka pro pripad, ze by chybel sloupec
                while len(row) < 9:
                    row.append("0")

                last_update = row[0]
                status_raw = row[1]
                volume = row[2]
                open_price = row[3]
                current_price = row[4]
                profit = row[5]
                
                buy_pct = f"{safe_float(row[6]):.2f}"
                hold_pct = f"{safe_float(row[7]):.2f}"
                sell_pct = f"{safe_float(row[8]):.2f}"

                st.caption(f"Poslední aktualizace: {last_update}")

                st.subheader(f"🤖 Pohled Neuronové Sítě ({SYMBOLS[i]})")
                col_buy, col_hold, col_sell = st.columns(3)
                with col_buy:
                    st.metric(label="🟢 BUY Signál", value=f"{buy_pct} %")
                with col_hold:
                    st.metric(label="⚪ HOLD Signál", value=f"{hold_pct} %")
                with col_sell:
                    st.metric(label="🔴 SELL Signál", value=f"{sell_pct} %")

                st.markdown("---")

                st.subheader("📊 Aktuální Otevřená Pozice")
                if "FLAT" in status_raw:
                    st.success("Žádná otevřená pozice. Bot čeká na čistý signál nad 70 %.")
                else:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Stav", status_raw)
                    with col2:
                        st.metric("Velikost (Lot)", volume)
                    with col3:
                        st.metric("Vstupní Cena", open_price)
                    with col4:
                        st.metric("Aktuální Profit ($)", profit)
            else:
                st.info("Zatím nejsou data pro tento trh.")

    st.markdown("---")

    st.subheader("📚 Agregovaná Historie Obchodů")
    hist_data = sheet_history.get_all_values()
    
    if len(hist_data) > 1:
        headers = hist_data[0]
        rows = hist_data[1:]
        df_history = pd.DataFrame(rows, columns=headers)
        # Zobrazeni dataframe od nejnovejsiho obchodu po nejstarsi
        st.dataframe(df_history.iloc[::-1], use_container_width=True)
    else:
        st.info("Zatím nebyl uzavřen žádný obchod.")

if __name__ == "__main__":
    render_dashboard()
    time.sleep(30)
    st.rerun()
