document.getElementById('meteoForm').addEventListener('submit', function(event) {
  event.preventDefault();

  const giorno = document.getElementById('giorno').value;
  const orario = document.getElementById('orario').value;
  const posizione = document.getElementById('posizione').value;

  const url = `https://meteo-api.onrender.com/meteo?giorno=${giorno}&orario=${orario}&posizione=${posizione}`;

  fetch(url)
    .then(response => response.json())
    .then(data => {
      const dettagli = document.getElementById('dettagli');
      
      const pioggiaClass = getColorClass(data.pioggia);
      const ventoClass = getColorClass(data.vento);

      dettagli.innerHTML = `
        <p><strong>Giorno:</strong> ${data.giorno}</p>
        <p><strong>Orario:</strong> ${data.orario}:00</p>
        <p><strong>Posizione:</strong> ${data.posizione}</p>
        <p><strong>Probabilità Pioggia:</strong> <span class="${pioggiaClass}">${data.pioggia}%</span></p>
        <p><strong>Probabilità Vento:</strong> <span class="${ventoClass}">${data.vento}%</span></p>
      `;
    })
    .catch(error => console.error('Errore:', error));
});

function getColorClass(probabilita) {
  if (probabilita < 20) {
    return 'green';
  } else if (probabilita < 40) {
    return 'yellow';
  } else if (probabilita < 60) {
    return 'orange';
  } else {
    return 'red';
  }
}
