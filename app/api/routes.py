from fastapi import APIRouter, HTTPException
from app.schemas.models import PromptRequest, PromptResponse, TripRequest, TripGenerateResponse
from app.services.gemini_ai import generate_response
import json
import re
import uuid
from datetime import datetime, timezone

router = APIRouter()

# ==========================================
# ROUTE 1 : Question simple (Chat basique)
# ==========================================
@router.post("/ask", response_model=PromptResponse, tags=["AI Interaction"])
async def ask_gemini(request: PromptRequest):
    """
    Reçoit un prompt libre de la webapp, interroge Gemini et renvoie la réponse brute en texte.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide ou constitué uniquement d'espaces.")
    
    ai_answer = await generate_response(request.message)
    
    return PromptResponse(response=ai_answer)


# ==========================================
# UTILITAIRE : Construction du Prompt Voyage
# ==========================================
def build_trip_prompt(data: TripRequest) -> str:
    """Construit le prompt final à envoyer à Gemini."""
    
    # 1. Gestion des enfants
    if data.preferences.travelWithChildren and data.preferences.children:
        ages = ", ".join([f"{c.age} ans" for c in data.preferences.children])
        children_info = f"Enfants présents : {ages}"
    else:
        children_info = "Pas d'enfants"

    # 2. Objectif du voyage
    if data.tripGoal == "cheapest":
        goal_instruction = "L'objectif est de minimiser le coût total. Choisis les options les moins chères."
    else:
        goal_instruction = "L'objectif est de visiter le maximum d'endroits différents. Sélectionne plusieurs logements dans différentes zones si possible."

    # 3. Calcul de la durée
    duration_days = (data.endDate - data.startDate).days

    # 4. Formatage des logements
    if data.availableLodgings:
        lodgings_list = []
        for l in data.availableLodgings:
            wifi_str = " | WiFi" if l.wifi else ""
            clim_str = " | Clim" if l.clim else ""
            lodgings_list.append(
                f"- ID: {l.id} | Nom: {l.lodgingName} | Lieu: {l.location} | "
                f"Prix/nuit: {l.pricePerNight}€ | Capacité: {l.numberOfGuests} pers. | "
                f"Chambres: {l.numberOfRooms}{wifi_str}{clim_str}"
            )
        lodgings_str = "\n".join(lodgings_list)
    else:
        lodgings_str = "Aucun logement disponible"

    # 5. Formatage des transports
    if data.availableTransports:
        transports_str = "\n".join([
            f"- ID: {t.id} | Type: {t.type} | {t.departureLocation} → {t.arrivalLocation} | "
            f"Horaires: {t.departureHour} - {t.arrivalHour} | Compagnie: {t.company} | Prix: {t.price}"
            for t in data.availableTransports
        ])
    else:
        transports_str = "Aucun transport disponible"

    # 6. Préférence écologique
    eco_str = "Privilégie les options écologiques si possible.\n" if data.preferences.ecologicalPreference else ""

    # 7. Assemblage final du prompt
    prompt = f"""Tu es un assistant de planification de voyages. Ton rôle est de sélectionner les meilleurs transports et logements parmi les options disponibles, en respectant le budget donné.

## Objectif du voyage
{goal_instruction}

## Budget total
{data.budget}

## Nombre de personnes
{data.numberOfPeople}

## Trajet
- Départ : {data.departurePoint.name}, {data.departurePoint.country}
- Arrivée : {data.returnPoint.name}, {data.returnPoint.country}
- Dates souhaitées : du {data.startDate.strftime('%d/%m/%Y')} au {data.endDate.strftime('%d/%m/%Y')}
- {children_info}

## Logements disponibles
{lodgings_str}

## Transports disponibles
{transports_str}

## Instructions
Sélectionne les transports et logements qui rentrent dans le budget total.
IMPORTANT :
1. Les dates et horaires doivent se suivre LOGIQUEMENT et CHRONOLOGIQUEMENT.
   - Si tu chaînes plusieurs transports (ex: A -> B puis B -> C), la date/heure d'arrivée du premier DOIT être avant la date/heure de départ du suivant.
   - La date de début de l'hébergement doit correspondre à la date d'arrivée sur place.
   - La date de fin de l'hébergement doit correspondre à la date de départ pour le retour.
2. Si le budget est insuffisant pour la durée totale ({duration_days} jours), tu DOIS raccourcir la durée du voyage (réduire le nombre de nuits) pour rentrer dans le budget.
{eco_str}
Réponds UNIQUEMENT avec un objet JSON au format suivant (sans backticks markdown) :
{{
  "selectedTransports": [
    {{ "$id": "transport-xxx", "departureDate": "YYYY-MM-DD" }}
  ],
  "selectedLodgings": [
    {{ "$id": "lodging-xxx", "numberOfNights": 3 }}
  ],
  "tripStartDate": "YYYY-MM-DD",
  "tripEndDate": "YYYY-MM-DD",
  "totalCost": "XXX €",
  "remainingBudget": "XXX €"
}}"""

    return prompt.strip()


@router.post("/trip/generate", response_model=TripGenerateResponse, tags=["Trips"])
async def generate_trip(request: TripRequest):
    """
    Génère un itinéraire de voyage personnalisé au format JSON en fonction des critères fournis.
    """
    try:
        prompt = build_trip_prompt(request)
        print(f"Prompt généré: {prompt}")

        generated_content = await generate_response(prompt)

        cleaned_json = re.sub(r'```json\n?', '', generated_content)
        cleaned_json = re.sub(r'```\n?', '', cleaned_json).strip()

        try:
            selection = json.loads(cleaned_json)
        except json.JSONDecodeError:
            print(f"Erreur de parsing JSON: {cleaned_json}")
            raise HTTPException(
                status_code=500, 
                detail={"error": "Réponse de l'IA invalide", "rawContent": generated_content}
            )
        return TripGenerateResponse(
            success=True,
            tripId=str(uuid.uuid4()),
            createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            request=request,
            selection=selection
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erreur lors de la génération du voyage: {e}")
        raise HTTPException(status_code=500, detail=str(e))