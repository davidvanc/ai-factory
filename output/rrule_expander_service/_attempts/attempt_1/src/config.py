from src.service_template.settings import Settings

class AppSettings(Settings):
    max_results: int = 10000
    max_batch_items: int = 100

settings = AppSettings()
