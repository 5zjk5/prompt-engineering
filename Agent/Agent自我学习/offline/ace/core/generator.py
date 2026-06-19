"""
Generator agent for ACE system.
Generates answers to questions using playbook and reflection.
"""

import json
import re
from typing import Dict, List, Tuple, Optional, Any
from Agent.Agent自我学习.offline import logger
from Agent.Agent自我学习.offline.ace.prompts.generator import GENERATOR_PROMPT
from Agent.Agent自我学习.offline.ace.llm import timed_llm_call

class Generator:
    """
    Generator agent that produces answers to questions using knowledge
    from a playbook and previous reflections.
    """
    
    def __init__(self, model, logger, max_tokens: int = 4096):
        """
        Initialize the Generator agent.
        
        Args:
            api_client: OpenAI client for LLM calls
            api_provider: API provider for LLM calls
            model: Model name to use for generation
            max_tokens: Maximum tokens for generation
        """
        self.model = model
        self.max_tokens = max_tokens
        self.logger = logger
    
    def generate(
        self,
        question: str,
        playbook: str,
        reflection: str = "(empty)",
        use_json_mode: bool = False,
        call_id: str = "gen",
        log_dir: Optional[str] = None
    ) -> Tuple[str, List[str], Dict[str, Any]]:
        """
        Generate an answer to a question using the playbook.
        
        Args:
            question: The question to answer
            playbook: The current playbook content
            reflection: Previous reflection content
            use_json_mode: Whether to use JSON mode
            call_id: Unique identifier for this call
            log_dir: Directory for logging
            
        Returns:
            Tuple of (full_response, bullet_ids_used, call_info)
        """
        # Format the prompt
        prompt = GENERATOR_PROMPT.format(playbook=playbook, reflection=reflection, question=question)
        
        response, call_info = timed_llm_call(
            model=self.model,
            prompt=prompt,
            role="generator",
            call_id=call_id,
            max_tokens=self.max_tokens,
            log_dir=log_dir,
            use_json_mode=use_json_mode,
            logger=self.logger
        )
        
        # Extract bullet IDs if using retrieval and reason mode
        bullet_ids = []
        bullet_ids = self._extract_bullet_ids(response, use_json_mode)
        
        return response, bullet_ids, call_info
    
    def _extract_bullet_ids(self, response: str, use_json_mode: bool) -> List[str]:
        """
        Extract bullet IDs from generator response.
        
        Args:
            response: The generator's response
            use_json_mode: Whether JSON mode was used
            
        Returns:
            List of bullet IDs
        """
        bullet_ids = []
        
        if use_json_mode:
            try:
                response_json = json.loads(response)
                bullet_ids = response_json.get("bullet_ids", [])
            except (json.JSONDecodeError, KeyError):
                # If parsing fails, try regex extraction
                bullet_ids = self._extract_bullet_ids_regex(response)
        else:
            bullet_ids = self._extract_bullet_ids_regex(response)
        
        return bullet_ids
    
    def _extract_bullet_ids_regex(self, text: str) -> List[str]:
        """
        Extract bullet IDs using regex pattern matching.
        
        Args:
            text: Text to extract bullet IDs from
            
        Returns:
            List of bullet IDs
        """
        # Pattern matches: [xxx-00001], [abc-00042], etc.
        pattern = r'\[([a-z]{3,}-\d{5})\]'
        matches = re.findall(pattern, text)
        return matches