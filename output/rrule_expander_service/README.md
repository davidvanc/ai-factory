# rrule_expander_service

HTTP microservice die iCalendar RRULE-strings volgens RFC 5545 uitklapt naar concrete datums/datetimes. Ondersteunt FREQ (SECONDLY t/m YEARLY), INTERVAL, BYDAY (incl. ordinals zoals -1SU), BYMONTHDAY (incl. negatieve waarden), BYMONTH, BYSETPOS, WKST, COUNT en UNTIL. Biedt daarnaast validatie/parsing van RRULE-strings, een 'volgende N occurrences vanaf een moment'-endpoint, expansie van volledige VEVENT-achtige recurrence sets (RRULE + RDATE + EXDATE) en een menselijk leesbare beschrijving van de regel.

## Lokaal draaien

```bash
docker build -t rrule_expander_service .
docker run --rm -p 8002:8002 rrule_expander_service
```

De service draait dan op http://localhost:8002


## Endpoints en testcommando's

### POST /expand

Klapt een RRULE-string uit naar concrete datums vanaf DTSTART. Respecteert COUNT/UNTIL en past een server-side veiligheidslimiet (max_results) toe. Ondersteunt optionele window (after/before) om alleen occurrences binnen een periode te retourneren.

```bash
curl -X POST http://localhost:8002/expand -H 'Content-Type: application/json' -d '{"rrule": "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR;COUNT=6", "dtstart": "2024-01-01T09:00:00", "tzid": "Europe/Amsterdam", "max_results": 100}'
```

**Response:**
```json
{
  "rrule": "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR;COUNT=6",
  "dtstart": "2024-01-01T09:00:00+01:00",
  "tzid": "Europe/Amsterdam",
  "count": 6,
  "truncated": false,
  "terminated_by": "COUNT",
  "occurrences": [
    "2024-01-01T09:00:00+01:00",
    "2024-01-03T09:00:00+01:00",
    "2024-01-05T09:00:00+01:00",
    "2024-01-15T09:00:00+01:00",
    "2024-01-17T09:00:00+01:00",
    "2024-01-19T09:00:00+01:00"
  ]
}
```

### GET /expand

Zelfde expansie als POST /expand maar via query parameters, handig voor snelle tests en links. Geeft altijd JSON terug.

```bash
curl -G http://localhost:8002/expand --data-urlencode 'rrule=FREQ=MONTHLY;BYMONTHDAY=-1;COUNT=4' --data-urlencode 'dtstart=2024-01-31' --data-urlencode 'max_results=50'
```

**Response:**
```json
{
  "rrule": "FREQ=MONTHLY;BYMONTHDAY=-1;COUNT=4",
  "dtstart": "2024-01-31",
  "tzid": null,
  "count": 4,
  "truncated": false,
  "terminated_by": "COUNT",
  "occurrences": [
    "2024-01-31",
    "2024-02-29",
    "2024-03-31",
    "2024-04-30"
  ]
}
```

### POST /next

Geeft de volgende N occurrences van een RRULE vanaf een referentiemoment (default: nu in UTC). Handig voor schedulers.

```bash
curl -X POST http://localhost:8002/next -H 'Content-Type: application/json' -d '{"rrule": "FREQ=DAILY;INTERVAL=3", "dtstart": "2024-01-01T08:00:00Z", "from_datetime": "2024-02-01T00:00:00Z", "n": 3}'
```

**Response:**
```json
{
  "rrule": "FREQ=DAILY;INTERVAL=3",
  "from_datetime": "2024-02-01T00:00:00+00:00",
  "n": 3,
  "occurrences": [
    "2024-02-01T08:00:00+00:00",
    "2024-02-04T08:00:00+00:00",
    "2024-02-07T08:00:00+00:00"
  ],
  "exhausted": false
}
```

### POST /validate

Parseert en valideert een RRULE-string tegen RFC 5545 zonder te expanderen. Retourneert de genormaliseerde regel, de losse onderdelen en eventuele fouten/waarschuwingen (bv. BYDAY met ordinal bij FREQ=WEEKLY is ongeldig).

```bash
curl -X POST http://localhost:8002/validate -H 'Content-Type: application/json' -d '{"rrule": "RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1TU;WKST=SU", "dtstart": "2024-01-01"}'
```

**Response:**
```json
{
  "valid": true,
  "normalized": "FREQ=YEARLY;BYMONTH=11;BYDAY=1TU;WKST=SU",
  "parts": {
    "FREQ": "YEARLY",
    "INTERVAL": 1,
    "BYMONTH": [
      11
    ],
    "BYDAY": [
      {
        "ordinal": 1,
        "weekday": "TU"
      }
    ],
    "WKST": "SU"
  },
  "infinite": true,
  "errors": [],
  "warnings": []
}
```

### POST /describe

Geeft een menselijk leesbare beschrijving van een RRULE-string (en/nl), plus metadata zoals of de reeks eindig is.

```bash
curl -X POST http://localhost:8002/describe -H 'Content-Type: application/json' -d '{"rrule": "FREQ=MONTHLY;BYDAY=-1FR;UNTIL=20241231T235959Z", "dtstart": "2024-01-01T10:00:00Z", "locale": "nl"}'
```

**Response:**
```json
{
  "rrule": "FREQ=MONTHLY;BYDAY=-1FR;UNTIL=20241231T235959Z",
  "locale": "nl",
  "text": "Elke maand op de laatste vrijdag, tot en met 31 december 2024",
  "infinite": false,
  "terminated_by": "UNTIL"
}
```

### POST /recurrence-set/expand

Expandeert een volledige recurrence set: meerdere RRULEs, extra RDATEs en uitgesloten EXDATEs, gesorteerd en gededupliceerd zoals RFC 5545 voorschrijft.

```bash
curl -X POST http://localhost:8002/recurrence-set/expand -H 'Content-Type: application/json' -d '{"dtstart": "2024-03-01T12:00:00Z", "rrules": ["FREQ=WEEKLY;BYDAY=FR;COUNT=4"], "rdates": ["2024-03-06T12:00:00Z"], "exdates": ["2024-03-15T12:00:00Z"], "max_results": 50}'
```

**Response:**
```json
{
  "count": 4,
  "truncated": false,
  "occurrences": [
    "2024-03-01T12:00:00+00:00",
    "2024-03-06T12:00:00+00:00",
    "2024-03-08T12:00:00+00:00",
    "2024-03-22T12:00:00+00:00"
  ],
  "excluded": [
    "2024-03-15T12:00:00+00:00"
  ]
}
```

### POST /expand/batch

Expandeert meerdere RRULE-verzoeken in één call. Per item wordt succes of een foutobject teruggegeven zodat één ongeldige regel de batch niet laat falen.

```bash
curl -X POST http://localhost:8002/expand/batch -H 'Content-Type: application/json' -d '{"items": [{"id": "a", "rrule": "FREQ=DAILY;COUNT=2", "dtstart": "2024-01-01"}, {"id": "b", "rrule": "FREQ=BOGUS;COUNT=2", "dtstart": "2024-01-01"}], "max_results": 20}'
```

**Response:**
```json
{
  "results": [
    {
      "id": "a",
      "ok": true,
      "count": 2,
      "occurrences": [
        "2024-01-01",
        "2024-01-02"
      ]
    },
    {
      "id": "b",
      "ok": false,
      "error": {
        "code": "INVALID_FREQ",
        "message": "FREQ=BOGUS is not a valid RFC 5545 frequency"
      }
    }
  ]
}
```

### GET /status

Health/readiness check met versie-informatie, ondersteunde RRULE-onderdelen en configuratielimieten.

```bash
curl http://localhost:8002/status
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "rfc": "RFC 5545",
  "supported_parts": [
    "FREQ",
    "INTERVAL",
    "BYDAY",
    "BYMONTHDAY",
    "BYMONTH",
    "BYSETPOS",
    "WKST",
    "COUNT",
    "UNTIL"
  ],
  "limits": {
    "max_results": 10000,
    "max_batch_items": 100
  }
}
```

## Standaard endpoints (van service template)

```bash
curl http://localhost:8002/health    # liveness probe
curl http://localhost:8002/ready     # readiness probe
curl http://localhost:8002/metrics   # Prometheus metrics
open http://localhost:8002/docs      # OpenAPI documentation
```


## Tests draaien

```bash
docker run --rm rrule_expander_service python -m pytest tests/ -v
```

## Project structuur

- `src/` - source code
- `tests/` - tests
- `Dockerfile` - container definitie
- `requirements.txt` - Python dependencies
- `.env.example` - voorbeeld environment variabelen

## Configuratie

Kopieer `.env.example` naar `.env` en pas aan indien nodig:

```bash
cp .env.example .env
```

---
*Auto-generated by AI Software Factory*
