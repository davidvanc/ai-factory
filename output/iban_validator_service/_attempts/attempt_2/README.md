# iban_validator_service

HTTP microservice die IBAN-rekeningnummers valideert en formatteert volgens ISO 13616. Bevat landspecifieke lengte- en formaatcontrole op basis van een centrale data-tabel (registry), mod-97 checksumvalidatie (ISO 7064), formattering in print- en compactvorm, en een bulk-endpoint dat een lijst IBANs per item onafhankelijk verwerkt zodat één ongeldig item de batch nooit laat crashen.

## Lokaal draaien

```bash
docker build -t iban_validator_service .
docker run --rm -p 8006:8006 iban_validator_service
```

De service draait dan op http://localhost:8006


## Endpoints en testcommando's

### GET /status

Healthcheck en metadata: service status, versie en aantal ondersteunde landen in de registry.

```bash
curl -X GET http://localhost:8006/status
```

**Response:**
```json
{
  "status": "ok",
  "service": "iban_validator_service",
  "version": "1.0.0",
  "spec": "ISO 13616 / ISO 7064 mod-97-10",
  "supported_countries": 78
}
```

### POST /validate

Valideert één IBAN: normalisatie (spaties/lowercase), structuurcheck, landspecifieke lengte- en formaatcheck uit de registry, en mod-97 checksum. Retourneert altijd HTTP 200 met valid true/false en een lijst foutcodes (alleen structureel onjuiste request-body geeft 422).

```bash
curl -X POST http://localhost:8006/validate -H 'Content-Type: application/json' -d '{"iban": "NL91 ABNA 0417 1643 00"}'
```

**Response:**
```json
{
  "input": "NL91 ABNA 0417 1643 00",
  "valid": true,
  "country_code": "NL",
  "check_digits": "91",
  "bban": "ABNA0417164300",
  "length": 18,
  "expected_length": 18,
  "checksum_mod97": 1,
  "formatted": "NL91 ABNA 0417 1643 00",
  "compact": "NL91ABNA0417164300",
  "bank_identifier": "ABNA",
  "branch_identifier": null,
  "account_number": "0417164300",
  "errors": []
}
```

### GET /validate

Validatie van één IBAN via query parameter, handig voor snelle checks en browsergebruik. Zelfde responsemodel als POST /validate.

```bash
curl -X GET 'http://localhost:8006/validate?iban=DE89370400440532013000'
```

**Response:**
```json
{
  "input": "DE89370400440532013000",
  "valid": true,
  "country_code": "DE",
  "check_digits": "89",
  "bban": "370400440532013000",
  "length": 22,
  "expected_length": 22,
  "checksum_mod97": 1,
  "formatted": "DE89 3704 0044 0532 0130 00",
  "compact": "DE89370400440532013000",
  "bank_identifier": "37040044",
  "branch_identifier": null,
  "account_number": "0532013000",
  "errors": []
}
```

### POST /format

Formatteert een IBAN naar 'print' (groepen van 4 gescheiden door spaties), 'compact' (geen scheidingstekens) of 'electronic' (alias van compact). Formattering wordt ook uitgevoerd bij niet-valide checksum, maar valid-vlag geeft de validatiestatus mee.

```bash
curl -X POST http://localhost:8006/format -H 'Content-Type: application/json' -d '{"iban": "nl91abna0417164300", "style": "print"}'
```

**Response:**
```json
{
  "input": "nl91abna0417164300",
  "style": "print",
  "formatted": "NL91 ABNA 0417 1643 00",
  "compact": "NL91ABNA0417164300",
  "valid": true,
  "errors": []
}
```

### POST /validate/bulk

Verwerkt een lijst IBANs in één request. Elk item wordt volledig geïsoleerd verwerkt (try/except per item): een ongeldig, leeg of niet-string item levert een per-item resultaat met status 'invalid'/'error' op zonder de rest van de batch te blokkeren. Response bevat index-behoudende resultaten plus een samenvatting.

```bash
curl -X POST http://localhost:8006/validate/bulk -H 'Content-Type: application/json' -d '{"ibans": ["NL91ABNA0417164300", "DE89 3704 0044 0532 0130 00", "NL91ABNA0417164301", "XX00INVALID", "FR761234"], "style": "print", "fail_fast": false}'
```

**Response:**
```json
{
  "count": 5,
  "summary": {
    "valid": 2,
    "invalid": 3,
    "errors": 0
  },
  "results": [
    {
      "index": 0,
      "input": "NL91ABNA0417164300",
      "status": "valid",
      "valid": true,
      "country_code": "NL",
      "formatted": "NL91 ABNA 0417 1643 00",
      "compact": "NL91ABNA0417164300",
      "length": 18,
      "expected_length": 18,
      "errors": []
    },
    {
      "index": 1,
      "input": "DE89 3704 0044 0532 0130 00",
      "status": "valid",
      "valid": true,
      "country_code": "DE",
      "formatted": "DE89 3704 0044 0532 0130 00",
      "compact": "DE89370400440532013000",
      "length": 22,
      "expected_length": 22,
      "errors": []
    },
    {
      "index": 2,
      "input": "NL91ABNA0417164301",
      "status": "invalid",
      "valid": false,
      "country_code": "NL",
      "formatted": "NL91 ABNA 0417 1643 01",
      "compact": "NL91ABNA0417164301",
      "length": 18,
      "expected_length": 18,
      "errors": [
        {
          "code": "CHECKSUM_FAILED",
          "message": "mod-97 checksum is niet gelijk aan 1"
        }
      ]
    },
    {
      "index": 3,
      "input": "XX00INVALID",
      "status": "invalid",
      "valid": false,
      "country_code": "XX",
      "formatted": "XX00 INVA LID",
      "compact": "XX00INVALID",
      "length": 11,
      "expected_length": null,
      "errors": [
        {
          "code": "UNKNOWN_COUNTRY",
          "message": "Landcode 'XX' staat niet in de ISO 13616 registry"
        }
      ]
    },
    {
      "index": 4,
      "input": "FR761234",
      "status": "invalid",
      "valid": false,
      "country_code": "FR",
      "formatted": "FR76 1234",
      "compact": "FR761234",
      "length": 8,
      "expected_length": 27,
      "errors": [
        {
          "code": "INVALID_LENGTH",
          "message": "Lengte 8 wijkt af van verwachte lengte 27 voor land FR"
        }
      ]
    }
  ]
}
```

### GET /countries

Retourneert de volledige landspecifieke registry (data-tabel) met verwachte totale lengte, BBAN-formaatpatroon en SEPA-vlag. Maakt de regels inspecteerbaar en testbaar zonder in de logica te kijken.

```bash
curl -X GET http://localhost:8006/countries
```

**Response:**
```json
{
  "count": 78,
  "countries": [
    {
      "country_code": "NL",
      "name": "Netherlands",
      "iban_length": 18,
      "bban_pattern": "4!a10!n",
      "bban_regex": "^[A-Z]{4}[0-9]{10}$",
      "sepa": true,
      "example": "NL91ABNA0417164300"
    },
    {
      "country_code": "DE",
      "name": "Germany",
      "iban_length": 22,
      "bban_pattern": "18!n",
      "bban_regex": "^[0-9]{18}$",
      "sepa": true,
      "example": "DE89370400440532013000"
    }
  ]
}
```

### GET /countries/{country_code}

Retourneert de registry-regel voor één landcode (case-insensitive). 404 als de landcode niet bestaat in de ISO 13616 registry.

```bash
curl -X GET http://localhost:8006/countries/BE
```

**Response:**
```json
{
  "country_code": "BE",
  "name": "Belgium",
  "iban_length": 16,
  "bban_pattern": "12!n",
  "bban_regex": "^[0-9]{12}$",
  "sepa": true,
  "example": "BE68539007547034"
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
