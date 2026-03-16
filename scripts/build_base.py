import pandas as pd

actores = pd.read_excel("www/pi-actores.xlsx")
alineacion = pd.read_excel("www/alineacion_pi.xlsx")

estructura = pd.merge(
    actores,
    alineacion,
    how="outer"
)

estructura["Acción reportada"] = "Por reportar"

estructura["Fecha de inicio"] = "01-01-2025"
estructura["Fecha de finalización"] = "12-20-2025"

estructura["No. Línea de acción"] = estructura["Línea de acción"].str.extract(r'^(\S+)')

estructura.to_excel("base.xlsx", index=False)

print("Base creada correctamente")
