import streamlit as st
import math
import requests
from streamlit_geolocation import streamlit_geolocation

# ---------------------------------------------------------
# 1. CONFIGURATION DE L'APPLICATION
# ---------------------------------------------------------
st.set_page_config(page_title="Disney Family Guide", page_icon="✨", layout="centered")

st.title("✨ Mon Guide Magique - Disneyland")
st.markdown("*Optimisation GPS et enchaînements intelligents.*")

# ---------------------------------------------------------
# 2. BASE DE DONNÉES STATIQUES (Nos réglages maison)
# ---------------------------------------------------------
attractions_statiques = {
    "Pirates of the Caribbean": {"coords": (48.873, 2.775), "immersion": 10, "pop": 9},
    "small world": {"coords": (48.874, 2.776), "immersion": 8, "pop": 8},
    "Phantom Manor": {"coords": (48.870, 2.779), "immersion": 9, "pop": 8},
    "Peter Pan's Flight": {"coords": (48.873, 2.776), "immersion": 9, "pop": 10},
    "Big Thunder Mountain": {"coords": (48.871, 2.777), "immersion": 8, "pop": 10},
    "Buzz Lightyear Laser Blast": {"coords": (48.874, 2.778), "immersion": 7, "pop": 8},
    "Ratatouille": {"coords": (48.868, 2.779), "immersion": 9, "pop": 9}
}

# ---------------------------------------------------------
# 3. CONNEXION À L'API (Temps réel)
# ---------------------------------------------------------
@st.cache_data(ttl=300)
def get_live_wait_times():
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        live_attractions = []
        for item in data.get("liveData", []):
            name = item.get("name", "")
            for attr_name, specs in attractions_statiques.items():
                if attr_name.lower() in name.lower() and item.get("status") == "OPERATING":
                    wait_time = item.get("queue", {}).get("STANDBY", {}).get("waitTime", 0)
                    live_attractions.append({
                        "nom": attr_name,
                        "wait": wait_time if wait_time is not None else 0,
                        "coords": specs["coords"],
                        "immersion": specs["immersion"],
                        "pop": specs["pop"]
                    })
        return live_attractions
    except Exception as e:
        st.error("Impossible de récupérer les temps d'attente actuels.")
        return []

attractions = get_live_wait_times()

# ---------------------------------------------------------
# 4. INTERFACE UTILISATEUR & GPS
# ---------------------------------------------------------
st.sidebar.header("📍 Ma Position")
st.sidebar.markdown("Clique pour activer le GPS :")

geo_data = streamlit_geolocation()

if geo_data and geo_data.get('latitude') is not None:
    user_coords = (geo_data['latitude'], geo_data['longitude'])
    st.sidebar.success("✅ Position GPS verrouillée !")
else:
    st.sidebar.warning("En attente du GPS... (Par défaut: Entrée)")
    user_coords = (48.871, 2.776)

st.sidebar.header("⚙️ Préférences")
# Option simplifiée : toggle poussette
mode_poussette = st.sidebar.toggle("Mode Poussette (trajets plus lents)", value=True)
coeff_vitesse = 1.5 if mode_poussette else 1.0

if st.sidebar.button("🔄 Actualiser les temps"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# 5. ALGORITHME DE COMBOS & SCORES
# ---------------------------------------------------------
def calculate_travel_time(coord1, coord2, coeff):
    dist = math.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)
    minutes = int(dist * 2000 * coeff) 
    return max(1, minutes)

recommandations = []

for att in attractions:
    travel_time = calculate_travel_time(user_coords, att["coords"], coeff_vitesse)
    total_time = att["wait"] + travel_time
    
    opportunite = (att["immersion"] * att["pop"]) / (total_time + 1)
    
    if opportunite > 3.0:
        status, color, border, conseil = "🟢", "#d4edda", "green", "Foncez ! Ratio temps/magie parfait."
    elif opportunite > 1.5:
        status, color, border, conseil = "🟡", "#fff3cd", "orange", "Bon choix."
    else:
        status, color, border, conseil = "🔴", "#f8d7da", "red", "Trop d'attente ou trop loin."
        
    recommandations.append({
        "nom": att["nom"],
        "wait": att["wait"],
        "travel": travel_time,
        "coords": att["coords"],
        "status": status,
        "color": color,
        "border": border,
        "conseil": conseil,
        "score": opportunite
    })

recommandations.sort(key=lambda x: x["score"], reverse=True)

# ---------------------------------------------------------
# 6. AFFICHAGE DES RÉSULTATS
# ---------------------------------------------------------
if not recommandations:
    st.warning("Aucune attraction disponible ou en cours de chargement...")
else:
    best = recommandations[0]
    
    # Recherche du Combo (Attraction la plus proche du Best)
    autres = [r for r in recommandations if r['nom'] != best['nom']]
    autres.sort(key=lambda x: calculate_travel_time(best['coords'], x['coords'], coeff_vitesse))
    combo = autres[0] if autres else None

    st.subheader("🌟 Votre Combo Magique")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div style="background-color: {best['color']}; border-left: 5px solid {best['border']}; padding: 15px; border-radius: 5px; height: 100%;">
            <h4 style="margin-top: 0; color: black;">Étape 1 : {best['nom']}</h4>
            <p style="margin: 0; color: #333;">⏳ Attente : <b>{best['wait']} min</b></p>
            <p style="margin: 0; color: #333;">🚶 Marche : <b>{best['travel']} min</b></p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        if combo:
            walk_next = calculate_travel_time(best['coords'], combo['coords'], coeff_vitesse)
            st.markdown(f"""
            <div style="background-color: {combo['color']}; border-left: 5px solid {combo['border']}; padding: 15px; border-radius: 5px; height: 100%;">
                <h4 style="margin-top: 0; color: black;">Étape 2 : {combo['nom']}</h4>
                <p style="margin: 0; color: #333;">⏳ Attente : <b>{combo['wait']} min</b></p>
                <p style="margin: 0; color: #333;">🚶 Relais : <b>{walk_next} min</b> depuis l'étape 1</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    st.subheader("📋 Autres options")
    
    for rec in recommandations[1:4]: # Affiche les 3 suivants
        if rec['nom'] != combo['nom'] if combo else True:
            card_html = f"""
            <div style="background-color: {rec['color']}; border-left: 5px solid {rec['border']}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                <h4 style="margin-top: 0; margin-bottom: 5px; color: black;">{rec['status']} {rec['nom']}</h4>
                <p style="margin: 0; font-size: 14px; color: #333;">
                    ⏳ {rec['wait']} min | 🚶 {rec['travel']} min
                </p>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
