import streamlit as st
import math
import requests

# ---------------------------------------------------------
# 1. CONFIGURATION DE L'APPLICATION
# ---------------------------------------------------------
st.set_page_config(page_title="Disney Family Guide", page_icon="✨", layout="centered")

st.title("✨ Mon Guide Magique - Disneyland")
st.markdown("*Optimisé pour l'immersion et la famille, avec données en temps réel.*")

# ---------------------------------------------------------
# 2. BASE DE DONNÉES STATIQUES (Nos réglages maison)
# ---------------------------------------------------------
# Utilisation de noms courts pour garantir la correspondance avec l'API
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
@st.cache_data(ttl=300) # Mise en cache de 5 minutes pour ne pas saturer l'API
def get_live_wait_times():
    # ID de l'API ThemeParks.wiki pour le RESORT Disneyland Paris entier (inclut les 2 parcs)
    url = "https://api.themeparks.wiki/v1/entity/e8d0207f-da8a-4048-bec8-117aa946b2c2/live"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        live_attractions = []
        
        for item in data.get("liveData", []):
            name = item.get("name", "")
            
            # On cherche si l'attraction fait partie de notre liste familiale
            for attr_name, specs in attractions_statiques.items():
                if attr_name.lower() in name.lower():
                    status = item.get("status", "CLOSED")
                    
                    if status != "OPERATING":
                        continue
                        
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
        st.error("Impossible de récupérer les temps d'attente actuels. Vérifiez votre connexion.")
        return []

# Récupération des données fusionnées
attractions = get_live_wait_times()

from streamlit_geolocation import streamlit_geolocation

# ---------------------------------------------------------
# 4. INTERFACE UTILISATEUR ET GPS EN DIRECT
# ---------------------------------------------------------
st.sidebar.header("📍 Ma Position")
st.sidebar.markdown("Clique pour activer le GPS de ton téléphone :")

# Le bouton magique qui appelle le GPS du navigateur
geo_data = streamlit_geolocation()

# Logique de récupération des coordonnées
if geo_data and geo_data.get('latitude') is not None:
    user_coords = (geo_data['latitude'], geo_data['longitude'])
    st.sidebar.success("✅ Position GPS verrouillée !")
else:
    st.sidebar.warning("En attente du GPS... Position par défaut : Entrée du parc.")
    user_coords = (48.871, 2.776) # Coordonnées de l'entrée par défaut

st.sidebar.header("⚙️ Préférences")
vitesse_marche = st.sidebar.radio("Rythme de marche :", ("Rapide", "Normal (avec Poussette)"))
coeff_vitesse = 1.5 if vitesse_marche == "Normal (avec Poussette)" else 1.0

# Bouton pour forcer le rafraîchissement
if st.sidebar.button("🔄 Actualiser les temps"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------
# 5. L'ALGORITHME D'OPTIMISATION
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
        status = "🟢"
        color = "#d4edda" 
        border = "green"
        conseil = "Foncez ! Le ratio temps/magie est parfait."
    elif opportunite > 1.5:
        status = "🟡"
        color = "#fff3cd" 
        border = "orange"
        conseil = "Bon choix si vous êtes dans les parages."
    else:
        status = "🔴"
        color = "#f8d7da" 
        border = "red"
        conseil = "Trop d'attente ou trop loin. Revenez plus tard."
        
    recommandations.append({
        "nom": att["nom"],
        "wait": att["wait"],
        "travel": travel_time,
        "status": status,
        "color": color,
        "border": border,
        "conseil": conseil,
        "score": opportunite
    })

recommandations.sort(key=lambda x: x["score"], reverse=True)

# ---------------------------------------------------------
# 6. AFFICHAGE DES RÉSULTATS (Les Cartes)
# ---------------------------------------------------------
if not recommandations:
    st.warning("Aucune attraction familiale n'est actuellement ouverte ou l'API est en cours de mise à jour.")
else:
    st.subheader("💡 Recommandations en direct :")

    for rec in recommandations:
        card_html = f"""
        <div style="background-color: {rec['color']}; border-left: 5px solid {rec['border']}; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
            <h3 style="margin-top: 0; color: black;">{rec['status']} {rec['nom']}</h3>
            <p style="margin: 0; color: #333;">
                ⏳ <b>Attente :</b> {rec['wait']} min | 
                🚶 <b>Trajet estimé :</b> {rec['travel']} min
            </p>
            <p style="margin-top: 10px; font-style: italic; color: #555;">{rec['conseil']}</p>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
