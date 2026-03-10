from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.models import PromptRequest, PromptResponse, TripRequest, TripGenerateResponse, TripSelection
from app.services.gemini_ai import generate_response, generate_structured_response
from app.services.pdf_generator import generate_trip_pdf
import uuid
import io
from datetime import datetime, timezone

router = APIRouter()


@router.post("/ask", response_model=PromptResponse, tags=["AI Interaction"])
async def ask_gemini(request: PromptRequest):
    """
    Reçoit un prompt libre de la webapp, interroge Gemini et renvoie la réponse brute en texte.
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Le message ne peut pas être vide ou constitué uniquement d'espaces.")
    
    ai_answer = await generate_response(request.message)
    
    return PromptResponse(response=ai_answer)



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
{eco_str}"""

    return prompt.strip()


@router.post("/trip/generate", response_model=TripGenerateResponse, tags=["Trips"])
async def generate_trip(request: TripRequest):
    """
    Génère un itinéraire de voyage personnalisé au format JSON en fonction des critères fournis.
    """
    try:
        prompt = build_trip_prompt(request)
        print(f"Prompt généré: {prompt}")

        selection = await generate_structured_response(prompt, TripSelection)

        return TripGenerateResponse(
            success=True,
            tripId=str(uuid.uuid4()),
            createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            request=request,
            selection=selection
        )

    except Exception as e:
        print(f"Erreur lors de la génération du voyage: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trip/pdf", tags=["Trips"])
async def generate_trip_pdf_endpoint(request: TripRequest):
    """
    Génère un itinéraire de voyage et retourne un PDF récapitulatif complet.
    """
    try:
        prompt = build_trip_prompt(request)
        selection = await generate_structured_response(prompt, TripSelection)

        trip_response = TripGenerateResponse(
            success=True,
            tripId=str(uuid.uuid4()),
            createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            request=request,
            selection=selection
        )

        pdf_bytes = generate_trip_pdf(trip_response)

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=voyage_{trip_response.tripId}.pdf"
            }
        )

    except Exception as e:
        print(f"Erreur lors de la génération du PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))