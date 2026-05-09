from src.service_template.bootstrap import create_app
from src.routes import router as business_router

app = create_app(
    title="movie_search_service",
    version="0.1.0",
    business_routers=[business_router],
)
