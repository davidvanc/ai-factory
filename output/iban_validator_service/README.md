# iban_validator_service

HTTP microservice die IBAN-rekeningnummers valideert en formatteert volgens ISO 13616. Bevat landspecifieke lengte- en formaatcontrole via een centrale data-tabel (IBAN_REGISTRY), mod-97 checksumvalidatie (ISO 7064 MOD 97-10), BBAN-structuurparsing en een fouttolerant bulk-endpoint dat elk item los verwerkt en per-item resultaat teruggeeft.

## Lokaal draaien

```bash
docker build -t iban_validator_service .
docker run --rm -p 8006:8006 iban_validator_service
```

De service draait dan op http://localhost:8006


## Endpoints en testcommando's

### POST /validate

Valideert een enkel IBAN: normalisatie (spaties/hoofdletters), landcode-check tegen de registry, landspecifieke lengtecontrole, BBAN-formaatcontrole via regex uit de registry en mod-97 checksum. Retourneert altijd HTTP 200 met valid=true/false en een lijst van gestructureerde fouten; alleen structureel foute request-body geeft 422.

```bash
curl -X POST http://localhost:8006/validate -H 'Content-Type: application/json' -d '{"iban": "nl91 abna 0417 1643 00"}'
```

**Response:**
```json
{
  "input": "nl91 abna 0417 1643 00",
  "valid": true,
  "iban": "NL91ABNA0417164300",
  "formatted": "NL91 ABNA 0417 1643 00",
  "country_code": "NL",
  "country_name": "Netherlands",
  "check_digits": "91",
  "bban": "ABNA0417164300",
  "length": 18,
  "expected_length": 18,
  "bank_code": "ABNA",
  "account_number": "0417164300",
  "checks": {
    "structure": true,
    "country_supported": true,
    "length": true,
    "bban_format": true,
    "mod97": true
  },
  "errors": []
}
```

### POST /validate/bulk

Valideert een lijst IBANs in één call. Elk item wordt onafhankelijk verwerkt: een ongeldig, leeg of niet-string item blokkeert de batch nooit. Per item wordt index, status (valid/invalid/error) en detail teruggegeven, plus een samenvatting.

```bash
curl -X POST http://localhost:8006/validate/bulk -H 'Content-Type: application/json' -d '{"ibans": ["NL91ABNA0417164300", "NL91ABNA0417164301", "XX00INVALID", ""], "format_output": true}'
```

**Response:**
```json
{
  "summary": {
    "total": 6,
    "valid": 3,
    "invalid": 3,
    "errors": 0
  },
  "results": [
    {
      "index": 0,
      "input": "NL91ABNA0417164300",
      "status": "valid",
      "valid": true,
      "iban": "NL91ABNA0417164300",
      "formatted": "NL91 ABNA 0417 1643 00",
      "country_code": "NL",
      "errors": []
    },
    {
      "index": 1,
      "input": "DE89 3704 0044 0532 0130 00",
      "status": "valid",
      "valid": true,
      "iban": "DE89370400440532013000",
      "formatted": "DE89 3704 0044 0532 0130 00",
      "country_code": "DE",
      "errors": []
    },
    {
      "index": 2,
      "input": "GB82WEST12345698765432",
      "status": "valid",
      "valid": true,
      "iban": "GB82WEST12345698765432",
      "formatted": "GB82 WEST 1234 5698 7654 32",
      "country_code": "GB",
      "errors": []
    },
    {
      "index": 3,
      "input": "NL91ABNA0417164301",
      "status": "invalid",
      "valid": false,
      "iban": "NL91ABNA0417164301",
      "formatted": "NL91 ABNA 0417 1643 01",
      "country_code": "NL",
      "errors": [
        {
          "code": "CHECKSUM_FAILED",
          "message": "mod-97 checksum is 24, verwacht 1"
        }
      ]
    },
    {
      "index": 4,
      "input": "XX00INVALID",
      "status": "invalid",
      "valid": false,
      "iban": "XX00INVALID",
      "formatted": "XX00 INVA LID",
      "country_code": "XX",
      "errors": [
        {
          "code": "COUNTRY_NOT_SUPPORTED",
          "message": "landcode 'XX' staat niet in de IBAN-registry"
        }
      ]
    },
    {
      "index": 5,
      "input": "",
      "status": "invalid",
      "valid": false,
      "iban": null,
      "formatted": null,
      "country_code": null,
      "errors": [
        {
          "code": "EMPTY_INPUT",
          "message": "lege waarde is geen geldig IBAN"
        }
      ]
    }
  ]
}
```

### POST /format

Formatteert een IBAN naar print-formaat (groepen van 4, gescheiden door spaties) of naar elektronisch formaat (compact, geen spaties). Formatteren gebeurt ook bij een ongeldige checksum; het validatieresultaat wordt informatief meegegeven.

```bash
curl -X POST http://localhost:8006/format -H 'Content-Type: application/json' -d '{"iban": "nl91abna0417164300", "style": "print"}'
```

**Response:**
```json
{
  "input": "nl91abna0417164300",
  "style": "print",
  "formatted": "NL91 ABNA 0417 1643 00",
  "electronic": "NL91ABNA0417164300",
  "valid": true,
  "errors": []
}
```

### POST /generate-check-digits

Berekent de correcte ISO 7064 MOD 97-10 controlegetallen voor een landcode + BBAN, of herstelt de check digits van een IBAN waarvan de checksum fout is (placeholder '00' of bestaande cijfers worden overschreven).

```bash
curl -X POST http://localhost:8006/generate-check-digits -H 'Content-Type: application/json' -d '{"country_code": "NL", "bban": "ABNA0417164300"}'
```

**Response:**
```json
{
  "country_code": "NL",
  "bban": "ABNA0417164300",
  "check_digits": "91",
  "iban": "NL91ABNA0417164300",
  "formatted": "NL91 ABNA 0417 1643 00",
  "valid": true,
  "errors": []
}
```

### GET /countries

Geeft de volledige centrale IBAN-registry als data-tabel terug: landcode, naam, totale lengte, BBAN-regex, SEPA-vlag en voorbeeld-IBAN. Optionele query parameter 'country' filtert op één landcode.

```bash
curl 'http://localhost:8006/countries?country=NL'
```

**Response:**
```json
{
  "count": 1,
  "countries": [
    {
      "country_code": "NL",
      "country_name": "Netherlands",
      "iban_length": 18,
      "bban_pattern": "^[A-Z]{4}[0-9]{10}$",
      "bank_code_slice": [
        4,
        8
      ],
      "sepa": true,
      "example": "NL91ABNA0417164300"
    }
  ]
}
```

### GET /status

Healthcheck en metadata: servicestatus, versie, aantal landen in de registry en de gebruikte standaarden.

```bash
curl http://localhost:8006/status
```

**Response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "standards": [
    "ISO 13616",
    "ISO 7064 MOD 97-10"
  ],
  "countries_supported": 78,
  "max_bulk_items": 1000
}
```

## Standaard endpoints (van service template)

```bash
curl http://localhost:8006/health    # liveness probe
curl http://localhost:8006/ready     # readiness probe
curl http://localhost:8006/metrics   # Prometheus metrics
open http://localhost:8006/docs      # OpenAPI documentation
```


## Tests draaien

```bash
docker run --rm iban_validator_service python -m pytest tests/ -v
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
