import re
import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
import pytz
import hashlib

# KONFIGURATION
URL = "https://www.th-ab.de/fileadmin/th-ab-redaktion/Stundenplaene/SD_2023.html"
OUTPUT_FILE = 'Vorlesungen_SD_Gr1.ics'
RELEVANT_GROUP = "Gr. 1" 

def fetch_and_parse():
    print(f"Lade Stundenplan von {URL} ...")
    try:
        response = requests.get(URL)
        response.raise_for_status()
        
        # Encoding manuell setzen
        response.encoding = 'iso-8859-15' 
        html_content = response.text
        
        cal = parse_schedule(html_content)
        
        if len(cal.events) == 0:
            print("Warnung: Es wurden keine Termine gefunden. Prüfe den Filter 'RELEVANT_GROUP'.")
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.writelines(cal.serialize_iter())
            
        print(f"Erfolg! Kalenderdatei gespeichert unter: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"Fehler beim Laden oder Parsen: {e}")
        import traceback
        traceback.print_exc()

def parse_schedule(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    cal = Calendar()
    tz = pytz.timezone("Europe/Berlin")

    # 1. Jahr aus dem Header extrahieren
    header_div = soup.find('div', class_='w2')
    year = datetime.now().year # Fallback
    if header_div:
        header_text = header_div.get_text()
        year_match = re.search(r'20\d{2}', header_text)
        if year_match:
            year = int(year_match.group(0))

    # 2. Spalten-zu-Datum Mapping
    day_mapping = {} 
    current_col_idx = 0
    found_header = False
    
    table = soup.find('table')
    if not table:
        print("Fehler: Keine Tabelle im HTML gefunden.")
        return cal

    # Header-Zeile suchen
    for row in table.find_all('tr'):
        cells = row.find_all(['td', 'th'])
        # Suche nach Zeile mit Datumsangaben (z.B. "07.07.")
        if any(re.search(r'\d{2}\.\d{2}\.', c.get_text()) for c in cells):
            for cell in cells:
                colspan = int(cell.get('colspan', 1))
                text = cell.get_text(strip=True)
                # Extrahiere Datum: "Mo, 07.07." -> "07.07."
                date_match = re.search(r'(\d{2}\.\d{2}\.)', text)
                
                if date_match:
                    date_str = date_match.group(1) 
                    for i in range(current_col_idx, current_col_idx + colspan):
                        day_mapping[i] = date_str
                
                current_col_idx += colspan
            found_header = True
            break
            
    if not found_header:
        print("Konnte die Datumszeile nicht identifizieren.")
        return cal

    # 3. Grid parsen
    rows = table.find_all('tr')
    blocked_slots = {} 

    # Start-Index finden (erste Zeile mit Uhrzeit)
    event_row_start_index = 0
    for i, row in enumerate(rows):
        if "8:00" in row.get_text() or "rowspan" in str(row): 
            event_row_start_index = i
            break
            
    for row in rows[event_row_start_index:]:
        cells = row.find_all('td')
        visual_col = 0
        cell_idx = 0
        
        # Grid durchlaufen (ca 30 Spalten max)
        while cell_idx < len(cells) or visual_col in blocked_slots:
            if visual_col in blocked_slots:
                blocked_slots[visual_col] -= 1
                if blocked_slots[visual_col] == 0:
                    del blocked_slots[visual_col]
                visual_col += 1
                continue
            
            if cell_idx >= len(cells):
                break
                
            cell = cells[cell_idx]
            cell_colspan = int(cell.get('colspan', 1))
            cell_rowspan = int(cell.get('rowspan', 1))
            
            if 'v' in cell.get('class', []):
                process_event(cell, visual_col, day_mapping, year, cal, tz)
            
            if cell_rowspan > 1:
                for k in range(visual_col, visual_col + cell_colspan):
                    blocked_slots[k] = cell_rowspan - 1
            
            visual_col += cell_colspan
            cell_idx += 1

    return cal

def process_event(cell, visual_col, day_mapping, year, cal, tz):
    text = cell.get_text(separator="\n").strip()
    
    # Filter
    if RELEVANT_GROUP not in text:
        return

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines: return

    # Zeit extrahieren
    time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', lines[0])
    if not time_match: return
    
    start_str, end_str = time_match.groups()
    
    # Datum finden
    date_str = day_mapping.get(visual_col) or day_mapping.get(visual_col - 1)
    if not date_str: return

    # --- KORREKTUR HIER ---
    # date_str ist z.B. "07.07."
    # Wir entfernen den letzten Punkt und splitten am Punkt
    clean_date = date_str.strip('.') # "07.07"
    day_str, month_str = clean_date.split('.') # ["07", "07"]
    day = int(day_str)
    month = int(month_str)
    # ----------------------

    start_dt = tz.localize(datetime(year, month, day, *map(int, start_str.split(':'))))
    end_dt = tz.localize(datetime(year, month, day, *map(int, end_str.split(':'))))

    e = Event()
    e.name = lines[1] if len(lines) > 1 else "Vorlesung"
    
    # Ort und Dozent finden (einfache Heuristik)
    lecturer = lines[2] if len(lines) > 2 else ""
    location = lines[3] if len(lines) > 3 else ""
    
    e.location = location
    e.begin = start_dt
    e.end = end_dt
    e.description = f"Dozent: {lecturer}\n\n{text}"
    
    cal.events.add(e)

def process_event(cell, visual_col, day_mapping, year, cal, tz):
    text = cell.get_text(separator="\n").strip()
    
    # Filter
    if RELEVANT_GROUP not in text:
        return

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines: return

    # Zeit extrahieren
    time_match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', lines[0])
    if not time_match: return
    
    start_str, end_str = time_match.groups()
    
    # Datum finden
    date_str = day_mapping.get(visual_col) or day_mapping.get(visual_col - 1)
    if not date_str: return

    clean_date = date_str.strip('.') 
    day_str, month_str = clean_date.split('.') 
    day = int(day_str)
    month = int(month_str)

    start_dt = tz.localize(datetime(year, month, day, *map(int, start_str.split(':'))))
    end_dt = tz.localize(datetime(year, month, day, *map(int, end_str.split(':'))))

    e = Event()
    e.name = lines[1] if len(lines) > 1 else "Vorlesung"
    
    lecturer = lines[2] if len(lines) > 2 else ""
    location = lines[3] if len(lines) > 3 else ""
    
    e.location = location
    e.begin = start_dt
    e.end = end_dt
    e.description = f"Dozent: {lecturer}\n\n{text}"
    
    # --- NEU: Eindeutige ID generieren ---
    # Wir basteln einen String aus Zeit + Titel und machen daraus einen Hash.
    uid_string = f"{start_dt.isoformat()}-{e.name}-{location}"
    e.uid = hashlib.md5(uid_string.encode('utf-8')).hexdigest() + "@th-ab.de"
    # -------------------------------------
    
    cal.events.add(e)

if __name__ == "__main__":
    fetch_and_parse()