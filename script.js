// METEO SANDRA/script.js

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('giorni-container');
    const loadingMessage = document.getElementById('loading-message');

    // Array con la pianificazione basata sulle tue indicazioni
    // nomeMostrato: visualizzato nell'interfaccia
    // cittaApi: inviato all'API per il meteo
    const pianificazione = [
        { giorno: "Lunedì", nomeMostrato: "Mercato Mirano", cittaApi: "Mirano" },
        { giorno: "Martedì", nomeMostrato: "Mercato Marghera", cittaApi: "Marghera" },
        { giorno: "Mercoledì", nomeMostrato: "Mercato Mestre", cittaApi: "Mestre" },
        { giorno: "Venerdì", nomeMostrato: "Mercato Mestre", cittaApi: "Mestre" }, // Mestre si ripete
        { giorno: "Sabato", nomeMostrato: "Mercato Spinea", cittaApi: "Spinea" },
    ];

    // Nascondi messaggio di caricamento se non ci sono voci
    if (pianificazione.length === 0) {
        loadingMessage.textContent = "Nessuna pianificazione definita in script.js";
        return;
    } else {
        loadingMessage.style.display = 'none'; // Nascondi il messaggio "Caricamento..."
    }


    // Mappa i nomi dei colori del backend alle classi Tailwind
    function mapBackendColorToTailwind(colorName) {
        switch (colorName) {
            case "verde": return "bg-green-500";
            case "giallo": return "bg-yellow-400";
            case "arancio": return "bg-orange-500";
            case "rosso": return "bg-red-600";
            default: return "bg-gray-500"; // Colore di default per errori/sconosciuto
        }
    }

    // Genera le righe e chiama l'API per ciascuna
    pianificazione.forEach((item, index) => {
        const { giorno, nomeMostrato, cittaApi } = item;
        // Crea un ID univoco per la riga e gli indicatori basato sull'indice
        const rowId = `row-${index}`;
        // Suffix unico per gli ID basato su giorno, città e indice
        const idSuffix = `${giorno.toLowerCase()}-${cittaApi.toLowerCase().replace(/\s+/g, '-')}-${index}`;

        const row = document.createElement("div");
        row.id = rowId;
        // Usiamo flexbox per allineare meglio gli elementi
        row.className = "flex flex-wrap items-center gap-x-4 gap-y-2 bg-gray-800 p-4 rounded shadow";

        // Contenuto della riga con i placeholder per gli indicatori
        // Visualizza 'nomeMostrato' invece di 'cittaApi'
        row.innerHTML = `
            <div class="w-28 font-semibold text-lg text-white">${giorno}</div>
            <div class="flex-1 min-w-[100px] text-gray-300">${nomeMostrato}</div>

            <div class="flex flex-col items-center p-2 bg-gray-700 rounded min-w-[80px]">
                <span class="text-xs font-medium text-gray-300 mb-1">6-8</span>
                <div class="flex gap-2 mt-1">
                    <span id="precip-6-8-${idSuffix}" title="Precipitazioni 6-8" class="w-5 h-5 rounded-full loading-indicator"></span>
                    <span id="wind-6-8-${idSuffix}" title="Vento 6-8" class="w-5 h-5 rounded-full loading-indicator"></span>
                </div>
            </div>

            <div class="flex flex-col items-center p-2 bg-gray-700 rounded min-w-[80px]">
                <span class="text-xs font-medium text-gray-300 mb-1">9-11</span>
                <div class="flex gap-2 mt-1">
                    <span id="precip-9-11-${idSuffix}" title="Precipitazioni 9-11" class="w-5 h-5 rounded-full loading-indicator"></span>
                    <span id="wind-9-11-${idSuffix}" title="Vento 9-11" class="w-5 h-5 rounded-full loading-indicator"></span>
                </div>
            </div>

            <div class="flex flex-col items-center p-2 bg-gray-700 rounded min-w-[80px]">
                <span class="text-xs font-medium text-gray-300 mb-1">12-14</span>
                <div class="flex gap-2 mt-1">
                    <span id="precip-12-14-${idSuffix}" title="Precipitazioni 12-14" class="w-5 h-5 rounded-full loading-indicator"></span>
                    <span id="wind-12-14-${idSuffix}" title="Vento 12-14" class="w-5 h-5 rounded-full loading-indicator"></span>
                </div>
            </div>
            <div id="error-${idSuffix}" class="text-red-400 text-xs w-full pl-[calc(theme(space.28)_+_theme(space.4))] mt-1"></div> `;
        container.appendChild(row);

        // *** MODIFICA CHIAVE: Usa l'URL completo del servizio Render ***
        fetch('https://meteo-api.onrender.com/meteo', { // <--- URL AGGIORNATO QUI
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            // Invia 'cittaApi' al backend
            body: JSON.stringify({ citta: cittaApi, giorno: giorno })
        })
        .then(response => {
            if (!response.ok) {
                // Se la risposta non è OK (es. 4xx, 5xx), leggiamo il dettaglio dell'errore dal JSON
                return response.json().then(errData => {
                   // Tenta di estrarre il messaggio di errore, altrimenti usa un messaggio generico
                   const errorDetail = errData && errData.detail ? errData.detail : `Errore HTTP ${response.status}`;
                   throw new Error(errorDetail);
                });
            }
            return response.json(); // Processa la risposta JSON se OK
        })
        .then(data => {
            // Aggiorna gli indicatori con i colori corretti
            // Slot 6-8
            const p68 = document.getElementById(`precip-6-8-${idSuffix}`);
            const w68 = document.getElementById(`wind-6-8-${idSuffix}`);
            // Verifica che l'elemento esista e che i dati siano presenti prima di aggiornare
            if(p68 && data.slot_6_8) p68.className = `w-5 h-5 rounded-full ${mapBackendColorToTailwind(data.slot_6_8.pioggia_colore)}`;
            if(w68 && data.slot_6_8) w68.className = `w-5 h-5 rounded-full ${mapBackendColorToTailwind(data.slot_6_8.vento_colore)}`;

            // Slot 9-11
            const p911 = document.getElementById(`precip-9-11-${idSuffix}`);
            const w911 = document.getElementById(`wind-9-11-${idSuffix}`);
            if(p911 && data.slot_9_11) p911.className = `w-5 h-5 rounded-full ${mapBackendColorToTailwind(data.slot_9_11.pioggia_colore)}`;
            if(w911 && data.slot_9_11) w911.className = `w-5 h-5 rounded-full ${mapBackendColorToTailwind(data.slot_9_11.vento_colore)}`;

            // Slot 12-14
            const p1214 = document.getElementById(`precip-12-14-${idSuffix}`);
            const w1214 = document.getElementById(`wind-12-14-${idSuffix}`);
            if(p1214 && data.slot_12_14) p1214.className = `w-5 h-5 rounded-full ${mapBackendColorToTailwind(data.slot_12_14.pioggia_colore)}`;
            if(w1214 && data.slot_12_14) w1214.className = `w-5 h-5 rounded-full ${mapBackendColorToTailwind(data.slot_12_14.vento_colore)}`;

            // Aggiungi tooltip con i valori numerici (usando ?? 'N/D' per dati mancanti)
            if(p68) p68.title = `Precipitazioni 6-8: ${data.slot_6_8?.pioggia_avg ?? 'N/D'}%`;
            if(w68) w68.title = `Vento 6-8: ${data.slot_6_8?.vento_avg ?? 'N/D'} m/s`;
            if(p911) p911.title = `Precipitazioni 9-11: ${data.slot_9_11?.pioggia_avg ?? 'N/D'}%`;
            if(w911) w911.title = `Vento 9-11: ${data.slot_9_11?.vento_avg ?? 'N/D'} m/s`;
            if(p1214) p1214.title = `Precipitazioni 12-14: ${data.slot_12_14?.pioggia_avg ?? 'N/D'}%`;
            if(w1214) w1214.title = `Vento 12-14: ${data.slot_12_14?.vento_avg ?? 'N/D'} m/s`;

        })
        .catch(error => {
            console.error(`Errore nel recuperare dati per ${nomeMostrato} (${cittaApi}), ${giorno}:`, error);
            // Mostra un messaggio di errore specifico per quella riga
             const errorDiv = document.getElementById(`error-${idSuffix}`);
             if(errorDiv) {
                 // Mostra il messaggio di errore estratto o uno generico
                 errorDiv.textContent = `Errore: ${error.message || 'Impossibile caricare i dati'}`;
             }
            // Cambia colore agli indicatori per mostrare l'errore
            const indicatorIds = [
                `precip-6-8-${idSuffix}`, `wind-6-8-${idSuffix}`,
                `precip-9-11-${idSuffix}`, `wind-9-11-${idSuffix}`,
                `precip-12-14-${idSuffix}`, `wind-12-14-${idSuffix}`
            ];
            indicatorIds.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.className = 'w-5 h-5 rounded-full bg-gray-500'; // Grigio scuro per errore
            });
        });
    });
});
