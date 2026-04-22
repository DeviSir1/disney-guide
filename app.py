import streamlit as st
import math
import requests
from streamlit_geolocation import streamlit_geolocation

# ---------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Disney Family Guide", page_icon="✨", layout="wide")

st.title("✨ Mon Guide Magique - Disneyland")
st.markdown("*Optimisation Triple : Manèges, Parcours Découverte et Spectacles.*")

# ---------------------------------------------------------
# 2. BASE DE DONNÉES (Catégorisation en 3 types)
# ---------------------------------------------------------
attractions_statiques = {
    # --- Manèges Classiques (Famille & Sensation) ---
    "Pirates of the Caribbean": {"coords": (48.8736, 2.7751), "immersion": 10, "pop": 9, "parc": "Disneyland", "type": "ride"},
    "small world": {"coords": (48.8745, 2.7768), "immersion": 8, "pop": 8, "parc": "Disneyland", "type": "ride"},
    "Phantom Manor": {"coords": (48.8702, 2.7796), "immersion": 9, "pop": 8, "parc": "Disneyland", "type": "ride"},
    "Peter Pan's Flight": {"coords": (48.8732, 2.7766), "immersion": 9, "pop": 10, "parc": "Disneyland", "type": "ride"},
    "Big Thunder Mountain": {"coords": (48.8715, 2.7777), "immersion": 8, "pop": 10, "parc": "Disneyland", "type": "ride"},
    "Buzz Lightyear": {"coords": (48.8741, 2.7781), "immersion": 7, "pop": 8, "parc": "Disneyland", "type": "ride"},
    "Ratatouille": {"coords": (48.8681, 2.7794), "immersion": 10, "pop": 9, "parc": "Studios", "type": "ride"},
    "Hyperspace Mountain": {"coords": (48.8735, 2.7788), "immersion": 8, "pop": 9, "parc": "Disneyland", "type": "ride"},
    "Tower of Terror": {"coords": (48.8675, 2.7790), "immersion": 10, "pop": 9, "parc": "Studios", "type": "ride"},

    # --- Attractions Secondaires (Parcours à pied / Walkthrough) ---
    "Tanière du Dragon": {"coords": (48.8730, 2.7760), "immersion": 9, "pop": 5, "parc": "Disneyland", "type": "walkthrough"},
    "Nautilus": {"coords": (48.8738, 2.7780), "immersion": 8, "pop": 5, "parc": "Disneyland", "type": "walkthrough"},
    "Alice's Curious Labyrinth": {"coords": (48.8748, 2.7758), "immersion": 7, "pop": 6, "parc": "Disneyland", "type": "walkthrough"},
    "Passage Enchanté d'Aladdin": {"coords": (48.8728, 2.7745), "immersion": 7, "pop": 4, "parc": "Disneyland", "type": "walkthrough"},
    "Swiss Family Robinson": {"coords": (48.8720, 2.7740), "immersion": 7, "pop": 5, "parc": "Disneyland", "type": "walkthrough"},
    "Fort Comstock": {"coords": (48.8710, 2.7770), "immersion": 6, "pop": 4, "parc": "Disneyland", "type": "walkthrough"},
}

# ---------------------------------------------------------
# 3. RÉCUPÉRATION DES DONNÉES LIVE
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def get_live_data(user_coords):
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        data = requests.get(url, timeout=10).json()
        live_rides, live_walks, live_specs = [], [], []
        
        for item in data.get("liveData", []):
            name = item.get("name", "")
            if item.get("status") != "OPERATING": continue

            specs = next((s for n, s in attractions_statiques.items() if n.lower() in name.lower()), None)
            
            if not specs:
                if any(m in name.lower() for m in ["show", "spectacle", "parade", "meet", "rencontre"]):
                    specs = {"type": "spectacle"}
                else:
                    specs = {"type": "ride", "coords": user_coords, "immersion": 5, "pop": 5, "parc": "Autre"}

            q = item.get("queue") or {}
            format_item = {
                "nom": name, "wait": (q.get("STANDBY") or {}).get("waitTime", 0),
                "single": (q.get("SINGLE_RIDER") or {}).get("waitTime"),
                "coords": specs.get("coords", user_coords), "type": specs.get("type"),
                "immersion": specs.get("immersion", 5), "pop": specs.get("pop", 5), "parc": specs.get("parc")
            }

            if format_item["type"] == "spectacle": live_specs.append(format_item)
            elif format_item["type"] == "walkthrough": live_walks.append(format_item)
            else: live_rides.append(format_item)
        return live_rides, live_walks, live_specs
    except: return [], [], []

# ---------------------------------------------------------
# 4. GPS & CALCULS
# ---------------------------------------------------------
st.sidebar.header("📍 Position")
geo = streamlit_geolocation()
u_coords = (geo['latitude'], geo['longitude']) if geo and geo.get('latitude') else (48.871, 2.776)
coeff = 1.6 if st.sidebar.toggle("Mode Poussette", value=True) else 1.0

rides, walks, specs = get_live_data(u_coords)

def get_walk_time(c1, c2, c):
    d = math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
    return max(1, int(d * 2200 * c))

# Scoring des Rides
for r in rides:
    r['w_time'] = get_walk_time(u_coords, r['coords'], coeff)
    r['score'] = (r['immersion'] * r['pop']) / (r['wait'] + r['w_time'] + 1)
rides.sort(key=lambda x: x["score"], reverse=True)

# Scoring des Walkthroughs (Proximité pure)
for w in walks:
    w['w_time'] = get_walk_time(u_coords, w['coords'], coeff)
walks.sort(key=lambda x: x["w_time"])

# ---------------------------------------------------------
# 6. AFFICHAGE TRIPLE COLONNE
# ---------------------------------------------------------
c1, c2, c3 = st.columns(3)

with c1:
    st.header("🎡 Manèges")
    if rides:
        best = rides[0]
        st.success(f"**TOP : {best['nom']}**\n\n⏳ {best['wait']} min | 🚶 {best['w_time']} min")
        with st.expander("Autres manèges"):
            for r in rides[1:8]:
                st.write(f"**{r['nom']}** ({r['wait']} min)")
    else: st.write("Aucun manège.")

with c2:
    st.header("🐉 Secondaires")
    st.info("Parcours à pied sans attente, idéal pour Samuel et Eliott.")
    if walks:
        for w in walks[:5]:
            st.markdown(f"""
            <div style="background:#f0f2f6; padding:10px; border-radius:5px; margin-bottom:5px; border-left:5px solid #6c757d;">
                <p style="margin:0; font-weight:bold; color:black;">{w['nom']}</p>
                <p style="margin:0; font-size:12px; color:grey;">🚶 à {w['w_time']} min de vous</p>
            </div>
            """, unsafe_allow_html=True)
    else: st.write("Rien à proximité.")

with c3:
    st.header("🎭 Spectacles")
    if specs:
        for s in specs:
            st.markdown(f"""
            <div style="background:#e8f4f8; padding:10px; border-radius:5px; margin-bottom:5px; border-left:5px solid #17a2b8;">
                <p style="margin:0; font-weight:bold; color:black;">{s['nom']}</p>
            </div>
            """, unsafe_allow_html=True)
    else: st.write("Aucun spectacle.")
