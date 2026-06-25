import pyodbc

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=MARIANA;"
        "DATABASE=BD_Siniestros;"
        "Trusted_Connection=yes;"
    )