import streamlit as st
import math
import requests
from datetime import datetime
from streamlit_geolocation import streamlit_geolocation

# ---------------------------------------------------------
# 1. CONFIGURATION & STYLE
# ---------------------------------------------------------
st.set_page_config(page_title="Disney Master Guide", page_icon="🏰", layout="wide")
st.markdown("""<style> .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; } </style>""", unsafe_allow_html=True)

st.title("🏰 Guide Magique : Mode Expert")

# ---------------------------------------------------------
# 2. BASE DE DONNÉES ET POINTS D'INTÉRÊT
# ---------------------------------------------------------
DB = {
    # Rides (famille/sensation)
    "Pirates of the Caribbean": {"type": "ride", "indoor": True, "coords": (48.8736, 2.7751), "imm": 10, "pop": 9, "parc": "Disneyland"},
    "small world": {"type": "ride", "indoor": True, "coords": (48.8745, 2.7768), "imm": 8, "pop": 8, "parc": "Disneyland"},
    "Phantom Manor": {"type": "ride", "indoor": True, "coords": (48.8702, 2.7796), "imm": 9, "pop": 8, "parc": "Disneyland"},
    "Peter Pan's Flight": {"type": "ride", "indoor": True, "coords": (48.8732, 2.7766), "imm": 9, "pop": 10, "parc": "Disneyland"},
    "Big Thunder Mountain": {"type": "ride", "indoor": False, "coords": (48.8715, 2.7777), "imm": 8, "pop": 10, "parc": "Disneyland"},
    "Buzz Lightyear": {"type": "ride", "indoor": True, "coords": (48.8741, 2.7781), "imm": 7, "pop": 8, "parc": "Disneyland"},
    "Ratatouille": {"type": "ride", "indoor": True, "coords": (48.8681, 2.7794), "imm": 10, "pop": 9, "parc": "Studios"},
    "Hyperspace Mountain": {"type": "ride", "indoor": True, "coords": (48.8735, 2.7788), "imm": 8, "pop": 9, "parc": "Disneyland"},
    "Crush's Coaster": {"type": "ride", "indoor": True, "coords": (48.8682, 2.7806), "imm": 9, "pop": 10, "parc": "Studios"},
    "Slinky Dog": {"type": "ride", "indoor": False, "coords": (48.8685, 2.7812), "imm": 6, "pop": 7, "parc": "Studios"},

    # Secondaires & Baby Care
    "Coin Bébé (Baby Care)": {"type": "walk", "coords": (48.8718, 2.7775), "imm": 10, "pop": 5, "parc": "Disneyland"},
    "Baby Care Center (Studios)": {"type": "walk", "coords": (48.8675, 2.7805), "imm": 10, "pop": 5, "parc": "Studios"},
    "Tanière du Dragon": {"type": "walk", "coords": (48.8730, 2.7760), "imm": 9, "pop": 5, "parc": "Disneyland"},
    "Nautilus": {"type": "walk", "coords": (48.8738, 2.7780), "imm": 8, "pop": 5, "parc": "Disneyland"},
}

# ---------------------------------------------------------
# 3. APIS : METEO ET DISNEY
# ---------------------------------------------------------
@st.cache_data(ttl=600)
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=48.87&longitude=2.77&hourly=precipitation_probability&forecast_days=1"
    try:
        res = requests.get(url).json()
        current_hour = datetime.now().hour
        prob = res['hourly']['precipitation_probability'][current_hour]
        return prob
    except: return 0

@st.cache_data(ttl=180)
def get_disney_data():
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        data = requests.get(url).json()
        live_rides, live_shows = [], []
        for item in data.get("liveData", []):
            name = item.get("name", "")
            match = next((k for k in DB.keys() if k.lower() in name.lower()), None)
            
            # Gestion des Spectacles (extraction horaires)
            if "show" in name.lower() or "parade" in name.lower() or item.get("entityType") == "SHOW":
                schedule = item.get("schedule", [])
                upcoming = [s for s in schedule if datetime.fromisoformat(s['startTime'].replace('Z', '+00:00')).replace(tzinfo=None) > datetime.now()]
                if upcoming:
                    next_show = datetime.fromisoformat(upcoming[0]['startTime'].replace('Z', '+00:00')).replace(tzinfo=None)
                    live_shows.append({"nom": name, "time": next_show.strftime("%H:%M")})
                continue

            if match and item.get("status") == "OPERATING":
                q = item.get("queue") or {}
                live_rides.append({
                    "nom": match, "wait": (q.get("STANDBY") or {}).get("waitTime", 0),
                    "single": (q.get("SINGLE_RIDER") or {}).get("waitTime"),
                    **DB[match]
                })
        return live_rides, live_shows
    except: return [], []

# ---------------------------------------------------------
# 4. LOGIQUE & CALCULS
# ---------------------------------------------------------
st.sidebar.header("📍 GPS & Météo")
prob_pluie = get_weather()
st.sidebar.metric("Risque de pluie", f"{prob_pluie}%")

geo = streamlit_geolocation()
u_coords = (geo['latitude'], geo['longitude']) if geo and geo.get('latitude') else (48.871, 2.776)
vitesse = 1.6 if st.sidebar.toggle("Mode Poussette", value=True) else 1.0

rides, shows = get_disney_data()

# Algorithme de Scoring
for r in rides:
    dist = math.sqrt((u_coords[0]-r['coords'][0])**2 + (u_coords[1]-r['coords'][1])**2)
    walk_time = max(1, int(dist * 2200 * vitesse))
    
    # FACTEUR PLUIE : On pénalise l'extérieur si proba > 40%
    rain_penalty = 1.0
    if prob_pluie > 40 and not r['indoor']:
        rain_penalty = 0.3 # Score divisé par 3
        
    r['walk'] = walk_time
    r['score'] = ((r['imm'] * r['pop']) / (r['wait'] + walk_time + 1)) * rain_penalty

# Séparation
rides_fam = sorted([r for r in rides if r['type'] == "ride"], key=lambda x: x['score'], reverse=True)
walks = sorted([{"nom": k, **v, "walk": max(1, int(math.sqrt((u_coords[0]-v['coords'][0])**2 + (u_coords[1]-v['coords'][1])**2) * 2200 * vitesse))} 
                for k, v in DB.items() if v['type'] == "walk"], key=lambda x: x['walk'])

# ---------------------------------------------------------
# 5. AFFICHAGE 3 COLONNES
# ---------------------------------------------------------
c1, c2, c3 = st.columns([1.5, 1, 1])

with c1:
    st.header("🎡 Manèges")
    if rides_fam:
        best = rides_fam[0]
        st.success(f"**CONSEIL : {best['nom']}**\n\n⏳ {best['wait']} min | 🚶 {best['walk']} min")
        if best.get('single'): st.info(f"⚡ Single Rider : {best['single']} min")
        with st.expander("Autres manèges optimisés"):
            for r in rides_fam[1:8]:
                st.write(f"**{r['nom']}** ({r['wait']} min)")
    else: st.write("Aucun manège disponible.")

with c2:
    st.header("🍼 Relais & Pause")
    for w in walks:
        bg = "#ffebeb" if "Bébé" in w['nom'] else "#f0f2f6"
        st.markdown(f"""<div style="background:{bg}; padding:10px; border-radius:5px; margin-bottom:5px; border-left:5px solid #6c757d;">
            <p style="margin:0; font-weight:bold; color:black;">{w['nom']}</p>
            <p style="margin:0; font-size:12px; color:grey;">🚶 à {w['walk']} min</p></div>""", unsafe_allow_html=True)

with c3:
    st.header("🎭 Spectacles")
    if shows:
        for s in sorted(shows, key=lambda x: x['time']):
            st.markdown(f"""<div style="background:#e8f4f8; padding:10px; border-radius:5px; margin-bottom:5px; border-left:5px solid #17a2b8;">
                <p style="margin:0; font-weight:bold; color:black;">{s['nom']}</p>
                <p style="margin:0; color:#055160;">🕒 Prochain à <b>{s['time']}</b></p></div>""", unsafe_allow_html=True)
    else: st.write("Pas d'horaires détectés.")
