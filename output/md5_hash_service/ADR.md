# Architecture Decision Records: md5_hash_service

> ADRs documenteren de WAAROM achter de architectuurkeuzes.
> Niet de hoe (dat staat in de code), maar de redenering en alternatieven.

## ADR-001: Microservice met FastAPI

**Status:** Accepted
**Date:** 2026-05-06

### Context
Deze service is gegenereerd door de AI Software Factory met microservice-by-default architectuur.

### Decision
- HTTP REST microservice met FastAPI
- Pydantic voor request/response models
- Standaard service template voor observability/security
- Service-to-service communicatie via HTTP/JSON

### Consequences
- ✓ Standaard observability, auth, rate limiting "voor gratis"
- ✓ OpenAPI docs automatisch gegenereerd
- ✓ Eenvoudig te schalen (stateless)
- ✗ Iedere call gaat via HTTP (overhead vs in-process)
- ✗ Vereist orchestratie voor multi-service deployments

---

## ADR-002: Service template
**Status:** Accepted
**Date:** 2026-05-06

### Context
Elke service moet aan dezelfde productie-kwaliteit voldoen.

### Decision
Gemeenschappelijk service_template injected door de Builder, met:
- Structured JSON logging (structlog)
- Health (/health) + Readiness (/ready)
- Prometheus metrics (/metrics)
- Bearer token auth (opt-in)
- Rate limiting (opt-in, slowapi + Redis)
- Request ID tracing
- Security headers (X-Frame-Options, etc.)

### Consequences
- ✓ Geen boilerplate per service
- ✓ Uniforme observability over alle services
- ✗ Template updates vereisen rebuilds
- ✗ Extra dependencies (structlog, prometheus-client, slowapi)

---

## ADR-003: Endpoints in apart routes.py
**Status:** Accepted
**Date:** 2026-05-06

### Context
main.py moet bootstrap doen, niet business logic bevatten.

### Decision
- main.py: import bootstrap + business routers, instantieer app
- routes.py: APIRouter met alle business endpoints
- logic.py: business logic (puur Python, geen FastAPI imports)

### Consequences
- ✓ Tests kunnen logic.py testen zonder FastAPI mee te starten
- ✓ Routes apart van business logic = SOLID
- ✗ Eenvoudige services hebben extra files

---

## Toevoegen van nieuwe ADRs

Wanneer je een belangrijke architectuurkeuze maakt:
1. Kopieer een ADR sectie hierboven
2. Geef nummering: ADR-004, 005, etc.
3. Status: "Proposed" → "Accepted" → "Deprecated" (later)
4. Houd het kort: 4-5 zinnen per sectie volstaat

## Referenties

- [ADR documentation](https://adr.github.io/)
- [Michael Nygard's original article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
