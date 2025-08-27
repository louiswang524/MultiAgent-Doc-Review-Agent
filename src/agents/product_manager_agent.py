"""
Product Manager Agent for evaluating launch documents from a business and product strategy perspective.
"""

from .base_agent import BaseAgent
from ..requirements_manager import AgentRequirement
from ..utils.llm_client import LLMClient


class ProductManagerAgent(BaseAgent):
    """
    Specialized agent that evaluates launch documents from a Product Manager perspective.
    
    Focuses on:
    - Market analysis and opportunity assessment
    - Product strategy and vision alignment
    - Business case and financial justification
    - Stakeholder alignment and execution planning
    """
    
    def __init__(self, requirements: AgentRequirement, llm_client: LLMClient):
        super().__init__(requirements, llm_client)
    
    def _get_system_message(self) -> str:
        """System message that defines the Product Manager agent's role and expertise."""
        return """You are an experienced Senior Product Manager with 10+ years of experience in product strategy, market analysis, and launch planning. You have a strong background in:

- Market research and competitive analysis
- Product strategy development and roadmapping
- Business case development and financial modeling
- Go-to-market planning and execution
- Stakeholder management and cross-functional collaboration
- Metrics definition and success measurement
- User research and customer validation

Your role is to evaluate launch documents from a product management perspective, focusing on business viability, market opportunity, strategic alignment, and execution feasibility.

When evaluating documents, you should:
1. Assess business and market fundamentals thoroughly
2. Look for data-driven decision making and quantitative analysis
3. Evaluate strategic thinking and long-term vision
4. Check for stakeholder alignment and clear ownership
5. Verify that success metrics and measurement plans are well-defined
6. Consider risks, assumptions, and mitigation strategies
7. Evaluate the go-to-market strategy and competitive positioning

Be thorough, analytical, and constructive in your feedback. Focus on practical business outcomes and strategic value."""
    
    async def _generate_recommendations(self, evaluations, document_content):
        """Generate PM-specific recommendations with business focus."""
        
        weak_evaluations = [e for e in evaluations if e.score < 6.0]
        if not weak_evaluations:
            return [
                "Consider conducting additional market validation to strengthen competitive positioning",
                "Ensure success metrics include both leading and lagging indicators",
                "Develop contingency plans for key assumptions and risks"
            ]
        
        # PM-specific recommendation logic
        recommendations = []
        
        for evaluation in weak_evaluations:
            if evaluation.category.lower().find("market") != -1:
                recommendations.append(
                    "Conduct comprehensive market sizing (TAM/SAM/SOM) with bottoms-up validation and competitive landscape analysis"
                )
            elif evaluation.category.lower().find("strategy") != -1 or evaluation.category.lower().find("product") != -1:
                recommendations.append(
                    "Clearly define product vision, value proposition, and strategic differentiation with measurable success criteria"
                )
            elif evaluation.category.lower().find("business") != -1 or evaluation.category.lower().find("financial") != -1:
                recommendations.append(
                    "Develop detailed business case with revenue projections, cost structure analysis, and ROI calculations with sensitivity analysis"
                )
            elif evaluation.category.lower().find("stakeholder") != -1:
                recommendations.append(
                    "Create stakeholder alignment framework with clear RACI matrix, communication plan, and decision-making process"
                )
        
        # Fallback to generic recommendations if none matched
        if not recommendations:
            recommendations = [f"Strengthen {e.category} with more detailed analysis and supporting data" for e in weak_evaluations[:3]]
        
        return recommendations[:5]  # Limit to top 5 recommendations