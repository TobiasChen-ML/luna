import logging
from typing import Optional, Any

from app.services.llm_service import LLMService
from app.services.relationship_service import relationship_service
from app.models.relationship import RelationshipAnalysisResult

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analyze the following conversation and evaluate its impact on the relationship.

## Current Relationship State
- Relationship stage: {{relationship_stage}}
- Intimacy: {{intimacy}}
- Trust: {{trust}}
- Desire: {{desire}}
- Dependency: {{dependency}}

## Recent Conversation
{{recent_conversation}}

## Analysis Requirements
1. Determine the emotional sentiment of the conversation (positive/negative/neutral)
2. Evaluate the impact on each relationship attribute (-5 to +5)
3. Determine if a relationship stage transition should occur

## Output Format (JSON only, no other text)
{
  "sentiment": "positive|negative|neutral",
  "intimacy_change": 0,
  "trust_change": 0,
  "desire_change": 0,
  "dependency_change": 0,
  "stage_transition": null,
  "reasoning": "Brief explanation for the changes"
}
"""


class RelationshipAnalyzer:
    _instance = None
    
    def __init__(self):
        self.llm = LLMService.get_instance()
    
    @classmethod
    def get_instance(cls) -> "RelationshipAnalyzer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def analyze_conversation(
        self,
        relationship_stage: str,
        intimacy: float,
        trust: float,
        desire: float,
        dependency: float,
        conversation: list[dict[str, str]],
        user_id: Optional[str] = None,
        character_id: Optional[str] = None,
    ) -> RelationshipAnalysisResult:
        from jinja2 import Template
        
        conv_text = "\n".join([
            f"{msg.get('role', 'user')}: {msg.get('content', '')}"
            for msg in conversation
        ])
        
        prompt = Template(ANALYSIS_PROMPT).render(
            relationship_stage=relationship_stage,
            intimacy=intimacy,
            trust=trust,
            desire=desire,
            dependency=dependency,
            recent_conversation=conv_text,
        )
        
        try:
            response = await self.llm.generate_structured(
                messages=[{"role": "user", "content": prompt}],
                schema={
                    "type": "object",
                    "properties": {
                        "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                        "intimacy_change": {"type": "number", "minimum": -5, "maximum": 5},
                        "trust_change": {"type": "number", "minimum": -5, "maximum": 5},
                        "desire_change": {"type": "number", "minimum": -5, "maximum": 5},
                        "dependency_change": {"type": "number", "minimum": -5, "maximum": 5},
                        "stage_transition": {"type": ["string", "null"]},
                        "reasoning": {"type": "string"},
                    },
                    "required": ["sentiment", "intimacy_change", "trust_change", "desire_change", "dependency_change", "reasoning"],
                },
            )
            
            data = response.data or {}
            
            return RelationshipAnalysisResult(
                sentiment=data.get("sentiment", "neutral"),
                intimacy_change=float(data.get("intimacy_change", 0)),
                trust_change=float(data.get("trust_change", 0)),
                desire_change=float(data.get("desire_change", 0)),
                dependency_change=float(data.get("dependency_change", 0)),
                stage_transition=data.get("stage_transition"),
                reasoning=data.get("reasoning", ""),
            )
        
        except Exception as e:
            logger.error(
                f"Relationship analysis failed: user_id={user_id}, character_id={character_id}, "
                f"conversation_length={len(conversation)}, error={e}"
            )
            return RelationshipAnalysisResult()
    
    async def analyze_and_update(
        self,
        user_id: str,
        character_id: str,
        conversation: list[dict[str, str]],
    ) -> Optional[dict[str, Any]]:
        rel = await relationship_service.get_relationship(user_id, character_id)
        if not rel:
            rel = await relationship_service.get_or_create_relationship(user_id, character_id)
        
        if rel.get("is_locked"):
            logger.info(f"Relationship {user_id}/{character_id} is locked, skipping analysis")
            return None
        
        result = await self.analyze_conversation(
            relationship_stage=rel.get("stage", "stranger"),
            intimacy=rel.get("intimacy", 0),
            trust=rel.get("trust", 0),
            desire=rel.get("desire", 0),
            dependency=rel.get("dependency", 0),
            conversation=conversation,
            user_id=user_id,
            character_id=character_id,
        )
        
        logger.info(f"Analysis result: sentiment={result.sentiment}, changes=({result.intimacy_change}, {result.trust_change}, {result.desire_change}, {result.dependency_change})")
        
        updated = await relationship_service.update_attributes(
            user_id=user_id,
            character_id=character_id,
            intimacy_change=result.intimacy_change,
            trust_change=result.trust_change,
            desire_change=result.desire_change,
            dependency_change=result.dependency_change,
        )
        
        if updated:
            return {
                "intimacy": updated.get("intimacy"),
                "trust": updated.get("trust"),
                "desire": updated.get("desire"),
                "dependency": updated.get("dependency"),
                "stage": updated.get("stage"),
                "previous_stage": rel.get("stage"),
                "reasoning": result.reasoning,
                "sentiment": result.sentiment,
            }
        
        return None


relationship_analyzer = RelationshipAnalyzer()
