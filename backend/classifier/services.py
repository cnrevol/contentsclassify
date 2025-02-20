from django.conf import settings
from .models import CategoryGroup
from .llm_providers import LLMProviderFactory
import logging
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import ResponseSchema, StructuredOutputParser

logger = logging.getLogger('classifier')

class ContentClassificationService:
    def __init__(self, provider_name=None, provider_config=None):
        # Use default provider if none specified, with fallback to 'deepseek'
        self.provider_name = provider_name or getattr(settings, 'DEFAULT_LLM_PROVIDER', 'deepseek')
        logger.info(f"LLM default Provider is {self.provider_name} ")
        # Get provider configuration with fallback
        provider_settings = getattr(settings, 'LLM_PROVIDERS', {}).get(self.provider_name, {})
        if not provider_settings:
            logger.warning(f"Provider settings not found for {self.provider_name}, using defaults")
            provider_settings = {
                'default_model': 'deepseek-chat',
            }
        # Merge configurations
        self.config = {
            'model_name': provider_settings.get('default_model'),
            'temperature': 0.7,
            'max_tokens': 1000,
        }
        if provider_config:
            self.config.update(provider_config)
            
        # Initialize LLM provider
        try:
            self.llm_provider = LLMProviderFactory.create(self.provider_name, self.config)
        except ValueError as e:
            logger.error(f"Failed to create LLM provider {self.provider_name}, falling back to deepseek: {str(e)}")
            self.provider_name = 'deepseek'
            self.llm_provider = LLMProviderFactory.create(self.provider_name, self.config)
        
        # Define the output schema
        self.response_schemas = [
            ResponseSchema(
                name="classification",
                description="The classification category of the content",
                type="string"
            ),
            ResponseSchema(
                name="confidence",
                description="Confidence score between 0 and 1",
                type="float"
            ),
            ResponseSchema(
                name="explanation",
                description="Brief explanation of the classification",
                type="string"
            )
        ]
        
        self.output_parser = StructuredOutputParser.from_response_schemas(self.response_schemas)
        self.format_instructions = self.output_parser.get_format_instructions()

    def update_provider(self, provider_name: str, provider_config: dict = None):
        """
        Update the LLM provider
        
        Args:
            provider_name (str): Name of the provider to use
            provider_config (dict, optional): Configuration for the provider
        """
        self.provider_name = provider_name
        if provider_config:
            self.config.update(provider_config)

        logger.info(f"Update llm Provider to {self.provider_name} with config: {self.config}")
        self.llm_provider = LLMProviderFactory.create(provider_name, self.config)

    def get_active_category_groups(self):
        """Get all active category groups and their categories"""
        groups = CategoryGroup.objects.filter(is_active=True).prefetch_related('categories')
        return [(group, [category.name for category in group.categories.all()]) for group in groups]

    def classify_content(self, content, content_type):
        """
        Classify content using the configured LLM provider for each active category group
        
        Args:
            content (str): The text content to classify
            content_type (str): Type of the content (e.g., 'text', 'pdf', 'doc', etc.)
            
        Returns:
            list: List of classification results for each active group
        """
        logger.info(f"Starting content classification for type: {content_type}")
        results = []
        
        try:
            # Get all active category groups and their categories
            active_groups = self.get_active_category_groups()
            logger.info(f"Found {len(active_groups)} active category groups")
            
            # Classify content for each active group
            for group, available_categories in active_groups:
                logger.info(f"Processing classification for group {group.id}: {group.name}")
                try:
                    # Get provider configuration
                    provider_info = settings.LLM_PROVIDERS.get(self.provider_name, {})
                    model_type = provider_info.get('model_type', 'llm')
                    
                    # Generate response based on model type
                    if model_type == 'llm':
                        # Prepare the system message with classification instructions
                        system_message = f"""You are a content classification system. Your task is to classify the given content into appropriate categories.
                        Available classification categories:
                        {', '.join([f'- {cat}' for cat in available_categories])}
                        
                        Provide your response in the following format:
                        {self.format_instructions}
                        """
                        
                        # Prepare the user message with content to classify
                        content_preview = content[:100] + "..." if len(content) > 100 else content
                        user_message = f"""Content Type: {content_type}
                        Content: {content[:1000]}  # Limit content length
                        
                        Classify this content and provide:
                        1. The most appropriate classification category from the available categories
                        2. A confidence score between 0 and 1
                        3. A brief explanation for your classification"""
                    else:
                        # For non-LLM models (e.g., BERT), pass content directly
                        system_message = ""
                        user_message = content[:1000]  # Still limit content length
                    
                    # Get completion from provider
                    response_content = self.llm_provider.generate_completion(
                        system_message=system_message,
                        user_message=user_message
                    )
                    
                    # Parse the response
                    result = self.output_parser.parse(response_content)
                    result['category_group_id'] = group.id
                    result['category_group_name'] = group.name
                    # Add provider information
                    result['llm_provider'] = self.provider_name
                    result['llm_model'] = self.config.get('model_name', provider_info.get('default_model', 'unknown'))
                    
                    logger.info(f"Classification result for group {group.name}: category={result.get('classification')}, confidence={result.get('confidence')}")
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error classifying content for group {group.name}: {str(e)}", exc_info=True)
                    results.append({
                        "category_group_id": group.id,
                        "category_group_name": group.name,
                        "classification": "error",
                        "confidence": 0.0,
                        "explanation": f"Error during classification: {str(e)}",
                        "llm_provider": self.provider_name,
                        "llm_model": self.config.get('model_name', 'unknown')
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error during classification process: {str(e)}", exc_info=True)
            return [{
                "category_group_name": "Error",
                "classification": "unclassified",
                "confidence": 0.0,
                "explanation": f"Error during classification process: {str(e)}"
            }] 