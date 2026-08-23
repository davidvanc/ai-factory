from src.service_template.bootstrap import create_app
from src.routes import router as business_router

app = create_app(
    title="string_reverse_service",
    version="1.0.0",
    business_routers=[business_router],
)

# Ensure our custom /status endpoint takes precedence over the template's default one.
# The template registers a /status route first, which shadows the one in business_router.
# We filter out all /status routes except the last one (our custom one).
status_routes = [r for r in app.router.routes if getattr(r, "path", "") == "/status"]
if len(status_routes) > 1:
    app.router.routes = [
        r for r in app.router.routes 
        if getattr(r, "path", "") != "/status" or r == status_routes[-1]
    ]
