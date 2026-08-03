const map = L.map('map').setView([41.3, 69.2], 6);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 19
}).addTo(map);

let radarLayer = null;
let radarData = null;
let currentFrame = 0;
let playTimer = null;
let radarOn = true;
let userMarker = null;

const btnRadar = document.getElementById('btn-radar');
const btnPlay = document.getElementById('btn-play');
const btnLocate = document.getElementById('btn-locate');
const slider = document.getElementById('slider');
const timeLabel = document.getElementById('time-label');
const weatherBox = document.getElementById('weather-box');
const searchInput = document.getElementById('search');
const searchResults = document.getElementById('search-results');

async function loadRadar() {
    try {
        const resp = await fetch('/api/radar');
        const data = await resp.json();
        if (data.error) throw new Error(data.error);
        radarData = data;
        slider.max = data.radar.past.length + data.radar.nowcast.length - 1;
        slider.value = data.radar.past.length - 1;
        currentFrame = data.radar.past.length - 1;
        btnPlay.disabled = false;
        slider.disabled = false;
        showFrame(currentFrame);
    } catch (e) {
        timeLabel.textContent = 'Xato: ' + e.message;
    }
}

function getFrame(i) {
    if (!radarData) return null;
    const pastLen = radarData.radar.past.length;
    if (i < pastLen) {
        return { path: radarData.radar.past[i].path, time: radarData.radar.past[i].time, forecast: false };
    }
    return { path: radarData.radar.nowcast[i - pastLen].path, time: radarData.radar.nowcast[i - pastLen].time, forecast: true };
}

function showFrame(i) {
    if (!radarData) return;
    currentFrame = i;
    const frame = getFrame(i);
    const tileUrl = radarData.host + frame.path + '/256/{z}/{x}/{y}/0/0_0.png';
    if (radarLayer) {
        map.removeLayer(radarLayer);
    }
    radarLayer = L.tileLayer(tileUrl, {
        opacity: 0.6,
        transparent: true,
        maxZoom: 10
    });
    if (radarOn) radarLayer.addTo(map);
    const forecastMark = frame.forecast ? ' [PROGNOZ]' : '';
    timeLabel.textContent = new Date(frame.time * 1000).toLocaleString() + forecastMark;
}

slider.addEventListener('input', (e) => {
    stopPlay();
    showFrame(parseInt(e.target.value));
});

btnRadar.addEventListener('click', () => {
    radarOn = !radarOn;
    btnRadar.textContent = radarOn ? 'Radar: Yoqilgan' : 'Radar: O\'chirilgan';
    btnRadar.classList.toggle('active', radarOn);
    if (radarOn && radarLayer) {
        radarLayer.addTo(map);
    } else if (radarLayer) {
        map.removeLayer(radarLayer);
    }
});

btnPlay.addEventListener('click', () => {
    if (playTimer) {
        stopPlay();
        return;
    }
    btnPlay.textContent = '⏸ To\'xtatish';
    const total = radarData.radar.past.length + radarData.radar.nowcast.length;
    playTimer = setInterval(() => {
        currentFrame = (currentFrame + 1) % total;
        slider.value = currentFrame;
        showFrame(currentFrame);
    }, 700);
});

function stopPlay() {
    if (playTimer) {
        clearInterval(playTimer);
        playTimer = null;
        btnPlay.textContent = '▶ O\'ynatish';
    }
}

const WMO_CODES = {
    0: '☀️ Och',
    1: '🌤 Asosan och',
    2: '⛅ Qisman bulutli',
    3: '☁️ Bulutli',
    45: '🌫 Tuman',
    48: '🌫 Muzli tuman',
    51: '🌦 Yengil yomg\'ir',
    53: '🌦 Mo\'tadil yomg\'ir',
    55: '🌧 Kuchli yomg\'ir',
    61: '🌦 Yengil yomg\'ir',
    63: '🌧 Yomg\'ir',
    65: '🌧 Kuchli yomg\'ir',
    71: '🌨 Yengil qor',
    73: '❄️ Qor',
    75: '❄️ Kuchli qor',
    80: '🌦 Qisqa yomg\'ir',
    81: '🌧 Qisqa kuchli yomg\'ir',
    82: '⛈ Kuchli jala',
    95: '⛈ Momaqaldiroq',
    96: '⛈ Momaqaldiroq + do\'l',
    99: '⛈ Kuchli momaqaldiroq'
};

async function showWeather(lat, lon) {
    try {
        const resp = await fetch(`/api/weather?lat=${lat}&lon=${lon}`);
        const data = await resp.json();
        if (data.error) throw new Error(data.error);
        const cur = data.current;
        const days = data.daily;
        let forecast = '';
        for (let i = 0; i < days.time.length; i++) {
            const d = new Date(days.time[i] + 'T00:00');
            const label = d.toLocaleDateString('uz-UZ', { weekday: 'short', day: 'numeric' });
            forecast +=
                `<tr><td>${label}</td><td>${WMO_CODES[days.weather_code[i]] || '?'}</td>` +
                `<td>${days.temperature_2m_max[i]}°/${days.temperature_2m_min[i]}°</td>` +
                `<td>💧${days.precipitation_probability_max[i]}%</td></tr>`;
        }
        weatherBox.classList.remove('hidden');
        weatherBox.innerHTML =
            `<h3>Ob-havo</h3>
             <p>🌡 ${cur.temperature_2m}°C (seziladi: ${cur.apparent_temperature}°C)</p>
             <p>💨 Shamol: ${cur.wind_speed_10m} km/soat</p>
             <p>💧 Namlik: ${cur.relative_humidity_2m}%</p>
             <table class="forecast">${forecast}</table>
             <p class="updated">Yangilangan: ${cur.time}</p>`;
    } catch (e) {
        weatherBox.classList.remove('hidden');
        weatherBox.innerHTML = `<h3>Ob-havo</h3><p>Xato: ${e.message}</p>`;
    }
}

function placeMarker(lat, lon, name) {
    if (userMarker) map.removeLayer(userMarker);
    userMarker = L.marker([lat, lon]).addTo(map)
        .bindPopup(name || 'Sizning joylashuvingiz').openPopup();
    map.setView([lat, lon], 8);
}

btnLocate.addEventListener('click', () => {
    if (!navigator.geolocation) {
        alert('Brauzeringiz geolokatsiyani qo\'llab-quvvatlamaydi');
        return;
    }
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            placeMarker(pos.coords.latitude, pos.coords.longitude);
            showWeather(pos.coords.latitude.toFixed(4), pos.coords.longitude.toFixed(4));
        },
        () => alert('Joylashuv aniqlanmadi'),
        { enableHighAccuracy: true }
    );
});

let searchTimer = null;
searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = searchInput.value.trim();
    if (q.length < 2) {
        searchResults.classList.remove('show');
        return;
    }
    searchTimer = setTimeout(async () => {
        try {
            const resp = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
            const cities = await resp.json();
            if (cities.error) throw new Error(cities.error);
            searchResults.innerHTML = cities.map((c) =>
                `<div class="result-item" data-lat="${c.lat}" data-lon="${c.lon}">` +
                `${c.name}, ${c.country}</div>`
            ).join('');
            searchResults.classList.add('show');
            searchResults.querySelectorAll('.result-item').forEach((el) => {
                el.addEventListener('click', () => {
                    placeMarker(parseFloat(el.dataset.lat), parseFloat(el.dataset.lon), el.textContent);
                    showWeather(el.dataset.lat, el.dataset.lon);
                    searchInput.value = '';
                    searchResults.classList.remove('show');
                });
            });
        } catch (e) {
            searchResults.innerHTML = `<div class="result-item">Xato: ${e.message}</div>`;
            searchResults.classList.add('show');
        }
    }, 400);
});

document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-box')) {
        searchResults.classList.remove('show');
    }
});

map.on('click', (e) => {
    showWeather(e.latlng.lat.toFixed(4), e.latlng.lng.toFixed(4));
});

loadRadar();
