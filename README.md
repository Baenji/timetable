# Timetable to ICS Converter

Fetches TH Aalen lecture schedules from HTML and converts them to iCalendar format.

## Quick Start

```bash
pip install beautifulsoup4 ics requests pytz
python timetable.py
```

## Configuration

Edit variables in `timetable.py`:
- `URL` - Source webpage
- `OUTPUT_FILE` - Output ICS filename
- `RELEVANT_GROUP` - Filter by study group (e.g., "Gr. 1")

## Output

Generates an ICS calendar file with lecture events including:
- Course title and time
- Location and lecturer
- Proper timezone handling (Europe/Berlin)

## Automation

GitHub Actions workflow (`.github/workflows/update.yml`) runs daily to auto-update the calendar file.
