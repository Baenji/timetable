import requests
from bs4 import BeautifulSoup
from ics import Calendar, Event
import datetime
import re

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("Europe/Berlin")
except ImportError:
    LOCAL_TZ = datetime.timezone(datetime.timedelta(hours=1))

DS_GROUP = 1  # Gruppe im Schwerpunkt Data Science (1 oder 2), None = alle Gruppen

URL_DS = "https://www.th-ab.de/fileadmin/th-ab-redaktion/Stundenplaene/SP-DS.html"

def fetch_html(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Bot/GitHubActions'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der URL {url}: {e}")
        return None

def parse_table(table):
    grid = {}
    for row_idx, tr in enumerate(table.find_all('tr')):
        col_idx = 0
        for td in tr.find_all(['td', 'th']):
            while (row_idx, col_idx) in grid:
                col_idx += 1
            
            rowspan = int(td.get('rowspan', 1))
            colspan = int(td.get('colspan', 1))
            
            for r in range(rowspan):
                for c in range(colspan):
                    grid[(row_idx + r, col_idx + c)] = td
            
            col_idx += colspan
    return grid

def filter_ds_group(text_lines, ds_group):
    if ds_group is None:
        return True

    groups = re.findall(r'Gr\.\s*(\d+)', " ".join(text_lines))
    if not groups:
        return True

    return str(ds_group) in groups

def extract_events_from_html(html, ds_group):
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    events_list = []
    
    for table in tables:
        grid = parse_table(table)
        
        year = datetime.date.today().year
        w2_div = table.find_previous('div', class_='w2')
        if w2_div:
            years = re.findall(r'\d{4}', w2_div.get_text())
            if years:
                year = int(years[-1])
                
        day_mapping = {}
        max_cols = max([c for (r, c) in grid.keys()] + [0]) + 1
        
        for search_row in [0, 1]:
            if day_mapping: 
                break
            for col_idx in range(max_cols):
                cell = grid.get((search_row, col_idx))
                if cell:
                    text = cell.get_text(strip=True)
                    m = re.search(r'(Mo|Di|Mi|Do|Fr|Sa|So),\s*(\d{1,2})\.(\d{1,2})\.', text)
                    if m:
                        _, day_str, month_str = m.groups()
                        try:
                            day_mapping[col_idx] = datetime.date(year, int(month_str), int(day_str))
                        except ValueError:
                            pass

        seen_cells = set()
        for (r, c), cell in grid.items():
            if id(cell) in seen_cells:
                continue
            seen_cells.add(id(cell))
            
            if cell.get('class') and 'v' in cell.get('class'):
                event_date = day_mapping.get(c)
                if not event_date:
                    continue 
                
                html_text = str(cell)
                html_text = re.sub(r'<br\s*/?>', '\n', html_text)
                text_soup = BeautifulSoup(html_text, 'html.parser')
                lines = [line.strip() for line in text_soup.get_text().split('\n') if line.strip()]
                
                if not lines: continue
                    
                time_str = lines[0] 
                title = lines[1] if len(lines) > 1 else "Unbenanntes Event"
                
                if not filter_ds_group(lines, ds_group):
                    continue
                    
                location = ""
                for line in lines:
                    if "Raum" in line or "Hörsaal" in line or "Seminarraum" in line or re.search(r'[A-Z]\d-\d{3}', line):
                        location = line
                        break
                        
                description = "\n".join(lines[2:])
                
                tm = re.search(r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})', time_str)
                if not tm: continue
                    
                h1, m1, h2, m2 = map(int, tm.groups())
                
                start_dt = datetime.datetime(event_date.year, event_date.month, event_date.day, h1, m1, tzinfo=LOCAL_TZ)
                end_dt = datetime.datetime(event_date.year, event_date.month, event_date.day, h2, m2, tzinfo=LOCAL_TZ)
                
                new_event = Event()
                new_event.name = title
                new_event.begin = start_dt
                new_event.end = end_dt
                new_event.location = location
                new_event.description = f"Uhrzeit: {time_str}\n\n{description}"
                
                events_list.append(new_event)
                
    return events_list

def generate_ics(new_events, filename="sd2023.ics"):
    cal = Calendar()
    existing_keys = set()
    
    for ev in new_events:
        key = (ev.name, ev.begin)
        if key not in existing_keys:
            cal.events.add(ev)
            existing_keys.add(key)
            
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(cal.serialize_iter())
        
    print(f"-> ERFOLG: {len(cal.events)} Termine geschrieben.")
    print(f"-> Datei komplett neu überschrieben: '{filename}'.")

def main():
    print(f"Starte Parsing-Vorgang... (DS-Gruppe: {DS_GROUP or 'alle'})")
    all_events = []

    print("-> Lade URL (DS)...")
    html_ds = fetch_html(URL_DS)
    if html_ds:
        all_events.extend(extract_events_from_html(html_ds, DS_GROUP))

    if all_events:
        generate_ics(all_events, filename="sd2023.ics")
    else:
        print("Keine Termine gefunden!")

if __name__ == "__main__":
    main()