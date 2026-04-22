import streamlit as st
import math
import requests
from datetime import datetime, timezone
from streamlit_geolocation import streamlit_geolocation

# =========================================================
# 1. CONFIGURATION & STYLE
# =========================================================
st.set_page_config(page_title="Disney Master Guide", page_icon="🏰", layout="wide")
st.markdown("""<style> .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; } </style>""", unsafe_allow_html=True)

st.title("🏰 Guide Magique - Ultimate Edition")
st.markdown("*Météo, Combos Famille, Single Rider et Spectacles : Tout est là.*")

# =========================================================
# 2. BASE DE DONNÉES (Catégorisation stricte)
# =========================================================
DB = {
    # --- RIDES FAMILIAUX ---
    "Pirates of the Caribbean": {"type": "famille", "indoor": True, "coords": (48.8736, 2.7751), "imm": 10, "pop": 9},
    "small world": {"type": "famille", "indoor": True, "coords": (48.8745, 2.7768), "imm": 8, "pop": 8},
    "Phantom Manor": {"type": "famille", "indoor": True, "coords": (48.8702, 2.7796), "imm": 9, "pop": 8},
    "Peter Pan's Flight": {"type": "famille", "indoor": True, "coords": (48.8732, 2.7766), "imm": 9, "pop": 10},
    "Big Thunder Mountain": {"type": "famille", "indoor": False, "coords": (48.8715, 2.7777), "imm": 8, "pop": 10},
    "Buzz Lightyear": {"type": "famille", "indoor": True, "coords": (48.8741, 2.7781), "imm": 7, "pop": 8},
    "Ratatouille": {"type": "famille", "indoor": True, "coords": (48.8681, 2.7794), "imm": 10, "pop": 9},
    
    # --- SENSATIONS & SINGLE RIDER ---
    "Hyperspace Mountain": {"type": "sensation", "indoor": True, "coords": (48.8735, 2.7788), "imm": 8, "pop": 9},
    "Indiana Jones": {"type": "sensation", "indoor": False, "coords": (48.8722, 2.7738), "imm": 8, "pop": 8},
    "Crush's Coaster": {"type": "sensation", "indoor": True, "coords": (48.8682, 2.7806), "imm": 9, "pop": 10},
    "Avengers Assemble": {"type": "sensation", "indoor": True, "coords": (48.8686, 2.7816), "imm": 8, "pop": 8},
    "Tower of Terror": {"type": "sensation", "indoor": True, "coords": (48.8675, 2.7790), "imm": 10, "pop": 9},
    "Spider-Man W.E.B.": {"type": "sensation", "indoor": True, "coords": (48.8684, 2.7820), "imm": 9, "pop": 10},

    # --- SECONDAIRES & BEBE ---
    "Coin Bébé (Main Street)": {"type": "walk", "indoor": True, "coords": (48.8718, 2.7775), "imm": 10, "pop": 5},
    "Baby Care Center (Studios)": {"type": "walk", "indoor": True, "coords": (48.8675, 2.7805), "imm": 10, "pop": 5},
    "Tanière du Dragon": {"type": "walk", "indoor": True, "coords": (48.8730, 2.7760), "imm": 9, "pop": 5},
    "Nautilus": {"type": "walk", "indoor": True, "coords": (48.8738, 2.7780), "imm": 8, "pop": 5},

    # --- SPECTACLES ---
    "Mickey and the Magician": {"type": "show"},
    "Lion King": {"type": "show"},
    "Disney Stars on Parade": {"type": "show"},
    "Disney Illuminations": {"type": "show"},
    "Stitch Live": {"type": "show"}
}

# =========================================================
# 3. APIS : METEO ET DISNEY (Robustesse Max)
# =========================================================
@st.cache_data(ttl=600)
def get_weather():
    url = "https://api.open-meteo.com/v1/forecast?latitude=48.87&longitude=2.77&hourly=precipitation_probability&forecast_days=1"
    try:
        res = requests.get(url, timeout=5).json()
        return res['hourly']['precipitation_probability'][datetime.now().hour]
    except: return 0

@st.cache_data(ttl=180)
def get_disney_data():
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        data = requests.get(url, timeout=10).json()
        result = {"famille": [], "sensation": [], "walk": [], "show": []}
        
        for item in data.get("liveData", []):
            name = item.get("name", "")
            status = item.get("status", "CLOSED")
            
            # Recherche dans notre Base de Données
            match = next((k for k in DB.keys() if k.lower() in name.lower()), None)
            if not match or status != "OPERATING":
                continue
                
            cat = DB[match]["type"]

            # Extraction spécifique pour les spectacles
            if cat == "show":
                show_info = {"nom": match, "time": "Aujourd'hui (Voir App officielle)"}
                # Tentative sécurisée de lire l'horaire
                try:
                    for s in item.get("schedule", []):
                        start_time = datetime.fromisoformat(s['startTime'].replace('Z', '+00:00'))
                        if start_time > datetime.now(timezone.utc):
                            # Convertir en heure locale lisible (HH:MM)
                            show_info["time"] = f"Prochain à {start_time.strftime('%H:%M')}"
                            break
                except: pass # Si le calcul plante, on garde le texte par défaut
                
                result["show"].append(show_info)
                continue

            # Extraction pour les manèges (File normale et Single Rider)
            queue = item.get("queue") or {}
            wait_norm = (queue.get("STANDBY") or {}).get("waitTime", 0)
            wait_sing = (queue.get("SINGLE_RIDER") or {}).get("waitTime", None)
            
            result[cat].append({
                "nom": match, "wait": wait_norm, "single": wait_sing, **DB[match]
            })
            
        return result
    except Exception as e: 
        st.error(f"Impossible de joindre les serveurs Disney. ({e})")
        return {"famille": [], "sensation": [], "walk": [], "show": []}

# =========================================================
# 4. GÉOLOCALISATION & MÉTÉO
# =========================================================
st.sidebar.header("📍 GPS & Météo")
prob_pluie = get_weather()
st.sidebar.metric("Risque de pluie", f"{prob_pluie}%")

geo = streamlit_geolocation()
u_coords = (geo['latitude'], geo['longitude']) if geo and geo.get('latitude') else (48.871, 2.776)
vitesse = 1.6 if st.sidebar.toggle("Mode Poussette", value=True) else 1.0

if st.sidebar.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

data = get_disney_data()

# =========================================================
# 5. ALGORITHME ET SCORING
# =========================================================
def calc_walk(c1, c2):
    return max(1, int(math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2) * 2200 * vitesse))

# Calcul pour la Famille
for r in data["famille"]:
    r['walk'] = calc_walk(u_coords, r['coords'])
    rain_penalty = 0.3 if (prob_pluie > 40 and not r['indoor']) else 1.0
    r['score'] = ((r['imm'] * r['pop']) / (r['wait'] + r['walk'] + 1)) * rain_penalty
data["famille"].sort(key=lambda x: x['score'], reverse=True)

# Calcul pour les Sensations (Trié par distance de marche pour faire vite)
for s in data["sensation"]:
    s['walk'] = calc_walk(u_coords, s['coords'])
data["sensation"].sort(key=lambda x: x['walk'])

# Calcul pour les Walkthrough / Baby Care
for w in data["walk"]:
    w['walk'] = calc_walk(u_coords, w['coords'])
data["walk"].sort(key=lambda x: x['walk'])

# =========================================================
# 6. AFFICHAGE 3 COLONNES
# =========================================================
c1, c2, c3 = st.columns([1.5, 1, 1])

with c1:
    st.header("🎡 Famille & Sensations")
    
    if data["famille"]:
        best = data["famille"][0]
        st.success(f"**TOP : {best['nom']}**\n\n⏳ {best['wait']} min | 🚶 {best['walk']} min")
        with st.expander("Toutes les attractions familiales"):
            for r in data["famille"][1:]:
                st.write(f"**{r['nom']}** ({r['wait']} min)")
    else: st.warning("Aucun manège familial.")

    st.divider()
    
    # LE RETOUR DU SINGLE RIDER !
    st.subheader("🎢 Relais Parent (Single Rider)")
    if data["sensation"]:
        for t in data["sensation"]:
            sing_txt = f"{t['single']} min" if t['single'] is not None else "Fermée"
            st.markdown(f"""
            <div style="background:#343a40; color:white; padding:10px; border-radius:5px; margin-bottom:5px;">
                <p style="margin:0; font-weight:bold;">{t['nom']}</p>
                <p style="margin:0; font-size:14px; color:#adb5bd;">
                    👤 Single : <b>{sing_txt}</b> (File normale: {t['wait']} min) | 🚶 à {t['walk']} min
                </p>
            </div>
            """, unsafe_allow_html=True)
    else: st.write("Aucune sensation forte détectée.")

with c2:
    st.header("🍼 Pauses & Découverte")
    if data["walk"]:
        for w in data["walk"]:
            bg = "#ffebeb" if "Bébé" in w['nom'] or "Baby" in w['nom'] else "#f0f2f6"
            st.markdown(f"""<div style="background:{bg}; padding:10px; border-radius:5px; margin-bottom:5px; border-left:5px solid #6c757d;">
                <p style="margin:0; font-weight:bold; color:black;">{w['nom']}</p>
                <p style="margin:0; font-size:12px; color:grey;">🚶 à {w['walk']} min</p></div>""", unsafe_allow_html=True)
    else: st.write("Aucun lieu à proximité.")

with c3:
    st.header("🎭 Spectacles")
    if data["show"]:
        for s in data["show"]:
            st.markdown(f"""<div style="background:#e8f4f8; padding:10px; border-radius:5px; margin-bottom:5px; border-left:5px solid #17a2b8;">
                <p style="margin:0; font-weight:bold; color:black;">{s['nom']}</p>
                <p style="margin:0; font-size:13px; color:#055160;">{s['time']}</p></div>""", unsafe_allow_html=True)
    else: st.info("Aucun spectacle répertorié pour le moment.")
