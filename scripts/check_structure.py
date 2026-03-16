import pandas as pd

actores = pd.read_excel("www/pi-actores.xlsx")
alineacion = pd.read_excel("www/alineacion_pi.xlsx")

la_actores = actores["Línea de acción"].drop_duplicates()

la_alineacion = alineacion["Línea de acción"].drop_duplicates()

check = pd.merge(
    la_actores,
    la_alineacion,
    how="outer",
    indicator=True
)

check["match"] = check["_merge"] == "both"

check.to_excel("check.xlsx", index=False)

print("Chequeo completado")
