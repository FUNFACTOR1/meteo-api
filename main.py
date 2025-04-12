# METEO SANDRA/main.py
from fastapi import FastAPI, HTTPException
# Importa CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import pytz
import requests
import os
from dotenv import load_dotenv
from math import floor

load_dotenv()

app = FastAPI()

# --- Configurazione CORS ---
# Specifica le origini consentite. "*" permette tutto, ma per maggiore sicurezza
# potresti limitarlo a "null" (per file locali file:///) o a un dominio specifico
# se servissi l'HTML da un altro sito web. Per ora usiamo "*" per semplicità.
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Consente tutti i metodi (GET, POST, etc.)
    allow_headers=["*"], # Consente tutti gli header
)
# --- Fine Configurazione CORS ---


OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    raise RuntimeError("Chiave API OpenWeatherMap non trovata nel file .env")

class InputData(BaseModel):
    citta: str
    giorno: str

# --- Funzioni Helper --- (uguali a prima)

def geocodifica_citta(citta: str):
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={citta},IT&limit=1&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        r = response.json()
        if not r:
            raise HTTPException(status_code=404, detail=f"Città '{citta}' non trovata.")
        return float(r[0]["lat"]), float(r[0]["lon"])
    except requests.exceptions.RequestException as e:
        print(f"Errore Geocoding API: {e}")
        raise HTTPException(status_code=503, detail="Servizio di geocodifica non disponibile.")
    except (KeyError, IndexError) as e:
        print(f"Errore parsing risposta Geocoding: {e}")
        raise HTTPException(status_code=500, detail="Errore nell'elaborazione dati geocoding.")

def colore_da_percentuale(val: float) -> str:
    if val <= 25: return "verde"
    if val <= 50: return "giallo"
    if val <= 75: return "arancio"
    return "rosso"

def colore_da_vento(val: float) -> str:
    if val < 2.8: return "verde"
    if val < 5.5: return "giallo"
    if val < 8.3: return "arancio"
    return "rosso"

def get_dati_meteo(citta: str, giorno_target_str: str):
    lat, lon = geocodifica_citta(citta)
    giorni_settimana = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    try:
        target_weekday = giorni_settimana.index(giorno_target_str.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Nome del giorno non valido.")

    tz_italia = pytz.timezone('Europe/Rome')
    oggi = datetime.now(tz_italia)
    offset_giorni = (target_weekday - oggi.weekday() + 7) % 7
    target_date = oggi + timedelta(days=offset_giorni)
    data_str = target_date.strftime('%Y-%m-%d')

    url_meteo = f"http://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric&lang=it"

    try:
        response = requests.get(url_meteo)
        response.raise_for_status()
        meteo_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Errore OpenWeather API: {e}")
        raise HTTPException(status_code=503, detail="Servizio meteo non disponibile.")
    except Exception as e:
        print(f"Errore parsing risposta Meteo: {e}")
        raise HTTPException(status_code=500, detail="Errore nell'elaborazione dati meteo.")

    fasce = {
        "slot_6_8": {"ore": [6, 7, 8], "pioggia_prob": [], "vento_vel": []},
        "slot_9_11": {"ore": [9, 10, 11], "pioggia_prob": [], "vento_vel": []},
        "slot_12_14": {"ore": [12, 13, 14], "pioggia_prob": [], "vento_vel": []},
    }
    risultati = {}

    if 'list' not in meteo_data:
         raise HTTPException(status_code=500, detail="Risposta API meteo non valida.")

    for forecast in meteo_data.get('list', []):
        dt_utc = datetime.fromtimestamp(forecast['dt'], tz=pytz.utc)
        dt_italia = dt_utc.astimezone(tz_italia)

        if dt_italia.strftime('%Y-%m-%d') == data_str:
            ora = dt_italia.hour
            prob_pioggia = forecast.get('pop', 0) * 100
            vel_vento = forecast.get('wind', {}).get('speed', 0)

            for nome_fascia, dettagli in fasce.items():
                if floor(ora / 3) * 3 in dettagli["ore"] or ora in dettagli["ore"]:
                    if prob_pioggia not in dettagli["pioggia_prob"]:
                       dettagli["pioggia_prob"].append(prob_pioggia)
                    if vel_vento not in dettagli["vento_vel"]:
                       dettagli["vento_vel"].append(vel_vento)

    for nome_fascia, dettagli in fasce.items():
        media_pioggia = sum(dettagli["pioggia_prob"]) / len(dettagli["pioggia_prob"]) if dettagli["pioggia_prob"] else 0
        media_vento = sum(dettagli["vento_vel"]) / len(dettagli["vento_vel"]) if dettagli["vento_vel"] else 0

        risultati[nome_fascia] = {
            "pioggia_avg": round(media_pioggia, 1),
            "pioggia_colore": colore_da_percentuale(media_pioggia),
            "vento_avg": round(media_vento, 1),
            "vento_colore": colore_da_vento(media_vento)
        }

    return risultati

# --- Endpoint API ---
@app.post("/meteo")
def analizza_dati(data: InputData):
    try:
        risultato = get_dati_meteo(data.citta, data.giorno)
        return risultato
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Errore non gestito: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server.")
