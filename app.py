import streamlit as st
import math
import requests
from datetime import datetime, timezone
from streamlit_geolocation import streamlit_geolocation

# =========================================================
# 1. CONFIGURATION & CSS PERSONNALISÉ (Le grand lifting !)
# =========================================================
st.set_page_config(page_title="Disney Premium", page_icon="🏰", layout="centered")

# Injection de CSS pour créer des "Cartes" façon application mobile native
st.markdown("""
<style>
    /* Style global des cartes */
    .d-card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05), 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 16px;
        border-left: 6px solid #e5e7eb;
        transition: transform 0.2s ease;
    }
    /* Couleurs de bordure selon le statut */
    .d-card.green { border-left-color: #10b981; }
    .d-card.orange { border-left-color: #f59e0b; }
    .d-card.red { border-left-color: #ef4444; }
    .d-card.dark { border-left-color: #374151; background-color: #f8fafc; }
    .d-card.blue { border-left-color: #3b82f6; background-color: #eff6ff; }
    .d-card.pink { border-left-color: #ec4899; background-color: #fdf2f8; }
    
    /* Textes */
    .d-title { margin: 0 0 8px 0; color: #1f2937; font-size: 18px; font-weight: 700; }
    .d-text { margin: 4px 0; color: #4b5563; font-size: 14px; display: flex; align-items: center; }
    
    /* Petits badges ronds */
    .d-badge { 
        display: inline-block; padding: 2px 8px; border-radius: 12px; 
        font-size: 11px; font-weight: bold; margin-left: 8px;
        background: #f1f5f9; color: #475569;
    }
    .badge-studios { background: #e0e7ff; color: #4338ca; }
    .badge-parc { background: #dcfce7; color: #15803d; }
</style>
""", unsafe_allow_html=True)

st.title("🏰 Guide VIP")
st.markdown("*Optimisé pour la navigation mobile.*")

# =========================================================
# 2. BASE DE DONNÉES 
# =========================================================
DB = {
    # Famille
    "Pirates of the Caribbean": {"type": "famille", "indoor": True, "coords": (48.8736, 2.7751), "imm": 10, "pop": 9, "parc": "Parc Disneyland"},
    "small world": {"type": "famille", "indoor": True, "coords": (48.8745, 2.7768), "imm": 8, "pop": 8, "parc": "Parc Disneyland"},
    "Phantom Manor": {"type": "famille", "indoor": True, "coords": (48.8702, 2.7796), "imm": 9, "pop": 8, "parc": "Parc Disneyland"},
    "Peter Pan's Flight": {"type": "famille", "indoor": True, "coords": (48.8732, 2.7766), "imm": 9, "pop": 10, "parc": "Parc Disneyland"},
    "Big Thunder Mountain": {"type": "famille", "indoor": False, "coords": (48.8715, 2.7777), "imm": 8, "pop": 10, "parc": "Parc Disneyland"},
    "Buzz Lightyear": {"type": "famille", "indoor": True, "coords": (48.8741, 2.7781), "imm": 7, "pop": 8, "parc": "Parc Disneyland"},
    "Ratatouille": {"type": "famille", "indoor": True, "coords": (48.8681, 2.7794), "imm": 10, "pop": 9, "parc": "Studios"},
    
    # Sensations
    "Hyperspace Mountain": {"type": "sensation", "indoor": True, "coords": (48.8735, 2.7788), "imm": 8, "pop": 9, "parc": "Parc Disneyland"},
    "Indiana Jones": {"type": "sensation", "indoor": False, "coords": (48.8722, 2.7738), "imm": 8, "pop": 8, "parc": "Parc Disneyland"},
    "Crush's Coaster": {"type": "sensation", "indoor": True, "coords": (48.8682, 2.7806), "imm": 9, "pop": 10, "parc": "Studios"},
    "Avengers Assemble": {"type": "sensation", "indoor": True, "coords": (48.8686, 2.7816), "imm": 8, "pop": 8, "parc": "Studios"},
    "Tower of Terror": {"type": "sensation", "indoor": True, "coords": (48.8675, 2.7790), "imm": 10, "pop": 9, "parc": "Studios"},
    "Spider-Man W.E.B.": {"type": "sensation", "indoor": True, "coords": (48.8684, 2.7820), "imm": 9, "pop": 10, "parc": "Studios"},

    # Pauses & Bébés
    "Baby Care (Main Street)": {"type": "walk", "indoor": True, "coords": (48.8718, 2.7775), "imm": 10, "pop": 5, "parc": "Parc Disneyland"},
    "Baby Care (Studios)": {"type": "walk", "indoor": True, "coords": (48.8675, 2.7805), "imm": 10, "pop": 5, "parc": "Studios"},
    "Tanière du Dragon": {"type": "walk", "indoor": True, "coords": (48.8730, 2.7760), "imm": 9, "pop": 5, "parc": "Parc Disneyland"},
    "Nautilus": {"type": "walk", "indoor": True, "coords": (48.8738, 2.7780), "imm": 8, "pop": 5, "parc": "Parc Disneyland"},

    # Spectacles
    "Mickey and the Magician": {"type": "show"},
    "Lion King": {"type": "show"},
    "Disney Stars on Parade": {"type": "show"},
    "Disney Illuminations": {"type": "show"}
}

# =========================================================
# 3. APIS 
# =========================================================
@st.cache_data(ttl=600)
def get_weather():
    try:
        res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=48.87&longitude=2.77&hourly=precipitation_probability&forecast_days=1", timeout=5).json()
        return res['hourly']['precipitation_probability'][datetime.now().hour]
    except: return 0

@st.cache_data(ttl=180)
def get_disney_data():
    try:
        data = requests.get("https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live", timeout=10).json()
        result = {"famille": [], "sensation": [], "walk": [], "show": []}
        
        for item in data.get("liveData", []):
            name, status = item.get("name", ""), item.get("status", "CLOSED")
            match = next((k for k in DB.keys() if k.lower() in name.lower()), None)
            
            if not match or status != "OPERATING": continue
            cat = DB[match]["type"]

            if cat == "show":
                t = "Aujourd'hui"
                try:
                    for s in item.get("schedule", []):
                        start = datetime.fromisoformat(s['startTime'].replace('Z', '+00:00'))
                        if start > datetime.now(timezone.utc):
                            t = start.strftime('%H:%M')
                            break
                except: pass
                result["show"].append({"nom": match, "time": t})
                continue

            q = item.get("queue") or {}
            result[cat].append({
                "nom": match, "wait": (q.get("STANDBY") or {}).get("waitTime", 0),
                "single": (q.get("SINGLE_RIDER") or {}).get("waitTime", None),
                **DB[match]
            })
        return result
    except: return {"famille": [], "sensation": [], "walk": [], "show": []}

# =========================================================
# 4. GÉOLOCALISATION ET BARRE LATÉRALE
# =========================================================
with st.sidebar:
    st.header("📍 Ma Position")
    geo = streamlit_geolocation()
    u_coords = (geo['latitude'], geo['longitude']) if geo and geo.get('latitude') else (48.871, 2.776)
    
    prob_pluie = get_weather()
    st.metric("🌧️ Risque de pluie", f"{prob_pluie}%")
    
    st.header("⚙️ Profil Famille")
    vitesse = 1.6 if st.toggle("🍼 Avec Poussette", value=True) else 1.0
    
    if st.button("🔄 Forcer l'actualisation", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

data = get_disney_data()

# =========================================================
# 5. ALGORITHME DE SCORING
# =========================================================
def calc_walk(c1, c2): return max(1, int(math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2) * 2200 * vitesse))

for r in data["famille"]:
    r['walk'] = calc_walk(u_coords, r['coords'])
    pen = 0.3 if (prob_pluie > 40 and not r['indoor']) else 1.0
    r['score'] = ((r['imm'] * r['pop']) / (r['wait'] + r['walk'] + 1)) * pen
data["famille"].sort(key=lambda x: x['score'], reverse=True)

for s in data["sensation"]: s['walk'] = calc_walk(u_coords, s['coords'])
data["sensation"].sort(key=lambda x: x['walk'])

for w in data["walk"]: w['walk'] = calc_walk(u_coords, w['coords'])
data["walk"].sort(key=lambda x: x['walk'])

# =========================================================
# 6. AFFICHAGE MOBILE-FIRST (ONGLETS)
# =========================================================
# Création de 3 onglets (parfait pour scroller sur téléphone)
tab1, tab2, tab3 = st.tabs(["🎡 Manèges", "🍼 Pauses", "🎭 Spectacles"])

def get_badge(parc):
    return "badge-studios" if "Studios" in parc else "badge-parc"

with tab1:
    if data["famille"]:
        best = data["famille"][0]
        st.markdown("### 🏆 Recommandation N°1")
        
        # Carte du meilleur choix
        st.markdown(f"""
        <div class="d-card green">
            <h3 class="d-title">{best['nom']} <span class="d-badge {get_badge(best['parc'])}">{best['parc']}</span></h3>
            <div class="d-text">⏳ <b>Attente :</b>&nbsp;{best['wait']} min</div>
            <div class="d-text">🚶 <b>Marche :</b>&nbsp;{best['walk']} min depuis votre position</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu déroulant pour le reste
        with st.expander("Voir les autres options familiales"):
            for r in data["famille"][1:]:
                color = "orange" if r['wait'] > 30 else "green"
                if r['wait'] > 60: color = "red"
                st.markdown(f"""
                <div class="d-card {color}" style="padding:10px;">
                    <div style="font-weight:bold; color:#1f2937;">{r['nom']}</div>
                    <div style="font-size:13px; color:#4b5563;">⏳ {r['wait']} min | 🚶 {r['walk']} min</div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("Aucun manège familial disponible.")

    st.markdown("### 🎢 Relais Parent (Single Rider)")
    for t in data["sensation"]:
        sing_txt = f"{t['single']} min" if t['single'] is not None else "Fermée"
        st.markdown(f"""
        <div class="d-card dark">
            <h3 class="d-title" style="color:#f8fafc; font-size:16px;">⚡ {t['nom']}</h3>
            <div class="d-text" style="color:#cbd5e1;">👤 File Solo : <b>{sing_txt}</b></div>
            <div class="d-text" style="color:#94a3b8; font-size:12px;">File classique : {t['wait']} min | 🚶 à {t['walk']} min</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 🍼 Coins Bébés & Découverte")
    for w in data["walk"]:
        style = "pink" if "Baby" in w['nom'] or "Bébé" in w['nom'] else "blue"
        st.markdown(f"""
        <div class="d-card {style}">
            <h3 class="d-title" style="font-size:16px;">{w['nom']} <span class="d-badge {get_badge(w['parc'])}">{w['parc']}</span></h3>
            <div class="d-text">🚶 À {w['walk']} min de votre position</div>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### 🎭 Prochains Spectacles")
    if data["show"]:
        for s in sorted(data["show"], key=lambda x: x['time']):
            st.markdown(f"""
            <div class="d-card blue">
                <h3 class="d-title" style="font-size:16px;">{s['nom']}</h3>
                <div class="d-text">🕒 Prochaine séance : <b>{s['time']}</b></div>
            </div>
            """, unsafe_allow_html=True)
    else: st.info("Aucun horaire trouvé pour le moment.")
