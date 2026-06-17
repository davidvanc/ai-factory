# AI Software Factory

> Autonome multi-agent AI software factory. Geef een beschrijving, krijg een productie-klare microservice — gepusht naar GitHub.

Draait op **één machine**. Geen VM-cluster, geen queue, geen aparte diensten die altijd aan moeten staan. Je start het wanneer je het nodig hebt en sluit het daarna gewoon af.

Voor de volledige achtergrond zie `HANDOVER.md`. Voor de technische stand zie `PROJECT_STATE.md`.

---

## Wat het doet

Jij schrijft:

> "Maak een service die hex-kleuren omzet naar RGB en HSL"

Het systeem:

1. **Plant** de architectuur (Planner)
2. **Schrijft** de code (Developer)
3. **Bouwt** een Docker-image (Builder)
4. **Test** het (unit + integratie + functionele HTTP smoke tests) (Tester)
5. Laat een **AI-judge** het beoordelen (Judge)
6. **Pusht** naar GitHub als het goedgekeurd is
7. **Onthoudt** wat werkte en wat niet (lokale memory)

In ongeveer 2-4 minuten per service. Faalt een poging, dan stuurt het zichzelf bij met de testoutput als feedback en escaleert het op de laatste poging naar een premium model.

---

## Architectuur (één plaatje)

```
┌──────────────────────────────────────────────┐
│  Jouw machine                                 │
│                                               │
│  python main.py "Maak een service die X"      │
│        │                                      │
│        ▼                                      │
│  run_factory_pipeline()                       │
│    Planner → Developer → Builder              │
│           → Tester → Judge → git push         │
│                                               │
│  data/factory.db   ← lokale memory (SQLite)   │
│  Docker            ← bouwt + test de services │
│  (optioneel) Postgres via docker compose      │
└──────────────────────────────────────────────┘
```

Eén Python-proces doet alles synchroon. De vroegere Orchestrator/Worker/Storage-VM's en de Redis-queue zijn weg: dat was alleen nodig om taken parallel te verdelen, wat zinloos is voor een project dat je een paar keer per jaar draait.

---

## Vereisten

- **Python 3.11+**
- **Docker** (de Builder/Tester bouwt en draait Linux-containers; op Windows via Docker Desktop/WSL2)
- Een **OpenRouter API-key**
- **git**, geconfigureerd met een identiteit en push-rechten op je repo:

```bash
git config --global user.name "Jouw Naam"
git config --global user.email "jij@voorbeeld.com"
```

> Zonder ingestelde git-identiteit faalt de push (het systeem stopt dan luid met een duidelijke foutmelding).

---

## Eenmalige setup

```bash
git clone <jouw-repo-url> ai-factory
cd ai-factory

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
nano .env                        # vul OPENROUTER_API_KEY in
```

Dat is alles. De memory-database (`data/factory.db`) maakt zichzelf aan bij de eerste run.

> **Op een verse VM draaien?** Zie [`deploy/`](deploy/README.md): Terraform maakt een
> Ubuntu-VM (Proxmox of Azure) en Ansible installeert alles automatisch.

---

## Gebruik

```bash
source venv/bin/activate
python main.py "Maak een service met POST /reverse die een string omkeert"
```

Je ziet de pipeline live: elke fase print zijn naam, `OK`/`FAIL`-markeringen en de streamende LLM-output. Aan het eind krijg je een JSON-resultaat met status, projectpad en logbestand. Bij succes staat de service in `output/<naam>/` en is hij naar GitHub gepusht.

Extra context meegeven (bv. een specificatie of voorbeelddata)? Zet bestanden (`.md`, `.txt`, `.csv`, `.json`) in een `input/` map; ze worden automatisch aan de taak toegevoegd.

Opties:

```bash
python main.py "..." --max-tester-attempts 6 --max-judge-attempts 3
python main.py "..." --input ./mijn-context
```

---

## Een gegenereerde service draaien

```bash
cd output/<service_naam>
docker compose up --build
# in een tweede terminal:
curl http://localhost:<poort>/health      # {"status":"ok"}
```

De juiste poort en `curl`-voorbeelden staan in de `README.md` van elke gegenereerde service.

---

## Services die een database nodig hebben

Standaard staat de database uit (`DATABASE_ENABLED=false`). Heeft een gegenereerde service wél Postgres nodig, start dan de meegeleverde lokale Postgres — enkel zolang je hem gebruikt:

```bash
docker compose up -d postgres        # start lokale Postgres
# zet in .env: DATABASE_ENABLED=true en de DATABASE_URL (zie .env.example)
...
docker compose down                  # stop hem weer als je klaar bent
```

---

## Onderhoud

**Memory bekijken** (geschiedenis, lessen, poorten):

```bash
python -c "from src.llm.memory_client import MemoryClient; import json; print(json.dumps(MemoryClient().get_stats(), indent=2))"
```

De hele staat zit in één bestand: `data/factory.db`. Back-up = dat bestand kopiëren.

**Een nieuwe dependency toevoegen aan alle gegenereerde services**: bewerk `guaranteed_test_deps` in `src/agents/builder.py`.

**Een model wisselen per agent**: bewerk `MODEL_ROUTES` in `src/llm/client.py`.

**Een bestaand project opnieuw testen zonder de hele pipeline**:

```bash
python diagnose.py output/<service_naam>
```

---

## Troubleshooting

| Symptoom | Oorzaak | Oplossing |
|---|---|---|
| Pipeline "klaar" in enkele seconden | Crash, geen succes | Bekijk het laatste logbestand in `logs/` (`"status": "error"`) |
| `OPENROUTER_API_KEY niet gevonden` | `.env` niet ingevuld | Vul de key in en activeer de venv |
| Pipeline hangt lang op `streaming...` | LLM-stream vastgelopen | Ctrl+C; probeer opnieuw of wissel het model in `client.py` |
| `git push` faalt | git-identiteit/credentials | Stel `user.name`/`user.email` in en check je push-rechten |
| "Address already in use" | oude container draait nog | `docker ps -a \| grep ai-factory \| awk '{print $1}' \| xargs docker rm -f` |
| Schijf vol | oude Docker-images | `docker system prune -a` |

Per-run logs (inclusief incrementele voortgang) staan als JSON in `logs/`.
