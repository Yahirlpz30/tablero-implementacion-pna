import pandas as pd
from services.dropbox_service import upload_excel_dropbox

df = pd.read_excel("base.xlsx")

upload_excel_dropbox(
    df,
    "/tablero_prueba/base.xlsx"
)

print("Base subida a Dropbox")
