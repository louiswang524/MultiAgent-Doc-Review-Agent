"""
Main launch document reviewer orchestrator that coordinates multiple agents.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .requirements_manager import RequirementsManager, ScoringConfig
from .utils.llm_client import LLMClientFactory
from .utils.google_docs_client import GoogleDocsClient
from .agents.product_manager_agent import ProductManagerAgent
from .agents.data_scientist_agent import DataScientistAgent
from .agents.engineering_agent import EngineeringAgent
from .agents.base_agent import AgentReview


@dataclass
class ReviewResult:
    """Complete review result from all agents."""
    document_url: str
    document_title: str
    review_timestamp: datetime
    overall_score: float
    agent_reviews: List[AgentReview]
    scoring_config: ScoringConfig
    summary: str
    confidence_level: str
    key_recommendations: List[str]


class LaunchDocReviewer:
    """Main orchestrator for launch document reviews."""
    
    def __init__(
        self,
        llm_provider: Optional[str] = None,
        llm_model: Optional[str] = None,
        base_url: Optional[str] = None,
        google_credentials_path: Optional[str] = None
    ):
        """
        Initialize the launch document reviewer.
        
        Args:
            llm_provider: LLM provider ('openai', 'anthropic', 'ollama', 'local')
            llm_model: Specific model to use
            base_url: Base URL for local LLM services
            google_credentials_path: Path to Google API credentials
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM client
        try:
            self.llm_client = LLMClientFactory.create_client(llm_provider, llm_model, base_url)
            self.logger.info(f"Initialized LLM client: {self.llm_client.get_provider_info()}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {e}")
            raise
        
        # Initialize Google Docs client
        try:
            self.docs_client = GoogleDocsClient(google_credentials_path)
            self.logger.info("Initialized Google Docs client")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google Docs client: {e}")
            raise
        
        # Initialize requirements manager
        self.requirements_manager = RequirementsManager()
        self.agents = {}
    
    async def review_document(self, document_url: str, requirements_file: str) -> ReviewResult:
        """
        Perform complete review of a launch document.
        
        Args:
            document_url: Google Docs URL
            requirements_file: Path to requirements YAML file
            
        Returns:
            Complete review result
        """
        self.logger.info(f"Starting document review for: {document_url}")
        
        # Load requirements
        requirements = self.requirements_manager.load_requirements(requirements_file)
        self.logger.info(f"Loaded requirements with {len(requirements.agents)} agents")
        
        # Initialize agents
        await self._initialize_agents()
        
        # Fetch document content
        self.logger.info("Fetching document content...")
        document_content = await self.docs_client.fetch_document_content(document_url)
        document_info = self.docs_client.get_document_info(document_url)
        
        self.logger.info(f"Fetched document: {len(document_content)} characters")
        
        # Run agent reviews in parallel
        self.logger.info("Running agent reviews...")
        agent_reviews = await self._run_agent_reviews(document_content)
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(agent_reviews, requirements.scoring)
        
        # Generate summary and recommendations
        summary = await self._generate_overall_summary(agent_reviews, overall_score)
        key_recommendations = self._consolidate_recommendations(agent_reviews)
        confidence_level = self._assess_overall_confidence(agent_reviews)
        
        # Create review result
        result = ReviewResult(
            document_url=document_url,
            document_title=document_info.get('title', 'Unknown Document'),
            review_timestamp=datetime.now(),
            overall_score=overall_score,
            agent_reviews=agent_reviews,
            scoring_config=requirements.scoring,
            summary=summary,
            confidence_level=confidence_level,
            key_recommendations=key_recommendations
        )
        
        self.logger.info(f"Review completed. Overall score: {overall_score:.2f}")
        return result
    
    async def _initialize_agents(self):
        """Initialize all agents based on loaded requirements."""
        self.agents = {}
        
        for agent_req in self.requirements_manager.get_all_agents():
            if agent_req.type == "product_manager":
                agent = ProductManagerAgent(agent_req, self.llm_client)
            elif agent_req.type == "data_scientist":
                agent = DataScientistAgent(agent_req, self.llm_client)
            elif agent_req.type == "engineering":
                agent = EngineeringAgent(agent_req, self.llm_client)
            else:
                self.logger.warning(f"Unknown agent type: {agent_req.type}")
                continue
            
            self.agents[agent_req.type] = agent
            self.logger.info(f"Initialized {agent_req.name}")
    
    async def _run_agent_reviews(self, document_content: str) -> List[AgentReview]:
        """Run all agent reviews in parallel."""
        tasks = []
        
        for agent_type, agent in self.agents.items():
            task = asyncio.create_task(
                agent.review_document(document_content),
                name=f"review_{agent_type}"
            )
            tasks.append(task)
        
        # Wait for all reviews to complete
        reviews = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        successful_reviews = []
        for i, result in enumerate(reviews):
            if isinstance(result, Exception):
                agent_type = list(self.agents.keys())[i]
                self.logger.error(f"Agent {agent_type} failed: {result}")
                # Create a fallback review
                fallback_review = self._create_fallback_review(agent_type, str(result))
                successful_reviews.append(fallback_review)
            else:
                successful_reviews.append(result)
        
        return successful_reviews
    
    def _create_fallback_review(self, agent_type: str, error_message: str) -> AgentReview:
        """Create a fallback review when an agent fails."""
        return AgentReview(
            agent_name=f"{agent_type.title()} Agent",
            agent_type=agent_type,
            overall_score=0.0,
            category_evaluations=[],
            summary=f"Review failed due to error: {error_message}",
            key_issues=[f"Agent evaluation failed: {error_message}"],
            recommendations=["Please check system configuration and try again"],
            confidence_level="Low"
        )
    
    def _calculate_overall_score(self, agent_reviews: List[AgentReview], scoring_config: ScoringConfig) -> float:
        """Calculate weighted overall score across all agents."""
        if not agent_reviews:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for review in agent_reviews:
            weight = scoring_config.weights.get(review.agent_type, 0.0)
            total_weighted_score += review.overall_score * weight
            total_weight += weight
        
        if total_weight == 0:
            # Fallback to equal weighting
            return sum(review.overall_score for review in agent_reviews) / len(agent_reviews)
        
        return round(total_weighted_score, 2)
    
    async def _generate_overall_summary(self, agent_reviews: List[AgentReview], overall_score: float) -> str:
        """Generate an overall summary across all agent reviews."""
        
        # Collect key insights from each agent
        agent_summaries = []
        for review in agent_reviews:
            agent_summaries.append(f"{review.agent_name}: {review.summary}")
        
        # Determine overall assessment
        thresholds = self.requirements_manager.get_scoring_config().thresholds
        
        if overall_score >= thresholds.get("excellent", 8.5):
            assessment = "Excellent"
        elif overall_score >= thresholds.get("good", 7.0):
            assessment = "Good"
        elif overall_score >= thresholds.get("acceptable", 5.5):
            assessment = "Acceptable"
        else:
            assessment = "Needs Improvement"
        
        summary = f"{assessment} launch document readiness (Score: {overall_score}/10). "
        
        # Add agent-specific insights
        strong_agents = [r.agent_name for r in agent_reviews if r.overall_score >= 7.0]
        weak_agents = [r.agent_name for r in agent_reviews if r.overall_score < 5.0]
        
        if strong_agents:
            summary += f"Strong coverage from {', '.join(strong_agents)} perspective(s). "
        
        if weak_agents:
            summary += f"Significant improvements needed from {', '.join(weak_agents)} perspective(s). "
        
        return summary.strip()
    
    def _consolidate_recommendations(self, agent_reviews: List[AgentReview]) -> List[str]:
        """Consolidate recommendations from all agents."""
        all_recommendations = []
        
        for review in agent_reviews:
            # Add top recommendations from each agent
            for rec in review.recommendations[:2]:  # Top 2 from each agent
                if rec not in all_recommendations:  # Avoid duplicates
                    all_recommendations.append(f"[{review.agent_type.upper()}] {rec}")
        
        return all_recommendations[:8]  # Limit to top 8 overall
    
    def _assess_overall_confidence(self, agent_reviews: List[AgentReview]) -> str:
        """Assess overall confidence level."""
        confidence_scores = {"High": 3, "Medium": 2, "Low": 1}
        
        if not agent_reviews:
            return "Low"
        
        # Calculate average confidence
        total_confidence = sum(confidence_scores.get(review.confidence_level, 1) for review in agent_reviews)
        avg_confidence = total_confidence / len(agent_reviews)
        
        if avg_confidence >= 2.5:
            return "High"
        elif avg_confidence >= 1.5:
            return "Medium"
        else:
            return "Low"
    
    def format_review_results(self, result: ReviewResult) -> str:
        """Format review results for display."""
        lines = []
        lines.append("="*80)
        lines.append("LAUNCH DOCUMENT REVIEW RESULTS")
        lines.append("="*80)
        lines.append(f"Document: {result.document_title}")
        lines.append(f"URL: {result.document_url}")
        lines.append(f"Review Date: {result.review_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Overall Score: {result.overall_score}/10")
        lines.append(f"Assessment: {result.summary}")
        lines.append(f"Confidence: {result.confidence_level}")
        lines.append("")
        
        # Agent-specific results
        lines.append("DETAILED AGENT REVIEWS:")
        lines.append("-" * 40)
        
        for review in result.agent_reviews:
            lines.append(f"\n{review.agent_name.upper()} (Score: {review.overall_score}/10)")
            lines.append(f"Summary: {review.summary}")
            
            if review.key_issues:
                lines.append(f"Key Issues: {', '.join(review.key_issues)}")
            
            if review.category_evaluations:
                lines.append("Category Scores:")
                for cat_eval in review.category_evaluations:
                    lines.append(f"  • {cat_eval.category}: {cat_eval.score}/10")
        
        # Recommendations
        if result.key_recommendations:
            lines.append("\nKEY RECOMMENDATIONS:")
            lines.append("-" * 20)
            for i, rec in enumerate(result.key_recommendations, 1):
                lines.append(f"{i}. {rec}")
        
        lines.append("\n" + "="*80)
        
        return "\n".join(lines)