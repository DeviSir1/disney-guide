import streamlit as st
import math
import requests
from datetime import datetime, timezone
from streamlit_geolocation import streamlit_geolocation

# =========================================================
# 1. CONFIGURATION & CSS (DARK/LIGHT MODE READY)
# =========================================================
st.set_page_config(page_title="Disney Premium", page_icon="🏰", layout="centered")

st.markdown("""
<style>
    :root {
        --bg-card: #ffffff; --text-main: #1f2937; --text-sub: #4b5563;
        --border-color: #e5e7eb; --bg-badge: #f1f5f9; --text-badge: #475569;
        --bg-blue: #eff6ff; --bg-pink: #fdf2f8; --bg-dark: #f8fafc;
    }
    @media (prefers-color-scheme: dark) {
        :root {
            --bg-card: #262730; --text-main: #f8fafc; --text-sub: #cbd5e1;
            --border-color: #333344; --bg-badge: #334155; --text-badge: #e2e8f0;
            --bg-blue: #1e3a8a30; --bg-pink: #83184330; --bg-dark: #0f172a;
        }
    }
    .d-card {
        background-color: var(--bg-card); border-radius: 12px; padding: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 16px;
        border: 1px solid var(--border-color); border-left: 6px solid var(--border-color);
    }
    .d-card.green { border-left-color: #10b981; }
    .d-card.orange { border-left-color: #f59e0b; }
    .d-card.red { border-left-color: #ef4444; }
    .d-card.dark { border-left-color: #64748b; background-color: var(--bg-dark); }
    .d-card.blue { border-left-color: #3b82f6; background-color: var(--bg-blue); }
    .d-card.pink { border-left-color: #ec4899; background-color: var(--bg-pink); }
    
    .d-title { margin: 0 0 8px 0; color: var(--text-main); font-size: 18px; font-weight: 700; }
    .d-title-small { margin: 0 0 4px 0; color: var(--text-main); font-size: 15px; font-weight: 700; }
    .d-text { margin: 4px 0; color: var(--text-sub); font-size: 14px; }
    
    .d-badge { 
        display: inline-block; padding: 2px 8px; border-radius: 12px; 
        font-size: 11px; font-weight: bold; margin-left: 8px;
        background: var(--bg-badge); color: var(--text-badge);
    }
    .badge-studios { background: #e0e7ff; color: #4338ca; }
    .badge-parc { background: #dcfce7; color: #15803d; }
</style>
""", unsafe_allow_html=True)

st.title("🏰 Guide VIP")

# =========================================================
# 2. BASE DE DONNÉES COMPLÈTE (LE POKÉDEX ENTIER)
# =========================================================
DB = {
    # --- RIDES FAMILIAUX : PARC DISNEYLAND ---
    "Pirates of the Caribbean": {"type": "famille", "indoor": True, "coords": (48.8736, 2.7751), "imm": 10, "pop": 9, "parc": "Parc Disneyland"},
    "small world": {"type": "famille", "indoor": True, "coords": (48.8745, 2.7768), "imm": 8, "pop": 8, "parc": "Parc Disneyland"},
    "Phantom Manor": {"type": "famille", "indoor": True, "coords": (48.8702, 2.7796), "imm": 9, "pop": 8, "parc": "Parc Disneyland"},
    "Peter Pan's Flight": {"type": "famille", "indoor": True, "coords": (48.8732, 2.7766), "imm": 9, "pop": 10, "parc": "Parc Disneyland"},
    "Big Thunder Mountain": {"type": "famille", "indoor": False, "coords": (48.8715, 2.7777), "imm": 8, "pop": 10, "parc": "Parc Disneyland"},
    "Buzz Lightyear": {"type": "famille", "indoor": True, "coords": (48.8741, 2.7781), "imm": 7, "pop": 8, "parc": "Parc Disneyland"},
    "Star Tours": {"type": "famille", "indoor": True, "coords": (48.8745, 2.7775), "imm": 8, "pop": 8, "parc": "Parc Disneyland"},
    "Autopia": {"type": "famille", "indoor": False, "coords": (48.8748, 2.7780), "imm": 5, "pop": 7, "parc": "Parc Disneyland"},
    "Orbitron": {"type": "famille", "indoor": False, "coords": (48.8742, 2.7775), "imm": 5, "pop": 6, "parc": "Parc Disneyland"},
    "Blanche-Neige": {"type": "famille", "indoor": True, "coords": (48.8733, 2.7762), "imm": 7, "pop": 7, "parc": "Parc Disneyland"},
    "Pinocchio": {"type": "famille", "indoor": True, "coords": (48.8734, 2.7760), "imm": 7, "pop": 7, "parc": "Parc Disneyland"},
    "Carrousel de Lancelot": {"type": "famille", "indoor": True, "coords": (48.8736, 2.7764), "imm": 6, "pop": 6, "parc": "Parc Disneyland"},
    "Dumbo": {"type": "famille", "indoor": False, "coords": (48.8738, 2.7766), "imm": 6, "pop": 8, "parc": "Parc Disneyland"},
    "Mad Hatter": {"type": "famille", "indoor": True, "coords": (48.8740, 2.7760), "imm": 6, "pop": 7, "parc": "Parc Disneyland"},
    "Casey Jr.": {"type": "famille", "indoor": False, "coords": (48.8745, 2.7755), "imm": 6, "pop": 6, "parc": "Parc Disneyland"},
    "Pays des Contes": {"type": "famille", "indoor": False, "coords": (48.8748, 2.7752), "imm": 7, "pop": 5, "parc": "Parc Disneyland"},
    "Thunder Mesa Riverboat": {"type": "famille", "indoor": False, "coords": (48.8712, 2.7785), "imm": 8, "pop": 5, "parc": "Parc Disneyland"},
    
    # --- RIDES FAMILIAUX : STUDIOS ---
    "Ratatouille": {"type": "famille", "indoor": True, "coords": (48.8681, 2.7794), "imm": 10, "pop": 9, "parc": "Studios"},
    "Spider-Man W.E.B.": {"type": "famille", "indoor": True, "coords": (48.8684, 2.7820), "imm": 9, "pop": 10, "parc": "Studios"},
    "Slinky Dog": {"type": "famille", "indoor": False, "coords": (48.8685, 2.7812), "imm": 5, "pop": 6, "parc": "Studios"},
    "Cars Quatre Roues": {"type": "famille", "indoor": False, "coords": (48.8680, 2.7815), "imm": 6, "pop": 5, "parc": "Studios"},
    "Cars Road Trip": {"type": "famille", "indoor": False, "coords": (48.8670, 2.7820), "imm": 6, "pop": 5, "parc": "Studios"},
    "Tapis Volants": {"type": "famille", "indoor": False, "coords": (48.8683, 2.7800), "imm": 5, "pop": 5, "parc": "Studios"},
    "Frozen Ever After": {"type": "famille", "indoor": True, "coords": (48.8672, 2.7801), "imm": 10, "pop": 10, "parc": "Studios"},
    
    # --- SENSATIONS (CIBLES SINGLE RIDER) ---
    "Hyperspace Mountain": {"type": "sensation", "indoor": True, "coords": (48.8735, 2.7788), "imm": 8, "pop": 9, "parc": "Parc Disneyland"},
    "Indiana Jones": {"type": "sensation", "indoor": False, "coords": (48.8722, 2.7738), "imm": 8, "pop": 8, "parc": "Parc Disneyland"},
    "Crush's Coaster": {"type": "sensation", "indoor": True, "coords": (48.8682, 2.7806), "imm": 9, "pop": 10, "parc": "Studios"},
    "Avengers Assemble": {"type": "sensation", "indoor": True, "coords": (48.8686, 2.7816), "imm": 8, "pop": 8, "parc": "Studios"},
    "Tower of Terror": {"type": "sensation", "indoor": True, "coords": (48.8675, 2.7790), "imm": 10, "pop": 9, "parc": "Studios"},
    "Toy Soldiers Parachute": {"type": "sensation", "indoor": False, "coords": (48.8682, 2.7810), "imm": 6, "pop": 7, "parc": "Studios"},
    "RC Racer": {"type": "sensation", "indoor": False, "coords": (48.8678, 2.7818), "imm": 6, "pop": 7, "parc": "Studios"},

    # --- WALKTHROUGHS & COINS BÉBÉ ---
    "Coin Bébé (Main Street)": {"type": "walk", "indoor": True, "coords": (48.8718, 2.7775), "imm": 10, "pop": 5, "parc": "Parc Disneyland"},
    "Baby Care Center (Studios)": {"type": "walk", "indoor": True, "coords": (48.8675, 2.7805), "imm": 10, "pop": 5, "parc": "Studios"},
    "Tanière du Dragon": {"type": "walk", "indoor": True, "coords": (48.8730, 2.7760), "imm": 9, "pop": 5, "parc": "Parc Disneyland"},
    "Nautilus": {"type": "walk", "indoor": True, "coords": (48.8738, 2.7780), "imm": 8, "pop": 5, "parc": "Parc Disneyland"},
    "Alice's Curious Labyrinth": {"type": "walk", "indoor": False, "coords": (48.8748, 2.7758), "imm": 7, "pop": 6, "parc": "Parc Disneyland"},
    "Aladdin": {"type": "walk", "indoor": True, "coords": (48.8728, 2.7745), "imm": 7, "pop": 4, "parc": "Parc Disneyland"},
    "Robinson": {"type": "walk", "indoor": False, "coords": (48.8720, 2.7740), "imm": 7, "pop": 5, "parc": "Parc Disneyland"},
    "Adventure Isle": {"type": "walk", "indoor": False, "coords": (48.8725, 2.7735), "imm": 8, "pop": 5, "parc": "Parc Disneyland"},

    # --- SPECTACLES MAJEURS ---
    "Mickey and the Magician": {"type": "show"},
    "Lion King": {"type": "show"},
    "Disney Stars on Parade": {"type": "show"},
    "Disney Illuminations": {"type": "show"},
    "Stitch Live": {"type": "show"},
    "Disney Junior": {"type": "show"},
    "Frozen: A Musical": {"type": "show"},
    "Pixar Musical": {"type": "show"},
    "Electrical Sky Parade": {"type": "show"}
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
tab1, tab2, tab3 = st.tabs(["🎡 Manèges", "🍼 Pauses", "🎭 Spectacles"])

def get_badge(parc): return "badge-studios" if "Studios" in parc else "badge-parc"

with tab1:
    if data["famille"]:
        best = data["famille"][0]
        st.markdown("### 🏆 Recommandation N°1")
        
        st.markdown(f"""
        <div class="d-card green">
            <h3 class="d-title">{best['nom']} <span class="d-badge {get_badge(best['parc'])}">{best['parc']}</span></h3>
            <div class="d-text">⏳ <b>Attente :</b>&nbsp;{best['wait']} min</div>
            <div class="d-text">🚶 <b>Marche :</b>&nbsp;{best['walk']} min depuis votre position</div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("Voir les autres options familiales (Triées par Score)"):
            for r in data["famille"][1:]:
                color = "orange" if r['wait'] > 30 else "green"
                if r['wait'] > 60: color = "red"
                
                # Bonus : Si Spider-Man ou Ratatouille a une file Single Rider, on l'affiche ici !
                single_info = f" | 👤 Solo: {r['single']} min" if r.get('single') is not None else ""
                
                st.markdown(f"""
                <div class="d-card {color}" style="padding:12px;">
                    <h4 class="d-title-small">{r['nom']} <span class="d-badge {get_badge(r['parc'])}">{r['parc']}</span></h4>
                    <div class="d-text">⏳ {r['wait']} min {single_info} | 🚶 {r['walk']} min</div>
                </div>
                """, unsafe_allow_html=True)
    else: st.info("Aucun manège familial disponible.")

    st.markdown("### 🎢 Relais Parent (Single Rider)")
    for t in data["sensation"]:
        sing_txt = f"{t['single']} min" if t['single'] is not None else "Fermée"
        st.markdown(f"""
        <div class="d-card dark">
            <h3 class="d-title">⚡ {t['nom']} <span class="d-badge {get_badge(t['parc'])}">{t['parc']}</span></h3>
            <div class="d-text">👤 File Solo : <b>{sing_txt}</b></div>
            <div class="d-text">👥 File classique : {t['wait']} min | 🚶 à {t['walk']} min</div>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 🍼 Coins Bébés & Découverte")
    for w in data["walk"]:
        style = "pink" if "Baby" in w['nom'] or "Bébé" in w['nom'] else "blue"
        st.markdown(f"""
        <div class="d-card {style}">
            <h3 class="d-title">{w['nom']} <span class="d-badge {get_badge(w['parc'])}">{w['parc']}</span></h3>
            <div class="d-text">🚶 À {w['walk']} min de votre position</div>
        </div>
        """, unsafe_allow_html=True)

with tab3:
    st.markdown("### 🎭 Prochains Spectacles")
    if data["show"]:
        for s in sorted(data["show"], key=lambda x: x['time']):
            st.markdown(f"""
            <div class="d-card blue">
                <h3 class="d-title">{s['nom']}</h3>
                <div class="d-text">🕒 Prochaine séance : <b>{s['time']}</b></div>
            </div>
            """, unsafe_allow_html=True)
    else: st.info("Aucun horaire trouvé pour le moment.")
