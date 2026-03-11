import io
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from app.schemas.models import TravelDocument, TravelSchema

def format_date(date_str: str) -> str:
    """Formate une date ISO en dd/mm/yyyy."""
    if not date_str:
        return ""
    try:
        date_part = date_str.split("T")[0]
        parts = date_part.split("-")
        if len(parts) == 3:
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
    except Exception:
        pass
    return date_str

def generate_trip_pdf(doc: TravelDocument, schema: TravelSchema) -> bytes:
    """
    Génère un PDF complet du récapitulatif de voyage via HTML/CSS.
    Retourne les bytes du PDF.
    """
    # 1. Préparation des données formatées pour le template
    steps = []
    for leg in schema.transportLegs:
        # Logique d'extraction des étapes (similaire à ton code d'origine)
        steps.append({
            "location": leg.fromLocation,
            "date": format_date(leg.date) if leg.date else "",
        })

    if not steps:
        departure_name = schema.departurePoint.name if schema.departurePoint else "Départ"
        steps = [{"location": departure_name, "date": format_date(doc.startDate)}]

    # 2. Configuration de Jinja2 (assure-toi que le dossier 'templates' existe à la racine)
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('template_voyage.html')

    # 3. Rendu du HTML avec les variables injectées
    html_out = template.render(
        doc=doc,
        schema=schema,
        steps=steps,
        # Tu peux injecter ici les autres données préparées (transports, checklist, etc.)
    )

    # 4. Conversion du HTML en PDF avec WeasyPrint
    pdf_bytes = HTML(string=html_out).write_pdf()

    return pdf_bytes