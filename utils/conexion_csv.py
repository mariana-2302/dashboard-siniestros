import pandas as pd
import os
import streamlit as st

DATA_DIR = "data"  # carpeta donde están los CSVs

@st.cache_data(ttl=86400)
def load_table(nombre: str) -> pd.DataFrame:
    """Carga un CSV del datamart. Asume separador ; y encoding utf-8-sig."""
    path = os.path.join(DATA_DIR, f"{nombre}.csv")
    return pd.read_csv(path, sep=";", encoding="utf-8-sig", low_memory=False)