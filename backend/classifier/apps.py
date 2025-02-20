from django.apps import AppConfig


class ClassifierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'classifier'
    # def ready(self):
    #     from django.conf import settings
    #     # Ensure LLM settings are available
    #     if not hasattr(settings, 'LLM_PROVIDERS'):
    #         settings.LLM_PROVIDERS = {
    #             'deepseek': {
    #                 'name': 'Deepseek',
    #                 'models': ['deepseek-chat'],
    #                 'default_model': 'deepseek-chat',
    #             }
    #         }
    #     if not hasattr(settings, 'DEFAULT_LLM_PROVIDER'):
    #         settings.DEFAULT_LLM_PROVIDER = 'deepseek'

