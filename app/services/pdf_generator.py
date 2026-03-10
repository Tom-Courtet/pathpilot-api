"""
Service de génération PDF pour les récapitulatifs de voyage PathPilot.
Reproduit le design du template A4 - 1_merge.pdf avec fpdf2.
"""

import io
from fpdf import FPDF
from app.schemas.models import TripGenerateResponse


COLOR_BG_BEIGE = (232, 224, 213)       
COLOR_BG_STEEL = (163, 177, 191)       
COLOR_NAVY = (44, 62, 90)              
COLOR_TERRACOTTA = (139, 69, 19)       
COLOR_WHITE = (255, 255, 255)
COLOR_LIGHT_BEIGE = (240, 235, 228)    


class TripPDF(FPDF):
    """PDF personnalisé pour les voyages PathPilot."""

    def __init__(self):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.set_auto_page_break(auto=False)

    def _set_bg(self, color):
        self.set_fill_color(*color)
        self.rect(0, 0, 210, 297, "F")

    def _set_color(self, color):
        self.set_text_color(*color)

    def _draw_separator(self, x, y, w):
        self.set_draw_color(*COLOR_TERRACOTTA)
        self.set_line_width(0.6)
        self.line(x, y, x + w, y)

    def _draw_checkbox(self, x, y, size=4):
        self.set_draw_color(*COLOR_TERRACOTTA)
        self.set_line_width(0.4)
        self.rect(x, y, size, size, "D")

    def _transport_icon_label(self, transport_type: str) -> str:
        icons = {
            "avion": "Avion",
            "train": "Train",
            "bus": "Bus",
            "voiture": "Voiture",
            "bateau": "Bateau",
            "ferry": "Ferry",
        }
        return icons.get(transport_type.lower(), "--")

    def page_cover(self, trip: TripGenerateResponse):
        self.add_page()
        self._set_bg(COLOR_BG_STEEL)

        self.set_font("Helvetica", "", 16)
        self._set_color(COLOR_NAVY)
        nom = f"{trip.request.departurePoint.name} - {trip.request.returnPoint.name}"
        self.set_xy(20, 20)
        self.cell(0, 10, nom, new_x="LMARGIN", new_y="NEXT")

        dates = f"{trip.request.startDate.strftime('%d/%m/%Y')} - {trip.request.endDate.strftime('%d/%m/%Y')}"
        self.set_font("Helvetica", "", 14)
        self.set_xy(120, 20)
        self.cell(70, 10, dates, align="R")

        self.set_font("Helvetica", "I", 38)
        self._set_color(COLOR_NAVY)
        title = f"Voyage {trip.request.returnPoint.name}"
        title_w = self.get_string_width(title)
        self.set_xy((210 - title_w) / 2, 100)
        self.cell(title_w, 20, title)

        self.set_fill_color(*COLOR_LIGHT_BEIGE)
        self.rect(30, 130, 150, 120, "F")
        self.set_font("Helvetica", "", 12)
        self._set_color((180, 175, 168))
        self.set_xy(30, 180)
        self.cell(150, 10, "Image de destination", align="C")

        self.set_font("Helvetica", "B", 20)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 268)
        self.cell(0, 10, "PathPilot")
        self.set_font("Helvetica", "", 8)
        self.set_xy(20, 277)
        self.cell(0, 5, "Votre assistant de voyage intelligent")

    def page_itinerary(self, trip: TripGenerateResponse):
        self.add_page()
        self._set_bg(COLOR_BG_BEIGE)

        self.set_font("Helvetica", "", 36)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 20)
        self.cell(0, 15, "Ton voyage")

        steps = []
        selected_ids = {t.id for t in trip.selection.selectedTransports}
        selected_dates = {t.id: t.departureDate for t in trip.selection.selectedTransports}

        for t in trip.request.availableTransports:
            if t.id in selected_ids:
                steps.append({
                    "label": f"{t.departureLocation} - {t.arrivalLocation}",
                    "location": t.departureLocation,
                    "date": selected_dates.get(t.id, ""),
                    "type": t.type,
                })

        if not steps:
            steps = [{"label": "Départ", "location": trip.request.departurePoint.name,
                       "date": trip.request.startDate.strftime("%d/%m/%Y"), "type": ""}]

        positions = [
            (35, 60), (120, 90), (50, 130), (130, 170), (40, 210)
        ]

        self.set_draw_color(*COLOR_NAVY)
        self.set_line_width(0.5)

        for i in range(min(len(steps), len(positions))):
            px, py = positions[i]

            if i < min(len(steps), len(positions)) - 1:
                nx, ny = positions[i + 1]
                self.line(px + 10, py + 12, nx + 10, ny)

            self.set_draw_color(*COLOR_TERRACOTTA)
            self.set_line_width(0.4)
            self.rect(px - 2, py - 2, 8, 8, "D")
            self.rect(px, py, 4, 4, "D")

            self.set_font("Helvetica", "B", 18)
            self._set_color(COLOR_NAVY)
            self.set_xy(px + 12, py - 4)
            self.cell(60, 10, f"Etape {i + 1}")

            self.set_font("Helvetica", "", 10)
            self._set_color(COLOR_NAVY)
            step = steps[i]
            self.set_xy(px + 12, py + 6)
            self.cell(60, 6, f"{step['location']} - {step['date']}")

        if len(steps) < len(positions):
            idx = len(steps)
            if idx < len(positions):
                px, py = positions[idx]
                if idx > 0:
                    prev_x, prev_y = positions[idx - 1]
                    self.set_draw_color(*COLOR_NAVY)
                    self.set_line_width(0.5)
                    self.line(prev_x + 10, prev_y + 12, px + 10, py)

                self.set_draw_color(*COLOR_TERRACOTTA)
                self.set_line_width(0.4)
                self.rect(px - 2, py - 2, 8, 8, "D")
                self.rect(px, py, 4, 4, "D")

                self.set_font("Helvetica", "B", 18)
                self._set_color(COLOR_NAVY)
                self.set_xy(px + 12, py - 4)
                self.cell(60, 10, f"Retour")

                self.set_font("Helvetica", "", 10)
                self.set_xy(px + 12, py + 6)
                self.cell(60, 6, f"{trip.request.returnPoint.name} - {trip.selection.tripEndDate}")

    def page_transports(self, trip: TripGenerateResponse):
        self.add_page()
        self._set_bg(COLOR_BG_BEIGE)

        self.set_font("Helvetica", "", 36)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 20)
        self.cell(0, 15, "Transports")

        selected_ids = {t.id for t in trip.selection.selectedTransports}
        selected_dates = {t.id: t.departureDate for t in trip.selection.selectedTransports}
        selected_transports = [t for t in trip.request.availableTransports if t.id in selected_ids]

        y = 55
        for t in selected_transports:
            if y > 260:
                self.add_page()
                self._set_bg(COLOR_BG_BEIGE)
                y = 30

            self.set_font("Helvetica", "B", 14)
            self._set_color(COLOR_NAVY)
            self.set_xy(20, y)
            self.cell(50, 8, t.departureHour)
            self.set_font("Helvetica", "", 11)
            self.set_xy(20, y + 8)
            self.cell(50, 7, t.departureLocation)

            self.set_draw_color(*COLOR_NAVY)
            self.set_line_width(0.4)
            self.line(75, y + 8, 120, y + 8)
            self.line(117, y + 5, 120, y + 8)
            self.line(117, y + 11, 120, y + 8)

            self.set_font("Helvetica", "I", 9)
            self._set_color(COLOR_NAVY)
            type_label = t.type.capitalize()
            self.set_xy(82, y + 10)
            self.cell(30, 6, type_label, align="C")

            dep_date = selected_dates.get(t.id, "")
            self.set_font("Helvetica", "", 8)
            self.set_xy(82, y - 2)
            self.cell(30, 6, dep_date, align="C")

            self.set_font("Helvetica", "B", 14)
            self._set_color(COLOR_NAVY)
            self.set_xy(130, y)
            self.cell(60, 8, t.arrivalHour, align="R")
            self.set_font("Helvetica", "", 11)
            self.set_xy(130, y + 8)
            self.cell(60, 7, t.arrivalLocation, align="R")

            self._draw_separator(40, y + 22, 130)

            y += 35

    def page_details(self, trip: TripGenerateResponse):
        self.add_page()
        self._set_bg(COLOR_BG_BEIGE)

        self.set_font("Helvetica", "B", 36)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 20)
        self.cell(0, 15, "Details")

        selected_ids = {t.id for t in trip.selection.selectedTransports}
        selected_dates = {t.id: t.departureDate for t in trip.selection.selectedTransports}
        selected_transports = [t for t in trip.request.availableTransports if t.id in selected_ids]

        days = {}
        for t in selected_transports:
            date_str = selected_dates.get(t.id, "Jour ?")
            if date_str not in days:
                days[date_str] = []
            days[date_str].append(t)

        y = 50
        day_num = 0
        for date_str, transports in days.items():
            day_num += 1

            if y > 220:
                self.add_page()
                self._set_bg(COLOR_BG_BEIGE)
                y = 25

            self.set_fill_color(*COLOR_TERRACOTTA)
            self.rect(20, y, 45, 12, "F")
            self.set_font("Helvetica", "B", 12)
            self._set_color(COLOR_WHITE)
            self.set_xy(20, y)
            self.cell(45, 12, f"Jour {day_num}", align="C")

            location = transports[0].departureLocation if transports else ""
            self.set_font("Helvetica", "", 12)
            self._set_color(COLOR_NAVY)
            self.set_xy(70, y)
            self.cell(100, 12, location)
            self._draw_separator(70, y + 13, 120)

            y += 20

            self.set_font("Helvetica", "B", 14)
            self._set_color(COLOR_NAVY)
            self.set_xy(20, y)
            self.cell(0, 8, "Itineraires")
            y += 12

            for t in transports:
                if y > 260:
                    self.add_page()
                    self._set_bg(COLOR_BG_BEIGE)
                    y = 25

                self.set_font("Helvetica", "I", 9)
                self._set_color(COLOR_NAVY)
                self.set_xy(25, y)
                self.cell(15, 6, t.type.capitalize())

                self.set_font("Helvetica", "", 10)
                self.set_xy(42, y)
                self.cell(35, 6, f"{t.departureHour} - {t.arrivalHour}")

                self.set_xy(80, y)
                self.cell(50, 6, f"{t.departureLocation} > {t.arrivalLocation}")

                self.set_xy(150, y)
                self.cell(40, 6, date_str)

                y += 10

            y += 5

            self.set_font("Helvetica", "B", 14)
            self._set_color(COLOR_NAVY)
            self.set_xy(20, y)
            self.cell(0, 8, "Activites")
            self._draw_separator(20, y + 9, 55)
            y += 14

            self.set_font("Helvetica", "B", 11)
            self._set_color(COLOR_TERRACOTTA)
            self.set_xy(25, y)
            self.cell(50, 7, "Matinee")

            self.set_xy(115, y)
            self.cell(50, 7, "Soiree")
            y += 10

            for box_idx in range(2):
                self.set_fill_color(*COLOR_LIGHT_BEIGE)
                self.set_draw_color(*COLOR_TERRACOTTA if box_idx == 0 else COLOR_NAVY)
                self.set_line_width(0.3)
                self.rect(25, y, 75, 18, "DF")
                self.set_font("Helvetica", "", 9)
                self._set_color((180, 175, 168))
                self.set_xy(28, y + 3)
                self.cell(70, 5, "Horaires + nom")
                self.set_xy(28, y + 9)
                self.cell(70, 5, "Lieu")

                self.set_draw_color(*COLOR_NAVY)
                self.set_line_width(0.3)
                self.rect(115, y, 75, 18, "DF")
                self.set_xy(118, y + 3)
                self.cell(70, 5, "Horaires + nom")
                self.set_xy(118, y + 9)
                self.cell(70, 5, "Lieu")

                y += 22

            y += 10

    def page_billets(self, trip: TripGenerateResponse):
        self.add_page()
        self._set_bg(COLOR_BG_STEEL)

        self.set_font("Helvetica", "", 36)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 20)
        self.cell(0, 15, "Billets")

        selected_ids = {t.id for t in trip.selection.selectedTransports}
        selected_dates = {t.id: t.departureDate for t in trip.selection.selectedTransports}
        selected_transports = [t for t in trip.request.availableTransports if t.id in selected_ids]

        y = 55
        for t in selected_transports:
            if y > 220:
                self.add_page()
                self._set_bg(COLOR_BG_STEEL)
                y = 30

            self.set_fill_color(*COLOR_LIGHT_BEIGE)
            self.rect(20, y, 170, 50, "F")

            self.set_font("Helvetica", "B", 11)
            self._set_color(COLOR_NAVY)
            self.set_xy(25, y + 5)
            self.cell(20, 8, t.type.capitalize())

            dep_date = selected_dates.get(t.id, "")
            self.set_font("Helvetica", "", 11)
            self.set_xy(25, y + 13)
            self.cell(80, 7, f"{dep_date}  {t.departureHour}")

            self.set_font("Helvetica", "B", 11)
            self.set_xy(25, y + 22)
            trajet = f"{t.departureLocation}  >  {t.arrivalLocation}"
            self.cell(100, 7, trajet)

            self.set_font("Helvetica", "", 12)
            self.set_xy(130, y + 5)
            self.cell(55, 8, t.company, align="R")

            self.set_fill_color(220, 218, 215)
            self.rect(25, y + 32, 155, 14, "F")
            self.set_font("Helvetica", "", 8)
            self._set_color((160, 155, 148))
            self.set_xy(25, y + 35)
            self.cell(155, 8, "Zone reservee pour QR code / billet electronique", align="C")

            self.set_draw_color(*COLOR_NAVY)
            self.set_line_width(0.8)
            self.line(30, y + 50, 180, y + 50)

            y += 60

    def page_checklist(self, trip: TripGenerateResponse):
        self.add_page()
        self._set_bg(COLOR_BG_BEIGE)

        self.set_font("Helvetica", "", 36)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 20)
        self.cell(0, 15, "Check List")

        categories = {
            "Documents": [
                "Passeport / Carte d'identite",
                "Billets d'avion / train",
                "Reservations hotel",
                "Assurance voyage",
                "Permis de conduire",
            ],
            "Vetements": [
                "T-shirts / hauts",
                "Pantalons / shorts",
                "Sous-vetements",
                "Chaussures confortables",
                "Veste / pull",
            ],
            "Hygiene": [
                "Brosse a dents",
                "Shampoing / gel douche",
                "Protection solaire",
                "Trousse de premiers soins",
                "Medicaments personnels",
            ],
            "Electronique": [
                "Chargeur telephone",
                "Adaptateur de prise",
                "Batterie externe",
                "Ecouteurs",
                "Appareil photo",
            ],
        }

        y_start = 55
        col_x = [25, 115]
        cat_idx = 0

        for cat_name, items in categories.items():
            col = cat_idx % 2
            x = col_x[col]
            y = y_start + (cat_idx // 2) * 95

            self.set_font("Helvetica", "B", 13)
            self._set_color(COLOR_NAVY)
            self.set_xy(x, y)
            self.cell(70, 8, cat_name)
            self._draw_separator(x, y + 10, 55)

            item_y = y + 16
            for item in items:
                self._draw_checkbox(x, item_y)
                self.set_font("Helvetica", "", 10)
                self._set_color(COLOR_NAVY)
                self.set_xy(x + 7, item_y - 1)
                self.cell(65, 6, item)
                item_y += 10

            cat_idx += 1

    def page_contacts(self, trip: TripGenerateResponse):
        self.add_page()
        self._set_bg(COLOR_BG_BEIGE)

        self.set_font("Helvetica", "", 36)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 20)
        self.cell(0, 15, "Contacts utiles")

        self.set_font("Helvetica", "B", 60)
        self._set_color(COLOR_TERRACOTTA)
        self.set_xy(20, 55)
        self.cell(170, 25, "112", align="C")

        self.set_font("Helvetica", "", 12)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, 82)
        self.cell(170, 8, "Numero d'urgence europeen", align="C")

        contacts = [
            {"pays": "France", "police": "17", "pompiers": "18", "ambulance": "15"},
            {"pays": "Espagne", "police": "091", "pompiers": "080", "ambulance": "061"},
            {"pays": "Italie", "police": "113", "pompiers": "115", "ambulance": "118"},
            {"pays": "Allemagne", "police": "110", "pompiers": "112", "ambulance": "112"},
            {"pays": "Portugal", "police": "112", "pompiers": "112", "ambulance": "112"},
            {"pays": "Royaume-Uni", "police": "999", "pompiers": "999", "ambulance": "999"},
            {"pays": "Grece", "police": "100", "pompiers": "199", "ambulance": "166"},
        ]

        y = 105
        col_widths = [45, 35, 35, 35]
        headers = ["Pays", "Police", "Pompiers", "Ambulance"]

        self.set_fill_color(*COLOR_NAVY)
        x = 30
        for i, header in enumerate(headers):
            self.set_font("Helvetica", "B", 11)
            self._set_color(COLOR_WHITE)
            self.set_xy(x, y)
            self.cell(col_widths[i], 10, header, fill=True, align="C")
            x += col_widths[i]

        y += 10

        for row_idx, contact in enumerate(contacts):
            x = 30
            bg = COLOR_LIGHT_BEIGE if row_idx % 2 == 0 else COLOR_BG_BEIGE
            self.set_fill_color(*bg)

            values = [contact["pays"], contact["police"], contact["pompiers"], contact["ambulance"]]
            for i, val in enumerate(values):
                self.set_font("Helvetica", "B" if i == 0 else "", 10)
                self._set_color(COLOR_NAVY)
                self.set_xy(x, y)
                self.cell(col_widths[i], 9, val, fill=True, align="C")
                x += col_widths[i]

            y += 9

        y += 15
        self.set_font("Helvetica", "I", 10)
        self._set_color(COLOR_NAVY)
        self.set_xy(20, y)
        self.cell(170, 7, "Ces numeros sont valables depuis un telephone fixe ou mobile local.", align="C")
        self.set_xy(20, y + 8)
        self.cell(170, 7, "Depuis un mobile etranger, composez le +33 pour la France, etc.", align="C")


def generate_trip_pdf(trip_data: TripGenerateResponse) -> bytes:
    """
    Génère un PDF complet du récapitulatif de voyage.
    Retourne les bytes du PDF.
    """
    pdf = TripPDF()

    pdf.page_cover(trip_data)
    pdf.page_itinerary(trip_data)
    pdf.page_transports(trip_data)
    pdf.page_details(trip_data)
    pdf.page_billets(trip_data)
    pdf.page_checklist(trip_data)
    pdf.page_contacts(trip_data)

    return pdf.output()
