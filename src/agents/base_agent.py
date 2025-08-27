"""
Base agent class for launch document review agents.
Provides LLM-powered evaluation with structured prompts and scoring.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..requirements_manager import AgentRequirement, RequirementCategory
from ..utils.llm_client import LLMClient


@dataclass
class CategoryEvaluation:
    """Evaluation result for a single requirement category."""
    category: str
    score: float
    weight: float
    weighted_score: float
    reasoning: str
    strengths: List[str]
    weaknesses: List[str]
    missing_elements: List[str]


@dataclass
class AgentReview:
    """Complete review result from an agent."""
    agent_name: str
    agent_type: str
    overall_score: float
    category_evaluations: List[CategoryEvaluation]
    summary: str
    key_issues: List[str]
    recommendations: List[str]
    confidence_level: str


class BaseAgent(ABC):
    """Base class for all launch document review agents."""
    
    def __init__(self, requirements: AgentRequirement, llm_client: LLMClient):
        self.requirements = requirements
        self.llm_client = llm_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        self.agent_name = requirements.name
        self.agent_type = requirements.type
        self.requirement_categories = requirements.requirements
    
    async def review_document(self, document_content: str) -> AgentReview:
        """
        Main method to review a document against agent requirements.
        
        Args:
            document_content: The full text content of the launch document
            
        Returns:
            AgentReview: Complete evaluation results
        """
        self.logger.info(f"Starting document review with {self.agent_name}")
        
        # Evaluate each category
        category_evaluations = []
        total_weighted_score = 0.0
        
        for category in self.requirement_categories:
            evaluation = await self._evaluate_category(category, document_content)
            category_evaluations.append(evaluation)
            total_weighted_score += evaluation.weighted_score
        
        # Calculate overall score
        total_weight = sum(cat.weight for cat in self.requirement_categories)
        overall_score = min(10.0, (total_weighted_score / total_weight) * 10) if total_weight > 0 else 0.0
        
        # Generate summary and recommendations
        summary = await self._generate_summary(overall_score, category_evaluations, document_content)
        key_issues = self._identify_key_issues(category_evaluations)
        recommendations = await self._generate_recommendations(category_evaluations, document_content)
        confidence_level = self._assess_confidence(category_evaluations)
        
        return AgentReview(
            agent_name=self.agent_name,
            agent_type=self.agent_type,
            overall_score=round(overall_score, 2),
            category_evaluations=category_evaluations,
            summary=summary,
            key_issues=key_issues,
            recommendations=recommendations,
            confidence_level=confidence_level
        )
    
    async def _evaluate_category(self, category: RequirementCategory, document_content: str) -> CategoryEvaluation:
        """Evaluate a specific requirement category using LLM."""
        
        # Build evaluation prompt
        prompt = self._build_category_evaluation_prompt(category, document_content)
        system_message = self._get_system_message()
        
        try:
            # Get LLM evaluation
            response = await self.llm_client.generate_response(
                prompt=prompt,
                system_message=system_message,
                max_tokens=2000,
                temperature=0.2,
                response_format="json"
            )
            
            # Parse structured response
            evaluation_data = self.llm_client.parse_json_response(response)
            
            # Calculate weighted score
            score = float(evaluation_data.get("score", 0))
            weight = category.weight
            weighted_score = (score * weight) / 100  # Convert percentage weight to decimal
            
            return CategoryEvaluation(
                category=category.category,
                score=score,
                weight=weight,
                weighted_score=weighted_score,
                reasoning=evaluation_data.get("reasoning", ""),
                strengths=evaluation_data.get("strengths", []),
                weaknesses=evaluation_data.get("weaknesses", []),
                missing_elements=evaluation_data.get("missing_elements", [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate category {category.category}: {e}")
            # Return fallback evaluation
            return CategoryEvaluation(
                category=category.category,
                score=0.0,
                weight=category.weight,
                weighted_score=0.0,
                reasoning=f"Evaluation failed due to error: {str(e)}",
                strengths=[],
                weaknesses=["Unable to complete evaluation"],
                missing_elements=[]
            )
    
    def _build_category_evaluation_prompt(self, category: RequirementCategory, document_content: str) -> str:
        """Build the evaluation prompt for a specific category."""
        
        criteria_text = "\n".join([
            f"- {criterion.name}: {criterion.description or 'No description provided'}"
            for criterion in category.criteria
        ])
        
        prompt = f"""
You are evaluating a launch document against specific {self.agent_type} requirements.

CATEGORY TO EVALUATE: {category.category}
CATEGORY DESCRIPTION: {category.description or 'No description provided'}
CATEGORY WEIGHT: {category.weight}%

SPECIFIC CRITERIA TO ASSESS:
{criteria_text}

DOCUMENT CONTENT TO REVIEW:
{document_content}

Please evaluate how well this document meets the requirements for the "{category.category}" category.

Provide your evaluation in the following JSON format:
{{
    "score": <number between 0-10>,
    "reasoning": "<detailed explanation of your scoring rationale>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
    "missing_elements": ["<missing element 1>", "<missing element 2>", ...]
}}

SCORING GUIDELINES:
- 9-10: Exceptional - All criteria excellently addressed with comprehensive detail
- 7-8: Good - Most criteria well addressed with good detail  
- 5-6: Adequate - Some criteria addressed but lacks depth or completeness
- 3-4: Weak - Few criteria addressed, significant gaps
- 0-2: Poor - Major deficiencies, criteria largely unaddressed

Focus specifically on the criteria listed above. Be thorough but concise in your reasoning.
"""
        
        return prompt.strip()
    
    @abstractmethod
    def _get_system_message(self) -> str:
        """Get the system message that defines the agent's role and expertise."""
        pass
    
    async def _generate_summary(self, overall_score: float, evaluations: List[CategoryEvaluation], document_content: str) -> str:
        """Generate a high-level summary of the evaluation."""
        
        strong_categories = [e.category for e in evaluations if e.score >= 7.0]
        weak_categories = [e.category for e in evaluations if e.score < 5.0]
        
        if overall_score >= 8.0:
            summary_start = f"Excellent {self.agent_type} coverage"
        elif overall_score >= 6.0:
            summary_start = f"Good {self.agent_type} coverage with some gaps"
        elif overall_score >= 4.0:
            summary_start = f"Moderate {self.agent_type} coverage with significant gaps"
        else:
            summary_start = f"Insufficient {self.agent_type} coverage"
        
        details = []
        if strong_categories:
            details.append(f"Strong areas: {', '.join(strong_categories)}")
        if weak_categories:
            details.append(f"Needs improvement: {', '.join(weak_categories)}")
        
        summary = summary_start
        if details:
            summary += ". " + ". ".join(details) + "."
        
        return summary
    
    def _identify_key_issues(self, evaluations: List[CategoryEvaluation]) -> List[str]:
        """Identify the most critical issues from evaluations."""
        issues = []
        
        for evaluation in evaluations:
            if evaluation.score < 5.0:  # Poor performance
                issues.extend(evaluation.missing_elements[:2])  # Top 2 missing elements
                issues.extend(evaluation.weaknesses[:1])  # Top weakness
        
        # Deduplicate and limit to top 5 issues
        unique_issues = list(dict.fromkeys(issues))  # Preserves order while removing duplicates
        return unique_issues[:5]
    
    async def _generate_recommendations(self, evaluations: List[CategoryEvaluation], document_content: str) -> List[str]:
        """Generate actionable recommendations based on evaluation results."""
        
        weak_evaluations = [e for e in evaluations if e.score < 6.0]
        if not weak_evaluations:
            return ["Document meets most requirements well. Consider minor refinements based on specific feedback."]
        
        # Build recommendation prompt
        weak_areas = "\n".join([
            f"- {e.category} (Score: {e.score}): {', '.join(e.missing_elements[:2])}"
            for e in weak_evaluations
        ])
        
        prompt = f"""
Based on the following weak areas in a launch document from a {self.agent_type} perspective, provide 3-5 specific, actionable recommendations for improvement:

WEAK AREAS IDENTIFIED:
{weak_areas}

Provide recommendations as a JSON array of strings. Each recommendation should be:
1. Specific and actionable
2. Focused on the most critical gaps
3. Relevant to {self.agent_type} concerns
4. Concise but clear

Format: {{"recommendations": ["recommendation 1", "recommendation 2", ...]}}
"""
        
        try:
            response = await self.llm_client.generate_response(
                prompt=prompt,
                system_message=self._get_system_message(),
                max_tokens=1000,
                temperature=0.3,
                response_format="json"
            )
            
            recommendations_data = self.llm_client.parse_json_response(response)
            return recommendations_data.get("recommendations", [])
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            # Fallback recommendations
            return [f"Address gaps in {e.category}" for e in weak_evaluations[:3]]
    
    def _assess_confidence(self, evaluations: List[CategoryEvaluation]) -> str:
        """Assess confidence level of the overall evaluation."""
        
        # Simple heuristic based on score distribution
        scores = [e.score for e in evaluations]
        avg_score = sum(scores) / len(scores) if scores else 0
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 0
        
        # High confidence: consistent scores (low variance)
        # Medium confidence: moderate variance
        # Low confidence: high variance or very low scores
        
        if score_variance < 1.0 and avg_score > 4.0:
            return "High"
        elif score_variance < 4.0 and avg_score > 2.0:
            return "Medium"
        else:
            return "Low"