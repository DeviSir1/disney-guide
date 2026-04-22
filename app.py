import streamlit as st
import math
import requests
from streamlit_geolocation import streamlit_geolocation

# ---------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="Disney Family Guide", page_icon="✨", layout="centered")

st.title("✨ Mon Guide Magique - Disneyland")
st.markdown("*Optimisation intelligente pour toute la famille (Filtre anti-traversée inclus).*")

# ---------------------------------------------------------
# 2. BASE DE DONNÉES (Avec distinction des Parcs)
# ---------------------------------------------------------
attractions_statiques = {
    "Pirates of the Caribbean": {"coords": (48.8736, 2.7751), "immersion": 10, "pop": 9, "parc": "Disneyland"},
    "small world": {"coords": (48.8745, 2.7768), "immersion": 8, "pop": 8, "parc": "Disneyland"},
    "Phantom Manor": {"coords": (48.8702, 2.7796), "immersion": 9, "pop": 8, "parc": "Disneyland"},
    "Peter Pan's Flight": {"coords": (48.8732, 2.7766), "immersion": 9, "pop": 10, "parc": "Disneyland"},
    "Big Thunder Mountain": {"coords": (48.8715, 2.7777), "immersion": 8, "pop": 10, "parc": "Disneyland"},
    "Buzz Lightyear Laser Blast": {"coords": (48.8741, 2.7781), "immersion": 7, "pop": 8, "parc": "Disneyland"},
    "Ratatouille": {"coords": (48.8681, 2.7794), "immersion": 10, "pop": 9, "parc": "Studios"},
    "Frozen Ever After": {"coords": (48.8672, 2.7801), "immersion": 10, "pop": 10, "parc": "Studios"},
    "Slinky Dog Zigzag Spin": {"coords": (48.8685, 2.7812), "immersion": 6, "pop": 7, "parc": "Studios"}
}

# ---------------------------------------------------------
# 3. RÉCUPÉRATION DES DONNÉES LIVE
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def get_live_data():
    # ID du Resort entier pour avoir les deux parcs
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        live = []
        for item in data.get("liveData", []):
            name = item.get("name", "")
            for attr_name, specs in attractions_statiques.items():
                if attr_name.lower() in name.lower() and item.get("status") == "OPERATING":
                    wait = item.get("queue", {}).get("STANDBY", {}).get("waitTime", 0)
                    live.append({
                        "nom": attr_name,
                        "wait": wait if wait is not None else 0,
                        "coords": specs["coords"],
                        "immersion": specs["immersion"],
                        "pop": specs["pop"],
                        "parc": specs["parc"]
                    })
        return live
    except: return []

# ---------------------------------------------------------
# 4. GPS & RÉGLAGES MARCHE
# ---------------------------------------------------------
st.sidebar.header("📍 Ma Position")
geo_data = streamlit_geolocation()
if geo_data and geo_data.get('latitude'):
    user_coords = (geo_data['latitude'], geo_data['longitude'])
    st.sidebar.success("✅ GPS Connecté")
else:
    st.sidebar.warning("GPS en attente... (Défaut : Entrée du parc)")
    user_coords = (48.871, 2.776)

st.sidebar.header("⚙️ Profil Famille")
mode_poussette = st.sidebar.toggle("Mode Poussette / Jeunes enfants", value=True)
coeff_vitesse = 1.6 if mode_poussette else 1.0

if st.sidebar.button("🔄 Actualiser les données"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# 5. ALGORITHME DE CALCUL
# ---------------------------------------------------------
def get_travel_time(c1, c2, c):
    dist = math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)
    # 2200 est un multiplicateur calibré pour transformer la distance GPS en minutes de marche réelle
    return max(1, int(dist * 2200 * c))

attractions = get_live_data()
recommandations = []

for a in attractions:
    walk = get_travel_time(user_coords, a['coords'], coeff_vitesse)
    total_time = a['wait'] + walk
    
    # Formule du Score de Magie
    score = (a['immersion'] * a['pop']) / (total_time + 1)
    
    if score > 3.0: status, color, border = "🟢", "#d4edda", "green"
    elif score > 1.5: status, color, border = "🟡", "#fff3cd", "orange"
    else: status, color, border = "🔴", "#f8d7da", "red"
        
    recommandations.append({
        **a, "walk": walk, "status": status, "color": color, "border": border, "score": score
    })

recommandations.sort(key=lambda x: x["score"], reverse=True)

# ---------------------------------------------------------
# 6. AFFICHAGE DES COMBOS INTELLIGENTS
# ---------------------------------------------------------
if not recommandations:
    st.warning("Aucune attraction familiale n'est disponible. Vérifiez les horaires d'ouverture.")
else:
    best = recommandations[0]
    
    # LOGIQUE DU COMBO : Même parc UNIQUEMENT + Attente faible
    combos_possibles = [
        r for r in recommandations 
        if r['nom'] != best['nom'] 
        and r['parc'] == best['parc'] # Règle d'or : On ne change pas de parc !
        and r['wait'] <= 40           # Règle d'or : Pas de longue attente après la première
    ]
    # On prend l'attraction la plus proche à pied de la première
    combos_possibles.sort(key=lambda x: get_travel_time(best['coords'], x['coords'], coeff_vitesse))
    combo = combos_possibles[0] if combos_possibles else None

    st.subheader("🌟 Votre Combo Magique")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background:{best['color']}; border-left:5px solid {best['border']}; padding:15px; border-radius:10px; height:180px;">
            <h4 style="margin:0; color:black;">1. {best['nom']}</h4>
            <p style="margin:10px 0; color:#333;">⏳ Attente : <b>{best['wait']} min</b><br>🚶 Marche : <b>{best['walk']} min</b></p>
            <p style="font-size:12px; color:grey;">Parc : {best['parc']}</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        if combo:
            walk_to_next = get_travel_time(best['coords'], combo['coords'], coeff_vitesse)
            st.markdown(f"""
            <div style="background:{combo['color']}; border-left:5px solid {combo['border']}; padding:15px; border-radius:10px; height:180px;">
                <h4 style="margin:0; color:black;">2. {combo['nom']}</h4>
                <p style="margin:10px 0; color:#333;">⏳ Attente : <b>{combo['wait']} min</b><br>🚶 +{walk_to_next} min du premier</p>
                <p style="font-size:12px; color:grey;">Même zone !</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.write("Pas de combo idéal à proximité immédiate.")

    st.divider()
    st.subheader("📋 Autres opportunités dans le parc")
    for r in recommandations[1:6]:
        if not combo or r['nom'] != combo['nom']:
            st.markdown(f"**{r['status']} {r['nom']}** ({r['parc']}) : {r['wait']} min attente | 🚶 {r['walk']} min")
