from fastapi.templating import Jinja2Templates
from starlette_problem.cors import CorsConfiguration

from server.config import settings

cors_configuration = CorsConfiguration(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory=settings.api.templates)
