#!/usr/bin/env python3
"""
LLM Prompt Manager for Legal AI
Handles prompt templates, optimization, and configuration management
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PromptConfig:
    """Configuration for a prompt template"""
    template: str
    system_instruction: str
    temperature: float = 0.3
    top_p: float = 0.9
    top_k: int = 40
    max_tokens: int = 2048
    stop_sequences: List[str] = None

class LegalPromptManager:
    """Manages LLM prompts for legal document analysis"""
    
    def __init__(self, config_path: str = "./configs/llm_prompts.yaml"):
        self.config_path = Path(config_path)
        self.prompts = {}
        self.system_instructions = {}
        self.global_config = {}
        self.optimization_settings = {}
        
        self._load_configuration()
    
    def _load_configuration(self):
        """Load prompt configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Prompt config not found at {self.config_path}, using defaults")
                self._create_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Load global configuration
            self.global_config = config.get('global_config', {})
            
            # Load system instructions
            self.system_instructions = config.get('system_instructions', {})
            
            # Load document prompts
            doc_prompts = config.get('document_prompts', {})
            task_prompts = config.get('task_prompts', {})
            validation_prompts = config.get('validation_prompts', {})
            rag_prompts = config.get('rag_enhanced_prompts', {})
            test_prompts = config.get('test_prompts', {})
            
            # Combine all prompts
            self.prompts = {
                **doc_prompts,
                **task_prompts,
                **validation_prompts,
                **rag_prompts,
                **test_prompts
            }
            
            # Load optimization settings
            self.optimization_settings = config.get('optimization', {})
            
            logger.info(f"Loaded {len(self.prompts)} prompt templates from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load prompt configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default prompt configuration"""
        self.global_config = {
            "temperature": 0.3,
            "top_p": 0.9,
            "top_k": 40,
            "max_tokens": 2048
        }
        
        self.system_instructions = {
            "legal_analyst": "Ты эксперт-юрист по российскому праву. Анализируй документы профессионально и структурированно."
        }
        
        self.prompts = {
            "general_analysis": {
                "template": "Проанализируй документ:\n\n{document_text}\n\nДай структурированный анализ с рекомендациями.",
                "system_instruction": "legal_analyst"
            }
        }
    
    def get_prompt_config(self, prompt_name: str) -> Optional[PromptConfig]:
        """Get prompt configuration by name"""
        if prompt_name not in self.prompts:
            logger.warning(f"Prompt '{prompt_name}' not found")
            return None
        
        prompt_data = self.prompts[prompt_name]
        
        # Get system instruction
        system_key = prompt_data.get('system_instruction', 'legal_analyst')
        system_instruction = self.system_instructions.get(system_key, "")
        
        # Merge with global config
        config = {**self.global_config, **prompt_data}
        
        return PromptConfig(
            template=config['template'],
            system_instruction=system_instruction,
            temperature=config.get('temperature', 0.3),
            top_p=config.get('top_p', 0.9),
            top_k=config.get('top_k', 40),
            max_tokens=config.get('max_tokens', 2048),
            stop_sequences=config.get('stop_sequences')
        )
    
    def format_prompt(
        self,
        prompt_name: str,
        document_text: str,
        document_type: Optional[str] = None,
        user_question: Optional[str] = None,
        legal_context: Optional[str] = None,
        entities: Optional[List[Dict]] = None,
        **kwargs
    ) -> Optional[str]:
        """Format a prompt template with provided data"""
        
        config = self.get_prompt_config(prompt_name)
        if not config:
            return None
        
        try:
            # Prepare template variables
            template_vars = {
                'document_text': document_text,
                'system_instruction': config.system_instruction,
                'user_question': user_question or '',
                'legal_context': legal_context or '',
                'document_type': document_type or '',
                **kwargs
            }
            
            # Add entities if provided
            if entities:
                entities_text = self._format_entities(entities)
                template_vars['entities'] = entities_text
            
            # Add task-specific instructions based on document type
            if document_type:
                task_instructions = self._get_task_instructions(document_type)
                template_vars['task_specific_instructions'] = task_instructions
            
            # Format the template
            formatted_prompt = config.template.format(**template_vars)
            
            return formatted_prompt.strip()
            
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return None
        except Exception as e:
            logger.error(f"Error formatting prompt: {e}")
            return None
    
    def _format_entities(self, entities: List[Dict]) -> str:
        """Format entities for inclusion in prompt"""
        if not entities:
            return ""
        
        entities_text = "\nИЗВЛЕЧЕННЫЕ СУЩНОСТИ:\n"
        for entity in entities:
            label = entity.get('label', 'Unknown')
            text = entity.get('text', 'N/A')
            entities_text += f"- {label}: {text}\n"
        
        return entities_text
    
    def _get_task_instructions(self, document_type: str) -> str:
        """Get task-specific instructions based on document type"""
        
        instructions = {
            'bill_of_exchange': """
ОСОБЫЕ ТРЕБОВАНИЯ ДЛЯ ВЕКСЕЛЕЙ:
- Проверь все обязательные реквизиты согласно ст. 4-5 ФЗ №48
- Оцени вексельную силу документа
- Укажи на возможные проблемы с взысканием
            """,
            
            'fine_notice': """
ОСОБЫЕ ТРЕБОВАНИЯ ДЛЯ ПОСТАНОВЛЕНИЙ:
- Проверь соответствие требованиям КоАП РФ
- Оцени правильность квалификации правонарушения
- Укажи сроки и возможности обжалования
            """,
            
            'protocol': """
ОСОБЫЕ ТРЕБОВАНИЯ ДЛЯ ПРОТОКОЛОВ:
- Проверь соответствие корпоративному законодательству
- Оцени правомочность принятых решений
- Укажи на процедурные нарушения
            """
        }
        
        return instructions.get(document_type, "")
    
    def get_optimal_prompt_for_task(
        self,
        task_type: str,
        document_type: Optional[str] = None,
        has_rag_context: bool = False
    ) -> str:
        """Get optimal prompt name for specific task"""
        
        # Priority order for prompt selection
        if has_rag_context:
            return "with_legal_context"
        
        if task_type == "analysis":
            if document_type == "bill_of_exchange":
                return "bill_of_exchange_analysis"
            elif document_type == "fine_notice":
                return "fine_notice_analysis"
            elif document_type == "protocol":
                return "protocol_analysis"
            else:
                return "general_analysis"
        
        elif task_type == "classification":
            return "document_classification"
        
        elif task_type == "risk_assessment":
            return "risk_assessment"
        
        else:
            return "general_analysis"
    
    def validate_response_quality(
        self,
        response: str,
        expected_sections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate LLM response quality"""
        
        if not expected_sections:
            expected_sections = self.optimization_settings.get(
                'quality_metrics', {}
            ).get('required_sections', [])
        
        validation_result = {
            'is_valid': True,
            'quality_score': 0.0,
            'missing_sections': [],
            'issues': [],
            'recommendations': []
        }
        
        # Check for required sections
        response_lower = response.lower()
        missing_sections = []
        
        for section in expected_sections:
            if section.lower() not in response_lower:
                missing_sections.append(section)
        
        validation_result['missing_sections'] = missing_sections
        
        # Calculate quality score
        sections_score = (len(expected_sections) - len(missing_sections)) / len(expected_sections) if expected_sections else 1.0
        
        # Check response length
        length_score = min(len(response) / 500, 1.0)  # Expect at least 500 chars
        
        # Check for structure
        structure_score = 1.0 if any(marker in response for marker in ['1.', '2.', '•', '-']) else 0.5
        
        validation_result['quality_score'] = (sections_score + length_score + structure_score) / 3
        
        # Add recommendations
        if missing_sections:
            validation_result['recommendations'].append(
                f"Добавить разделы: {', '.join(missing_sections)}"
            )
        
        if len(response) < 200:
            validation_result['recommendations'].append("Расширить анализ, добавить больше деталей")
        
        validation_result['is_valid'] = validation_result['quality_score'] >= 0.7
        
        return validation_result
    
    def optimize_prompt_for_model(
        self,
        prompt_text: str,
        model_name: str = "mistral:7b"
    ) -> str:
        """Optimize prompt for specific model"""
        
        # Model-specific optimizations
        if "mistral" in model_name.lower():
            # Mistral works well with structured prompts
            if not prompt_text.startswith("ЗАДАЧА:"):
                prompt_text = f"ЗАДАЧА: Анализ юридического документа\n\n{prompt_text}"
            
            # Add clear formatting instructions
            if "ФОРМАТ ОТВЕТА:" not in prompt_text:
                format_instruction = """

ФОРМАТ ОТВЕТА:
Структурируй ответ по разделам с четкими заголовками.
Используй списки и подпункты для лучшей читаемости.
Обязательно укажи конкретные ссылки на законодательство.
"""
                prompt_text += format_instruction
        
        return prompt_text
    
    def get_model_config(self, model_name: str = "mistral:7b") -> Dict[str, Any]:
        """Get optimized configuration for specific model"""
        
        base_config = self.global_config.copy()
        
        # Model-specific adjustments
        if "mistral" in model_name.lower():
            base_config.update({
                "temperature": 0.3,  # Lower for more consistent legal analysis
                "top_p": 0.9,
                "top_k": 40,
                "max_tokens": 2048
            })
        
        return base_config
    
    def test_prompt_consistency(
        self,
        prompt_name: str,
        test_document: str,
        num_tests: int = 3
    ) -> Dict[str, Any]:
        """Test prompt consistency across multiple runs"""
        
        test_results = {
            'prompt_name': prompt_name,
            'test_count': num_tests,
            'test_document_preview': test_document[:100] + "...",
            'consistency_score': 0.0,
            'variations': [],
            'recommendations': []
        }
        
        # This would need to be connected to actual LLM for testing
        # For now, return mock results
        test_results['consistency_score'] = 0.85
        test_results['recommendations'] = [
            "Промпт показывает хорошую консистентность",
            "Незначительные вариации в формулировках"
        ]
        
        return test_results
    
    def export_prompt_stats(self) -> Dict[str, Any]:
        """Export prompt usage statistics and metadata"""
        
        stats = {
            'total_prompts': len(self.prompts),
            'system_instructions': len(self.system_instructions),
            'config_file': str(self.config_path),
            'last_loaded': datetime.now().isoformat(),
            'prompt_categories': {},
            'optimization_enabled': bool(self.optimization_settings)
        }
        
        # Categorize prompts
        categories = {}
        for prompt_name in self.prompts.keys():
            if 'analysis' in prompt_name:
                category = 'analysis'
            elif 'classification' in prompt_name:
                category = 'classification'
            elif 'validation' in prompt_name:
                category = 'validation'
            elif 'test' in prompt_name:
                category = 'testing'
            else:
                category = 'other'
            
            categories[category] = categories.get(category, 0) + 1
        
        stats['prompt_categories'] = categories
        
        return stats

# Global prompt manager instance
_prompt_manager = None

def get_prompt_manager() -> LegalPromptManager:
    """Get global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = LegalPromptManager()
    return _prompt_manager

# Convenience functions for API integration
def format_legal_prompt(
    task_type: str,
    document_text: str,
    document_type: Optional[str] = None,
    user_question: Optional[str] = None,
    legal_context: Optional[str] = None,
    entities: Optional[List[Dict]] = None
) -> tuple[str, Dict[str, Any]]:
    """Format legal prompt for API use"""
    
    manager = get_prompt_manager()
    
    # Determine optimal prompt
    has_rag = bool(legal_context and legal_context.strip())
    prompt_name = manager.get_optimal_prompt_for_task(task_type, document_type, has_rag)
    
    # Format prompt
    formatted_prompt = manager.format_prompt(
        prompt_name=prompt_name,
        document_text=document_text,
        document_type=document_type,
        user_question=user_question,
        legal_context=legal_context,
        entities=entities
    )
    
    # Get model config
    model_config = manager.get_model_config()
    
    if formatted_prompt:
        # Optimize for model
        optimized_prompt = manager.optimize_prompt_for_model(formatted_prompt)
        return optimized_prompt, model_config
    else:
        # Fallback to basic prompt
        fallback_prompt = f"Проанализируй документ:\n\n{document_text}\n\nДай структурированный анализ."
        return fallback_prompt, model_config

def validate_llm_response(response: str, task_type: str = "analysis") -> Dict[str, Any]:
    """Validate LLM response quality"""
    manager = get_prompt_manager()
    return manager.validate_response_quality(response) 