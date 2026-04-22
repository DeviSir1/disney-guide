import streamlit as st
import math
import requests
from streamlit_geolocation import streamlit_geolocation

# ---------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Disney Family Guide", page_icon="✨", layout="wide")

st.title("✨ Mon Guide Magique - Disneyland")
st.markdown("*Optimisation Totale : Famille, Spectacles et Relais Parent.*")

# ---------------------------------------------------------
# 2. BASE DE DONNÉES 
# ---------------------------------------------------------
attractions_statiques = {
    "Pirates of the Caribbean": {"coords": (48.8736, 2.7751), "immersion": 10, "pop": 9, "parc": "Disneyland", "type": "famille"},
    "small world": {"coords": (48.8745, 2.7768), "immersion": 8, "pop": 8, "parc": "Disneyland", "type": "famille"},
    "Phantom Manor": {"coords": (48.8702, 2.7796), "immersion": 9, "pop": 8, "parc": "Disneyland", "type": "famille"},
    "Peter Pan's Flight": {"coords": (48.8732, 2.7766), "immersion": 9, "pop": 10, "parc": "Disneyland", "type": "famille"},
    "Big Thunder Mountain": {"coords": (48.8715, 2.7777), "immersion": 8, "pop": 10, "parc": "Disneyland", "type": "famille"},
    "Buzz Lightyear": {"coords": (48.8741, 2.7781), "immersion": 7, "pop": 8, "parc": "Disneyland", "type": "famille"},
    "Star Tours": {"coords": (48.8745, 2.7775), "immersion": 8, "pop": 8, "parc": "Disneyland", "type": "famille"},
    "Ratatouille": {"coords": (48.8681, 2.7794), "immersion": 10, "pop": 9, "parc": "Studios", "type": "famille"},
    
    "Hyperspace Mountain": {"coords": (48.8735, 2.7788), "immersion": 8, "pop": 9, "parc": "Disneyland", "type": "sensation"},
    "Indiana Jones": {"coords": (48.8722, 2.7738), "immersion": 8, "pop": 8, "parc": "Disneyland", "type": "sensation"},
    "Crush's Coaster": {"coords": (48.8682, 2.7806), "immersion": 9, "pop": 10, "parc": "Studios", "type": "sensation"},
    "Avengers Assemble": {"coords": (48.8686, 2.7816), "immersion": 8, "pop": 8, "parc": "Studios", "type": "sensation"},
    "Spider-Man": {"coords": (48.8684, 2.7820), "immersion": 9, "pop": 10, "parc": "Studios", "type": "sensation"},
    "Tower of Terror": {"coords": (48.8675, 2.7790), "immersion": 10, "pop": 9, "parc": "Studios", "type": "sensation"},
}

# ---------------------------------------------------------
# 3. RÉCUPÉRATION DES DONNÉES (Anti-Crash)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def get_live_data(user_coords):
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        data = requests.get(url, timeout=10).json()
        live_attractions = []
        live_spectacles = []
        
        for item in data.get("liveData", []):
            name = item.get("name", "")
            if item.get("status") != "OPERATING":
                continue

            specs = None
            for attr_name, s in attractions_statiques.items():
                if attr_name.lower() in name.lower():
                    specs = s
                    break
            
            if not specs:
                mots_spectacles = ["show", "spectacle", "parade", "meet", "rencontre", "theater", "character"]
                if any(mot in name.lower() for mot in mots_spectacles):
                    specs = {"type": "spectacle"}
                else:
                    specs = {"type": "famille", "coords": user_coords, "immersion": 5, "pop": 5, "parc": "Inconnu"}

            # ---- CORRECTION DU BUG ICI : Lecture sécurisée des files d'attente ----
            queue_data = item.get("queue") or {} # Si queue est 'null', ça devient un dictionnaire vide
            standby = queue_data.get("STANDBY") or {}
            single = queue_data.get("SINGLE_RIDER") or {}
            
            wait_standby = standby.get("waitTime", 0)
            wait_single = single.get("waitTime", None)
            
            format_item = {
                "nom": name, 
                "wait": wait_standby if wait_standby is not None else 0,
                "single_wait": wait_single,
                "coords": specs.get("coords", user_coords),
                "immersion": specs.get("immersion", 5),
                "pop": specs.get("pop", 5),
                "parc": specs.get("parc", "Parc"),
                "type": specs.get("type", "famille")
            }

            if format_item["type"] == "spectacle":
                live_spectacles.append(format_item)
            else:
                live_attractions.append(format_item)
                
        return live_attractions, live_spectacles
    except Exception as e: 
        st.error(f"Erreur de réseau. Veuillez réessayer. ({e})")
        return [], []

# ---------------------------------------------------------
# 4. GPS & RÉGLAGES
# ---------------------------------------------------------
st.sidebar.header("📍 Ma Position")
geo_data = streamlit_geolocation()
if geo_data and geo_data.get('latitude'):
    user_coords = (geo_data['latitude'], geo_data['longitude'])
    st.sidebar.success("✅ GPS Connecté")
else:
    st.sidebar.warning("GPS en attente... (Défaut : Entrée)")
    user_coords = (48.871, 2.776)

attractions, spectacles = get_live_data(user_coords)

st.sidebar.header("⚙️ Profil Famille")
coeff_vitesse = 1.6 if st.sidebar.toggle("Rythme Poussette", value=True) else 1.0
mode_single_rider = st.sidebar.toggle("🎢 Chercher des Single Riders", value=True)

if st.sidebar.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# 5. ALGORITHME DE CALCUL
# ---------------------------------------------------------
def get_travel_time(c1, c2, c):
    dist = math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
    return max(1, int(dist * 2200 * c))

attractions_famille = []
attractions_thrill = []

for a in attractions:
    a['walk'] = get_travel_time(user_coords, a['coords'], coeff_vitesse)
    total_time = a['wait'] + a['walk']
    a['score'] = (a['immersion'] * a['pop']) / (total_time + 1)
    
    # Couleurs communes
    if a['score'] > 3.0: a['status'], a['color'], a['border'] = "🟢", "#d4edda", "green"
    elif a['score'] > 1.5: a['status'], a['color'], a['border'] = "🟡", "#fff3cd", "orange"
    else: a['status'], a['color'], a['border'] = "🔴", "#f8d7da", "red"
    
    if a['type'] == "famille":
        attractions_famille.append(a)
    elif a['type'] == "sensation":
        attractions_thrill.append(a) # On ne les perd plus jamais !

attractions_famille.sort(key=lambda x: x["score"], reverse=True)

# ---------------------------------------------------------
# 6. AFFICHAGE EN COLONNES
# ---------------------------------------------------------
col_gauche, col_droite = st.columns([2, 1])

with col_gauche:
    st.header("🎡 Optimisation des Manèges")
    if not attractions_famille:
        st.warning("Aucune attraction n'est disponible ou le parc est fermé.")
    else:
        best = attractions_famille[0]
        combos_possibles = [
            r for r in attractions_famille 
            if r['nom'] != best['nom'] and r['parc'] == best['parc'] and r['wait'] <= 40           
        ]
        combos_possibles.sort(key=lambda x: get_travel_time(best['coords'], x['coords'], coeff_vitesse))
        combo = combos_possibles[0] if combos_possibles else None

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown(f"""
            <div style="background:{best['color']}; border-left:5px solid {best['border']}; padding:15px; border-radius:10px; height:180px;">
                <h4 style="margin:0; color:black;">1. {best['nom']}</h4>
                <p style="margin:10px 0; color:#333;">⏳ Attente : <b>{best['wait']} min</b><br>🚶 Marche : <b>{best['walk']} min</b></p>
                <p style="font-size:12px; color:grey;">Parc : {best['parc']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_c2:
            if combo:
                walk_to_next = get_travel_time(best['coords'], combo['coords'], coeff_vitesse)
                st.markdown(f"""
                <div style="background:{combo['color']}; border-left:5px solid {combo['border']}; padding:15px; border-radius:10px; height:180px;">
                    <h4 style="margin:0; color:black;">2. {combo['nom']}</h4>
                    <p style="margin:10px 0; color:#333;">⏳ Attente : <b>{combo['wait']} min</b><br>🚶 +{walk_to_next} min du premier</p>
                    <p style="font-size:12px; color:grey;">Même zone !</p>
                </div>
                """, unsafe_allow_html=True)

        # --- RELAIS PARENT ---
        if mode_single_rider and attractions_thrill:
            st.divider()
            thrill_proches = [t for t in attractions_thrill if t['parc'] == best['parc'] and t['single_wait'] is not None and t['single_wait'] <= 30]
            thrill_proches.sort(key=lambda x: x['walk'])
            
            if thrill_proches:
                bonus = thrill_proches[0]
                st.markdown(f"""
                <div style="background:#e2e3e5; border-left:5px solid #343a40; padding:15px; border-radius:10px;">
                    <h4 style="margin:0; color:black;">🎢 Relais Parent : {bonus['nom']}</h4>
                    <p style="margin:10px 0; color:#333;">
                        ⏳ File Solo : <b>{bonus['single_wait']} min</b> (Normal: {bonus['wait']} min)<br>
                        🚶 À {bonus['walk']} min. Idéal pendant la sieste de bébé !
                    </p>
                </div>
                """, unsafe_allow_html=True)

        # --- AUTRES OPTIONS FAMILLES ---
        with st.expander("Voir toutes les autres attractions familles ouvertes"):
            for r in attractions_famille[1:]:
                if not combo or r['nom'] != combo['nom']:
                    st.write(f"**{r['status']} {r['nom']}** - Attente: {r['wait']} min")

        # --- TOUTES LES SENSATIONS FORTES ---
        with st.expander("🎢 Voir les attractions à sensations (Classique)"):
            if not attractions_thrill:
                st.write("Aucune attraction à sensations détectée pour le moment.")
            for t in attractions_thrill:
                single_txt = f"{t['single_wait']} min" if t['single_wait'] is not None else "Fermé"
                st.write(f"**{t['nom']}** - Attente Normale: {t['wait']} min | File Solo: {single_txt}")

with col_droite:
    st.header("🎭 Spectacles & Parades")
    st.info("Expériences actuellement ouvertes ou prévues.")
    
    if spectacles:
        for s in spectacles:
            st.markdown(f"""
            <div style="background:#e8f4f8; border-left:5px solid #17a2b8; padding:10px; border-radius:5px; margin-bottom:10px;">
                <p style="margin:0; color:black; font-weight:bold;">{s['nom']}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("Aucun spectacle détecté pour le moment.")
