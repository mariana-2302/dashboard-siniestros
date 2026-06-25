def aplicar_estilos() -> str:
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif !important;
    }
    .block-container {
        max-width: 100%;
        padding: 1.5rem 2rem 2rem 2rem;
    }

    /* ── Sidebar visible y limpio ── */
    section[data-testid="stSidebar"] {
        display: block !important;
        background: #F8F9FB;
        border-right: 0.5px solid #E4E8EF;
        min-width: 220px !important;
        max-width: 260px !important;
    }
    section[data-testid="stSidebar"] > div {
        padding: 1.5rem 1.25rem;
    }

    /* Selectbox en sidebar */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div {
        border: 0.5px solid #D0D8E4 !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        background: #fff !important;
    }

    /* Botón limpiar en sidebar */
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        border: 0.5px solid #D0D8E4 !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        background: #fff !important;
        color: #5A7FA8 !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
        background: #E6F1FB !important;
        border-color: #185FA5 !important;
        color: #185FA5 !important;
    }

    /* Tabs */
    div[data-testid="stTabs"] button {
        font-family: 'DM Sans', sans-serif !important;
        font-size: 12px !important;
        font-weight: 400;
        color: #888780 !important;
        padding: 8px 14px !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #185FA5 !important;
        font-weight: 500 !important;
    }
    div[data-testid="stTabs"] button:hover {
        color: #185FA5 !important;
    }

    /* Footer */
    .footer {
        text-align: center;
        font-size: 11px;
        color: #aaa;
        margin-top: 32px;
        padding-top: 14px;
        border-top: 0.5px solid #e8e8e8;
    }
    </style>
    """