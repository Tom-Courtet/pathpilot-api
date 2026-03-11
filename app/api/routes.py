from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.models import (
    PromptRequest, PromptResponse, TripRequest, TripGenerateResponse, TripSelection,
    TravelDocument, TravelSchema
)
from app.services.gemini_ai import generate_response, generate_structured_response
from app.services.pdf_generator import generate_trip_pdf
import uuid
import io
import json
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
    
    if data.preferences.travelWithChildren and data.preferences.children:
        ages = ", ".join([f"{c.age} ans" for c in data.preferences.children])
        children_info = f"Enfants présents : {ages}"
    else:
        children_info = "Pas d'enfants"

    if data.tripGoal == "cheapest":
        goal_instruction = "L'objectif est de minimiser le coût total. Choisis les options les moins chères."
    else:
        goal_instruction = "L'objectif est de visiter le maximum d'endroits différents. Sélectionne plusieurs logements dans différentes zones si possible."

    # Formater les dates une seule fois pour les réutiliser facilement
    start_date_str = data.startDate.strftime('%d/%m/%Y')
    end_date_str = data.endDate.strftime('%d/%m/%Y')
    duration_days = (data.endDate - data.startDate).days

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

    if data.availableTransports:
        transports_str = "\n".join([
            f"- ID: {t.id} | Type: {t.type} | {t.departureLocation} → {t.arrivalLocation} | "
            f"Horaires: {t.departureHour} - {t.arrivalHour} | Compagnie: {t.company} | Prix: {t.price}"
            for t in data.availableTransports
        ])
    else:
        transports_str = "Aucun transport disponible"

    eco_str = "4. **Écologie :** Privilégie les options écologiques si possible.\n" if data.preferences.ecologicalPreference else ""

    prompt = f"""Tu es un assistant de planification de voyages expert en logistique. Ton rôle est de sélectionner les meilleurs transports et logements parmi les options disponibles, en respectant le budget donné.

## Objectif du voyage
{goal_instruction}

## Budget total maximum
{data.budget}€

## Nombre de personnes
{data.numberOfPeople} personne(s)
{children_info}

## Trajet souhaité
- Départ de : {data.departurePoint.name}, {data.departurePoint.country}
- Arrivée à : {data.returnPoint.name}, {data.returnPoint.country}
- Dates : du {start_date_str} au {end_date_str} ({duration_days} jours)

## Logements disponibles
{lodgings_str}

## Transports disponibles
{transports_str}

## Instructions Critiques (À RESPECTER IMPÉRATIVEMENT) :
1. **Limites de dates strictes :** L'intégralité du voyage DOIT se dérouler entre le {start_date_str} et le {end_date_str}. Tu n'as pas le droit de sélectionner un transport ou un logement en dehors de cette plage de dates.
2. **Continuité absolue (AUCUN TROU) :** Chaque jour et chaque nuit de l'itinéraire sélectionné doit être couvert. Il ne peut y avoir aucun jour vide sans logement ou sans transport en cours. Les dates doivent se suivre parfaitement.
3. **Logique Chronologique :**
   - La date et l'heure de check-in du premier hébergement doivent correspondre à l'arrivée du transport aller.
   - Si tu combines plusieurs transports (ex: A -> B puis B -> C), l'heure d'arrivée du premier DOIT être antérieure à l'heure de départ du suivant. Laisse un délai raisonnable pour la correspondance.
4. **Gestion du budget :** Si le budget est insuffisant pour tenir les {duration_days} jours, tu DOIS raccourcir la durée du voyage en avançant la date de retour. La règle de continuité absolue s'applique toujours sur ce voyage raccourci.
{eco_str}
## Format de réponse
Pour t'assurer qu'il n'y a aucune erreur de dates, commence TOUJOURS ta réponse par un récapitulatif "Jour par Jour" (ex: Jour 1 : [Date] - [Action/Lieu]) avant de lister les ID des transports et logements choisis.
"""

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
async def generate_trip_pdf_endpoint(request: TravelDocument):
    """
    Reçoit un document de voyage complet et retourne un PDF récapitulatif.
    """
    try:
        schema = TravelSchema.model_validate(json.loads(request.schema_))

        pdf_bytes = generate_trip_pdf(request, schema)

        filename = request.name.replace(' ', '_') if request.name else 'voyage'
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}.pdf"'
            }
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Le champ schema contient un JSON invalide.")
    except Exception as e:
        print(f"Erreur lors de la génération du PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))