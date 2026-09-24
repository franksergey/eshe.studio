from starlette_problem.cors import CorsConfiguration

cors_configuration = CorsConfiguration(
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
