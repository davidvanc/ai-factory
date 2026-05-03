from src.service_template.bootstrap import create_app
from src.routes import router as business_router

app = create_app(
    title="Password Generator Service",
    version="0.1.0",
    business_routers=[business_router],
)

# Fix for OpenAPI email validation error with .local domain in newer Pydantic versions
if hasattr(app, "contact") and isinstance(app.contact, dict):
    if app.contact.get("email") == "ops@ai-factory.local":
        app.contact["email"] = "ops@ai-factory.com"
