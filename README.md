# Timetable to ICS Converter

Fetches TH AB lecture schedules from HTML, merges multiple schedules, filters by study group, and converts them to iCalendar format.

## Quick Start

```bash
pip install beautifulsoup4 ics requests tzdata
python timetable.py
```

## Configuration

Edit the variables at the top of `timetable.py`:
* **`TARGET_GROUP`** - Filter by your study group (e.g., `"sd61"` or `"sd62"`)
* **`URL_1_SD`** - Source webpage for the main Software Design schedule
* **`URL_2_DS`** - Source webpage for the Data Science schedule (always included)

## Output

Generates an ICS calendar file (`sd2023.ics`) with lecture events including:
* Course title, exact date, and time
* Location and additional descriptions (lecturer, etc.)
* Proper timezone handling (Europe/Berlin)

## Automation

A GitHub Actions workflow (`.github/workflows/update.yml`) runs daily at 06:00 UTC to automatically fetch the latest schedules, update the `sd2023.ics` file, and push changes to the repository.