import io
from pathlib import Path # <-- Ajout de pathlib
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
    steps = []
    for leg in schema.transportLegs:
        steps.append({
            "location": leg.fromLocation,
            "date": format_date(leg.date) if leg.date else "",
        })

    if not steps:
        departure_name = schema.departurePoint.name if schema.departurePoint else "Départ"
        steps = [{"location": departure_name, "date": format_date(doc.startDate)}]

    current_dir = Path(__file__).parent.resolve()
    env = Environment(loader=FileSystemLoader(str(current_dir)))
    template = env.get_template('template.html')

    html_out = template.render(
        doc=doc,
        schema=schema,
        steps=steps,
    )

    pdf_bytes = HTML(string=html_out).write_pdf()

    return pdf_bytes