# METEO SANDRA/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import pytz
import requests
import os
from dotenv import load_dotenv
from math import floor # Usato per arrotondare l'ora

load_dotenv() # Carica le variabili dal file .env

app = FastAPI()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    raise RuntimeError("Chiave API OpenWeatherMap non trovata nel file .env")

# Input atteso dall'API: solo città e giorno
class InputData(BaseModel):
    citta: str
    giorno: str # Es. "Lunedì", "Martedì", ...

# --- Funzioni Helper ---

def geocodifica_citta(citta: str):
    """Ottiene latitudine e longitudine da OpenWeatherMap Geocoding API."""
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={citta},IT&limit=1&appid={OPENWEATHER_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status() # Solleva eccezione per errori HTTP (4xx, 5xx)
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
    """Restituisce il nome del colore basato sulla percentuale di probabilità pioggia."""
    # Soglie leggermente aggiustate per matchare meglio la legenda 0-25, 26-50, 51-75, 76-100
    if val <= 25: return "verde"
    if val <= 50: return "giallo"
    if val <= 75: return "arancio"
    return "rosso"

def colore_da_vento(val: float) -> str:
    """Restituisce il nome del colore basato sulla velocità del vento (in m/s)."""
    # Soglie indicative (puoi aggiustarle) - OpenWeather dà m/s, non km/h
    # < 2.8 m/s (~10 km/h) -> verde
    # < 5.5 m/s (~20 km/h) -> giallo
    # < 8.3 m/s (~30 km/h) -> arancio
    # >= 8.3 m/s -> rosso
    if val < 2.8: return "verde"
    if val < 5.5: return "giallo"
    if val < 8.3: return "arancio"
    return "rosso"

def get_dati_meteo(citta: str, giorno_target_str: str):
    """Recupera e processa dati meteo per le fasce orarie definite."""
    lat, lon = geocodifica_citta(citta)

    # --- Calcolo Data Target ---
    giorni_settimana = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
    try:
        target_weekday = giorni_settimana.index(giorno_target_str.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Nome del giorno non valido.")

    # Usiamo il fuso orario locale (Italia)
    tz_italia = pytz.timezone('Europe/Rome')
    oggi = datetime.now(tz_italia)
    offset_giorni = (target_weekday - oggi.weekday() + 7) % 7 # Offset per arrivare al giorno target nella settimana corrente o prossima
    target_date = oggi + timedelta(days=offset_giorni)
    data_str = target_date.strftime('%Y-%m-%d')

    # --- Chiamata API OpenWeatherMap (5 day / 3 hour forecast) ---
    # Nota: La One Call API 3.0 sarebbe migliore per dati orari, ma richiede sottoscrizione a pagamento.
    # La 5 day / 3 hour è gratuita ma meno granulare. Adattiamo le fasce orarie.
    # Se hai accesso alla One Call API 3.0, usa quella.
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

    # --- Elaborazione Dati per Fasce Orarie ---
    fasce = {
        "slot_6_8": {"ore": [6, 7, 8], "pioggia_prob": [], "vento_vel": []},
        "slot_9_11": {"ore": [9, 10, 11], "pioggia_prob": [], "vento_vel": []},
        "slot_12_14": {"ore": [12, 13, 14], "pioggia_prob": [], "vento_vel": []},
    }
    risultati = {}

    if 'list' not in meteo_data:
         raise HTTPException(status_code=500, detail="Risposta API meteo non valida.")

    for forecast in meteo_data.get('list', []):
        # Timestamp UTC fornito dall'API
        dt_utc = datetime.fromtimestamp(forecast['dt'], tz=pytz.utc)
        # Converti in fuso orario italiano
        dt_italia = dt_utc.astimezone(tz_italia)

        # Controlla se la previsione è per il giorno target
        if dt_italia.strftime('%Y-%m-%d') == data_str:
            ora = dt_italia.hour
            prob_pioggia = forecast.get('pop', 0) * 100 # 'pop' è probabilità da 0 a 1
            vel_vento = forecast.get('wind', {}).get('speed', 0) # velocità in m/s

            # Assegna i dati alla fascia oraria corretta
            for nome_fascia, dettagli in fasce.items():
                # Arrotondiamo l'ora per matchare l'intervallo 3h dell'API free
                # Se l'ora della previsione (es. 9) rientra nel range della fascia (es. 9-11)
                # l'API 5gg/3h dà un solo valore (es. alle 9:00) valido per le 3h successive.
                # Prendiamo il valore se l'ora della previsione rientra nella fascia.
                if floor(ora / 3) * 3 in dettagli["ore"] or ora in dettagli["ore"]: # Cerchiamo di catturare il dato più rilevante per la fascia
                     # Evita duplicati se più ore della fascia mappano sullo stesso blocco 3h
                    if prob_pioggia not in dettagli["pioggia_prob"]:
                       dettagli["pioggia_prob"].append(prob_pioggia)
                    if vel_vento not in dettagli["vento_vel"]:
                       dettagli["vento_vel"].append(vel_vento)


    # --- Calcolo Medie e Colori per Fascia ---
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
    """Endpoint principale che riceve città/giorno e restituisce i dati meteo per fasce."""
    try:
        risultato = get_dati_meteo(data.citta, data.giorno)
        return risultato
    except HTTPException as e:
        # Rilancia le eccezioni HTTP gestite nelle funzioni helper
        raise e
    except Exception as e:
        # Cattura altri errori imprevisti
        print(f"Errore non gestito: {e}")
        raise HTTPException(status_code=500, detail="Errore interno del server.")

# Non includere '</html>' alla fine!
