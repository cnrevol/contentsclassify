from abc import ABC, abstractmethod
from openai import OpenAI
from anthropic import Anthropic
import dashscope
from django.conf import settings
import logging
from transformers import BertForSequenceClassification, BertTokenizer
import torch
import fasttext
from openai import AzureOpenAI

logger = logging.getLogger('classifier')

class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_completion(self, system_message: str, user_message: str) -> dict:
        """Generate completion from LLM"""
        pass
# 
class OpenAIProvider(BaseLLMProvider):
    def __init__(self, config):
        self.client = AzureOpenAI(
            api_key=config.get('api_key', settings.AZ_OPENAI_API_KEY),
            api_version="2024-08-01-preview",
            azure_endpoint=config.get('base_url', settings.AZ_OPENAI_API_URL)
        )
        
        self.model_name = config.get('model_name', 'gpt-4o')  # Azure OpenAI 的模型名称格式
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)

    def generate_completion(self, system_message: str, user_message: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False
        )
        return response.choices[0].message.content
        
class ClaudeProvider(BaseLLMProvider):
    def __init__(self, config):
        self.client = Anthropic(api_key=config.get('api_key', settings.CLAUDE_API_KEY))
        self.model_name = config.get('model_name', 'claude-3-sonnet-20240229')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)

    def generate_completion(self, system_message: str, user_message: str) -> dict:
        response = self.client.messages.create(
            model=self.model_name,
            system=system_message,
            messages=[{"role": "user", "content": user_message}],
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        return response.content[0].text

class QwenProvider(BaseLLMProvider):
    def __init__(self, config):
        self.api_key = config.get('api_key', settings.QWEN_API_KEY)
        self.model_name = config.get('model_name', 'qwen-max')
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)

    def generate_completion(self, system_message: str, user_message: str) -> dict:
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        response = dashscope.Generation.call(
            model=self.model_name,
            messages=messages,
            api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            result_format='message'
        )
        return response.output.choices[0].message.content

class DoubaoProvider(BaseLLMProvider):
    def __init__(self, config):
        self.client = OpenAI(
            api_key=config.get('api_key', settings.ARK_API_KEY),
            base_url=config.get('base_url', settings.ARK_API_URL)
        )
        self.model_name = config.get('model_name', settings.ARK_MODEL_NAME)
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)

    def generate_completion(self, system_message: str, user_message: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False
        )
        return response.choices[0].message.content

class DeepseekProvider(BaseLLMProvider):
    def __init__(self, config):
        self.client = OpenAI(
            api_key=config.get('api_key', settings.DEEPSEEK_API_KEY),
            base_url=config.get('base_url', settings.DEEPSEEK_API_URL)
        )
        self.model_name = config.get('model_name', settings.DEEPSEEK_MODEL_NAME)
        self.temperature = config.get('temperature', 0.7)
        self.max_tokens = config.get('max_tokens', 1000)

    def generate_completion(self, system_message: str, user_message: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=False
        )
        return response.choices[0].message.content

class BertProvider(BaseLLMProvider):
    def __init__(self, config):
        model_path = config.get('model_path', settings.BERT_MODEL_PATH)
        logger.info(f"Loading BERT model from {model_path}")
        
        try:
            self.model = BertForSequenceClassification.from_pretrained(model_path)
            self.tokenizer = BertTokenizer.from_pretrained(model_path)
            self.model.eval()
            logger.info("BERT model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading BERT model: {str(e)}")
            raise

    def get_category_name(self, label_id):
        """根据标签ID获取类别名称"""
        return settings.BERT_LABEL_MAP.get(label_id, "none")

    def generate_completion(self, system_message: str, user_message: str) -> dict:
        try:
            # 处理输入文本
            encoding = self.tokenizer(
                user_message,
                add_special_tokens=True,
                max_length=128,
                padding='max_length',
                truncation=True,
                return_tensors='pt'
            )
            
            # 进行预测
            with torch.no_grad():
                outputs = self.model(
                    input_ids=encoding['input_ids'],
                    attention_mask=encoding['attention_mask']
                )
                prediction = torch.argmax(outputs.logits, dim=1)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
                confidence = probabilities[0][prediction].item()
                
                # 获取预测的类别名称
                category = self.get_category_name(prediction.item())
                
                logger.info(f"BERT prediction: {prediction.item()} label: {category} with confidence {confidence:.2%}")
                
                # 返回与其他 LLM 一致的字符串格式
                return f'''{{
                    "classification": "{category}",
                    "confidence": {confidence:.4f},
                    "explanation": "BERT model predicted {category} with {confidence:.2%} confidence",
                    "category_group_id": null,
                    "category_group_name": ""
                }}'''
                
        except Exception as e:
            logger.error(f"Error in BERT prediction: {str(e)}")
            return '''{{
                "classification": "unknown",
                "confidence": 0.0,
                "explanation": "Error in BERT prediction",
                "category_group_id": null,
                "category_group_name": ""
            }}'''

class FastTextProvider(BaseLLMProvider):
    def __init__(self, config):
        model_path = config.get('model_path', settings.FASTTEXT_MODEL_PATH)
        logger.info(f"Loading FastText model from {model_path}")
        
        try:
            self.model = fasttext.load_model(model_path)
            logger.info("FastText model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading FastText model: {str(e)}")
            raise

    def get_category_name(self, label: str) -> str:
        """Convert fasttext label to category name"""
        # FastText labels are in format '__label__category'
        label = label.replace('__label__', '')
        return settings.FASTTEXT_LABEL_MAP.get(label, "none")

    def generate_completion(self, system_message: str, user_message: str) -> dict:
        try:
            # FastText prediction
            user_message = user_message.strip().replace('\n', ' ').replace('\r', ' ')[:100]
            predictions = self.model.predict(user_message, k=1)  # Get top prediction
            labels, probabilities = predictions
            
            label = labels[0]  # Get first label
            confidence = probabilities[0]  # Get first probability
            
            # Get category name
            category = self.get_category_name(label)
            
            logger.info(f"FastText prediction: {label} ({category}) with confidence {confidence:.2%}")
            
            # Return in same format as other providers
            return f'''{{
                "classification": "{category}",
                "confidence": {confidence:.4f},
                "explanation": "FastText model predicted {category} with {confidence:.2%} confidence",
                "category_group_id": null,
                "category_group_name": ""
            }}'''
            
        except Exception as e:
            logger.error(f"Error in FastText prediction: {str(e)}")
            return '''{{
                "classification": "unknown",
                "confidence": 0.0,
                "explanation": "Error in FastText prediction",
                "category_group_id": null,
                "category_group_name": ""
            }}'''

# Factory for creating LLM providers
class LLMProviderFactory:
    _providers = {
        'openai': OpenAIProvider,
        # 'claude': ClaudeProvider,
        'qwen': QwenProvider,
        'doubao': DoubaoProvider,
        'deepseek': DeepseekProvider,
        'bert': BertProvider,
        'fasttext': FastTextProvider
    }

    @classmethod
    def create(cls, provider_name: str, config: dict) -> BaseLLMProvider:
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider_name}")
            
        # 获取提供者配置
        provider_config = settings.LLM_PROVIDERS.get(provider_name.lower())
        if not provider_config:
            raise ValueError(f"No configuration found for provider: {provider_name}")
            
        # 记录模型类型
        model_type = provider_config.get('model_type', 'llm')
        logger.info(f"Creating {model_type} provider: {provider_name}")
        
        return provider_class(config) 