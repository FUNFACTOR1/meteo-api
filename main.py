from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import pytz
import requests

app = FastAPI()

class InputData(BaseModel):
    città: str
    giorno: str
    orario_inizio: int
    orario_fine: int

@app.post("/meteo")
def analizza_dati(data: InputData):
    return get_dati_meteo(data.città, data.giorno, data.orario_inizio, data.orario_fine)

def geocodifica_città(città):
    url = f"https://nominatim.openstreetmap.org/search?q={città}&format=json"
    r = requests.get(url).json()
    return float(r[0]["lat"]), float(r[0]["lon"])

def get_dati_meteo(città, giorno, orario_inizio, orario_fine):
    lat, lon = geocodifica_città(città)
    oggi = datetime.now(pytz.timezone('Europe/Rome'))
    giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    offset = giorni.index(giorno.lower()) - oggi.weekday()
    target = oggi + timedelta(days=offset)
    data_str = target.strftime('%Y-%m-%d')

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation_probability,wind_speed_10m&timezone=auto"
    r = requests.get(url).json()
    orari = r["hourly"]["time"]
    pioggia = r["hourly"]["precipitation_probability"]
    vento = r["hourly"]["wind_speed_10m"]

    p_vals = []
    v_vals = []

    for i, orario in enumerate(orari):
        if orario.startswith(data_str):
            ora = int(orario[11:13])
            if orario_inizio <= ora < orario_fine:
                p_vals.append(pioggia[i])
                v_vals.append(vento[i])

    media_pioggia = sum(p_vals)/len(p_vals) if p_vals else 0
    media_vento = sum(v_vals)/len(v_vals) if v_vals else 0

    return {
        "media_pioggia": round(media_pioggia, 1),
        "colore_pioggia": colore_da_percentuale(media_pioggia),
        "media_vento": round(media_vento, 1),
        "colore_vento": colore_da_vento(media_vento)
    }

def colore_da_percentuale(val):
    if val <= 20: return "verde"
    if val <= 50: return "giallo"
    if val <= 80: return "arancio"
    return "rosso"

def colore_da_vento(val):
    if val < 10: return "verde"
    if val < 20: return "giallo"
    if val < 30: return "arancio"
    return "rosso"
