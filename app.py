import streamlit as st
import math
import requests
from streamlit_geolocation import streamlit_geolocation

# =========================================================
# 1. CONFIGURATION DU PROJET
# =========================================================
st.set_page_config(page_title="Disney Optimizer", page_icon="🏰", layout="wide")

st.title("🏰 Guide Magique - Master Edition")
st.markdown("*Optimisation stricte : Filtre anti-bruit, Combos et Relais Single Rider.*")

# =========================================================
# 2. BASE DE DONNÉES STRICTE (La "Whitelist")
# =========================================================
# Seules les attractions listées ici seront affichées. Fini les fausses données.
# Types : RIDE_FAMILY, RIDE_THRILL, WALKTHROUGH, SHOW
DB = {
    # --- RIDES FAMILIAUX ---
    "Pirates of the Caribbean": {"type": "RIDE_FAMILY", "coords": (48.8736, 2.7751), "immersion": 10, "pop": 9, "parc": "Disneyland"},
    "small world": {"type": "RIDE_FAMILY", "coords": (48.8745, 2.7768), "immersion": 8, "pop": 8, "parc": "Disneyland"},
    "Phantom Manor": {"type": "RIDE_FAMILY", "coords": (48.8702, 2.7796), "immersion": 9, "pop": 8, "parc": "Disneyland"},
    "Peter Pan's Flight": {"type": "RIDE_FAMILY", "coords": (48.8732, 2.7766), "immersion": 9, "pop": 10, "parc": "Disneyland"},
    "Big Thunder Mountain": {"type": "RIDE_FAMILY", "coords": (48.8715, 2.7777), "immersion": 8, "pop": 10, "parc": "Disneyland"},
    "Buzz Lightyear": {"type": "RIDE_FAMILY", "coords": (48.8741, 2.7781), "immersion": 7, "pop": 8, "parc": "Disneyland"},
    "Star Tours": {"type": "RIDE_FAMILY", "coords": (48.8745, 2.7775), "immersion": 8, "pop": 8, "parc": "Disneyland"},
    "Ratatouille": {"type": "RIDE_FAMILY", "coords": (48.8681, 2.7794), "immersion": 10, "pop": 9, "parc": "Studios"},
    "Spider-Man": {"type": "RIDE_FAMILY", "coords": (48.8684, 2.7820), "immersion": 9, "pop": 10, "parc": "Studios"},
    
    # --- RIDES SENSATIONS (Cibles Single Rider) ---
    "Hyperspace Mountain": {"type": "RIDE_THRILL", "coords": (48.8735, 2.7788), "immersion": 8, "pop": 9, "parc": "Disneyland"},
    "Indiana Jones": {"type": "RIDE_THRILL", "coords": (48.8722, 2.7738), "immersion": 8, "pop": 8, "parc": "Disneyland"},
    "Crush's Coaster": {"type": "RIDE_THRILL", "coords": (48.8682, 2.7806), "immersion": 9, "pop": 10, "parc": "Studios"},
    "Avengers Assemble": {"type": "RIDE_THRILL", "coords": (48.8686, 2.7816), "immersion": 8, "pop": 8, "parc": "Studios"},
    "Tower of Terror": {"type": "RIDE_THRILL", "coords": (48.8675, 2.7790), "immersion": 10, "pop": 9, "parc": "Studios"},
    "RC Racer": {"type": "RIDE_THRILL", "coords": (48.8678, 2.7818), "immersion": 6, "pop": 7, "parc": "Studios"},

    # --- WALKTHROUGHS (Parcours découverte sans attente) ---
    "Tanière du Dragon": {"type": "WALKTHROUGH", "coords": (48.8730, 2.7760), "immersion": 9, "pop": 5, "parc": "Disneyland"},
    "Nautilus": {"type": "WALKTHROUGH", "coords": (48.8738, 2.7780), "immersion": 8, "pop": 5, "parc": "Disneyland"},
    "Alice's Curious Labyrinth": {"type": "WALKTHROUGH", "coords": (48.8748, 2.7758), "immersion": 7, "pop": 6, "parc": "Disneyland"},
    "Passage Enchanté d'Aladdin": {"type": "WALKTHROUGH", "coords": (48.8728, 2.7745), "immersion": 7, "pop": 4, "parc": "Disneyland"},
    "Swiss Family Robinson": {"type": "WALKTHROUGH", "coords": (48.8720, 2.7740), "immersion": 7, "pop": 5, "parc": "Disneyland"},
    "Adventure Isle": {"type": "WALKTHROUGH", "coords": (48.8725, 2.7735), "immersion": 8, "pop": 5, "parc": "Disneyland"},

    # --- SPECTACLES MAJEURS ---
    "Mickey and the Magician": {"type": "SHOW"},
    "Lion King": {"type": "SHOW"},
    "Disney Stars on Parade": {"type": "SHOW"},
    "Disney Illuminations": {"type": "SHOW"},
    "Stitch Live": {"type": "SHOW"},
    "Frozen: A Musical Invitation": {"type": "SHOW"}
}

# =========================================================
# 3. MOTEUR DE PARSING API (Robustesse accrue)
# =========================================================
@st.cache_data(ttl=180) # Cache réduit à 3 min pour une meilleure précision
def fetch_and_parse_live_data(user_coords):
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Lève une erreur si HTTP n'est pas 200 OK
        data = response.json()
        
        parsed_data = {"RIDE_FAMILY": [], "RIDE_THRILL": [], "WALKTHROUGH": [], "SHOW": []}
        
        for item in data.get("liveData", []):
            name = item.get("name", "")
            status = item.get("status", "CLOSED")
            
            if status != "OPERATING":
                continue

            # Vérification stricte contre notre Whitelist
            match = next((key for key in DB.keys() if key.lower() in name.lower()), None)
            if not match:
                continue # On ignore tout ce qui n'est pas dans la base de données !

            specs = DB[match]
            item_type = specs["type"]
            
            # Extraction sécurisée des files d'attente
            queue = item.get("queue") or {}
            standby_wait = (queue.get("STANDBY") or {}).get("waitTime", 0)
            single_wait = (queue.get("SINGLE_RIDER") or {}).get("waitTime", None)
            
            parsed_item = {
                "nom": match,
                "wait": standby_wait,
                "single": single_wait,
                "coords": specs.get("coords", user_coords),
                "immersion": specs.get("immersion", 5),
                "pop": specs.get("pop", 5),
                "parc": specs.get("parc", "Disneyland")
            }
            
            parsed_data[item_type].append(parsed_item)
            
        return parsed_data
    except Exception as e:
        st.error(f"Erreur de communication avec les serveurs Disney : {e}")
        return {"RIDE_FAMILY": [], "RIDE_THRILL": [], "WALKTHROUGH": [], "SHOW": []}

# =========================================================
# 4. CONTRÔLES ET GÉOLOCALISATION
# =========================================================
st.sidebar.header("📍 Position")
geo = streamlit_geolocation()
u_coords = (geo['latitude'], geo['longitude']) if geo and geo.get('latitude') else (48.871, 2.776)

st.sidebar.header("⚙️ Réglages")
coeff_marche = 1.6 if st.sidebar.toggle("Rythme Poussette", value=True) else 1.0

if st.sidebar.button("🔄 Forcer l'actualisation"):
    st.cache_data.clear()
    st.rerun()

# Récupération des données structurées
data = fetch_and_parse_live_data(u_coords)

# =========================================================
# 5. ALGORITHMES DE SCORING
# =========================================================
def calculate_walk_time(c1, c2, coeff):
    dist = math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
    return max(1, int(dist * 2200 * coeff))

# Traitement des Rides Familiaux
for r in data["RIDE_FAMILY"]:
    r['walk'] = calculate_walk_time(u_coords, r['coords'], coeff_marche)
    r['score'] = (r['immersion'] * r['pop']) / (r['wait'] + r['walk'] + 1)
data["RIDE_FAMILY"].sort(key=lambda x: x["score"], reverse=True)

# Traitement des Walkthroughs (Triés purement par proximité)
for w in data["WALKTHROUGH"]:
    w['walk'] = calculate_walk_time(u_coords, w['coords'], coeff_marche)
data["WALKTHROUGH"].sort(key=lambda x: x["walk"])

# Traitement des Rides Thrill (Triés par rentabilité de la file Single Rider)
for t in data["RIDE_THRILL"]:
    t['walk'] = calculate_walk_time(u_coords, t['coords'], coeff_marche)
data["RIDE_THRILL"].sort(key=lambda x: x["single"] if x["single"] is not None else 999)

# =========================================================
# 6. INTERFACE UTILISATEUR : LES 3 COLONNES
# =========================================================
col1, col2, col3 = st.columns([1.2, 1, 1])

# --- COLONNE 1 : LES MANÈGES ET RELAIS PARENT ---
with col1:
    st.header("🎡 Manèges Famille")
    if data["RIDE_FAMILY"]:
        best = data["RIDE_FAMILY"][0]
        st.success(f"**TOP 1 : {best['nom']}**\n\n⏳ Attente : **{best['wait']} min** | 🚶 Marche : **{best['walk']} min**")
        
        with st.expander("Voir les autres manèges", expanded=True):
            for r in data["RIDE_FAMILY"][1:]:
                st.write(f"**{r['nom']}** - ⏳ {r['wait']} min | 🚶 {r['walk']} min")
    else:
        st.warning("Aucun manège n'est ouvert actuellement.")

    st.divider()
    
    st.header("🎢 Relais Parent (Single Rider)")
    st.info("Attractions à sensations pour les grands.")
    if data["RIDE_THRILL"]:
        for t in data["RIDE_THRILL"]:
            single_text = f"**{t['single']} min**" if t['single'] is not None else "Fermée"
            st.markdown(f"""
            <div style="background:#343a40; color:white; padding:10px; border-radius:5px; margin-bottom:5px;">
                <p style="margin:0; font-weight:bold;">{t['nom']}</p>
                <p style="margin:0; font-size:14px; color:#adb5bd;">
                    👤 Single Rider : {single_text} <br>
                    👥 File normale : {t['wait']} min | 🚶 à {t['walk']} min
                </p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Aucune donnée Single Rider disponible.")

# --- COLONNE 2 : LES PARCOURS DÉCOUVERTE ---
with col2:
    st.header("🐉 Secondaires")
    st.info("Exploration à pied sans attente, idéal pour laisser marcher un enfant de 4 ans ou faire une pause poussette.")
    if data["WALKTHROUGH"]:
        for w in data["WALKTHROUGH"]:
            st.markdown(f"""
            <div style="background:#f0f2f6; border-left:4px solid #6c757d; padding:10px; border-radius:3px; margin-bottom:8px;">
                <p style="margin:0; font-weight:bold; color:black;">{w['nom']}</p>
                <p style="margin:0; font-size:12px; color:grey;">🚶 à {w['walk']} min de vous</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Aucun parcours détecté.")

# --- COLONNE 3 : LES SPECTACLES ---
with col3:
    st.header("🎭 Spectacles")
    if data["SHOW"]:
        for s in data["SHOW"]:
            st.markdown(f"""
            <div style="background:#e8f4f8; border-left:4px solid #17a2b8; padding:10px; border-radius:3px; margin-bottom:8px;">
                <p style="margin:0; font-weight:bold; color:black;">{s['nom']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Aucun spectacle majeur actuellement.")
