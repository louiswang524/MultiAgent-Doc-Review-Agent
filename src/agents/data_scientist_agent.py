"""
Data Scientist Agent for evaluating launch documents from a data and analytics perspective.
"""

from .base_agent import BaseAgent
from ..requirements_manager import AgentRequirement
from ..utils.llm_client import LLMClient


class DataScientistAgent(BaseAgent):
    """
    Specialized agent that evaluates launch documents from a Data Scientist perspective.
    
    Focuses on:
    - Data requirements and quality standards
    - Analytics strategy and measurement methodology
    - Technical implementation of data systems
    - Reporting, insights, and data governance
    """
    
    def __init__(self, requirements: AgentRequirement, llm_client: LLMClient):
        super().__init__(requirements, llm_client)
    
    def _get_system_message(self) -> str:
        """System message that defines the Data Scientist agent's role and expertise."""
        return """You are a Senior Data Scientist with 8+ years of experience in analytics, machine learning, and data infrastructure. You have deep expertise in:

- Data architecture and pipeline design
- Statistical analysis and experimental design
- A/B testing and causal inference methodologies
- Machine learning model development and deployment
- Data quality assurance and governance frameworks
- Analytics strategy and KPI definition
- Business intelligence and data visualization
- Privacy regulations and data compliance (GDPR, CCPA, etc.)
- Real-time and batch data processing systems
- Statistical significance testing and power analysis

Your role is to evaluate launch documents from a data science and analytics perspective, ensuring that data requirements, measurement strategies, and technical implementation plans are robust and feasible.

When evaluating documents, you should:
1. Assess data availability, quality, and governance requirements
2. Validate measurement methodology and statistical rigor
3. Evaluate the feasibility of proposed analytics architecture
4. Check for proper experimental design and hypothesis testing
5. Verify data privacy and compliance considerations
6. Assess scalability and performance requirements
7. Evaluate reporting and visualization strategies
8. Look for proper baseline establishment and success criteria
9. Consider data pipeline reliability and monitoring
10. Validate metric definitions and measurement accuracy

Be technically rigorous while considering business practicality. Focus on statistical validity, data quality, and sustainable analytics practices."""
    
    async def _generate_recommendations(self, evaluations, document_content):
        """Generate Data Science-specific recommendations with technical focus."""
        
        weak_evaluations = [e for e in evaluations if e.score < 6.0]
        if not weak_evaluations:
            return [
                "Consider implementing automated data quality monitoring and alerting",
                "Establish baseline measurements and statistical power analysis for key metrics",
                "Develop data lineage documentation and impact analysis procedures"
            ]
        
        # DS-specific recommendation logic
        recommendations = []
        
        for evaluation in weak_evaluations:
            category_lower = evaluation.category.lower()
            
            if "data requirement" in category_lower or "data quality" in category_lower:
                recommendations.append(
                    "Define comprehensive data quality framework with validation rules, monitoring dashboards, and automated alerting for data anomalies"
                )
            elif "analytics" in category_lower or "measurement" in category_lower:
                recommendations.append(
                    "Establish rigorous measurement methodology with proper statistical testing, sample size calculations, and confidence intervals for all key metrics"
                )
            elif "technical" in category_lower or "implementation" in category_lower:
                recommendations.append(
                    "Design scalable data architecture with clear ETL/ELT processes, real-time streaming capabilities, and proper data versioning"
                )
            elif "reporting" in category_lower or "insight" in category_lower:
                recommendations.append(
                    "Implement self-service analytics platform with automated reporting, interactive dashboards, and role-based access controls"
                )
            elif "experiment" in category_lower or "test" in category_lower:
                recommendations.append(
                    "Develop comprehensive A/B testing framework with proper randomization, stratification, and statistical significance testing"
                )
            elif "privacy" in category_lower or "compliance" in category_lower:
                recommendations.append(
                    "Implement data privacy-by-design with anonymization, consent management, and compliance monitoring for GDPR/CCPA requirements"
                )
        
        # Add generic technical recommendations if none matched
        if not recommendations:
            recommendations = [
                "Strengthen data validation and quality assurance processes",
                "Implement proper statistical methodology for measurement and testing",
                "Design robust data pipeline architecture with monitoring and alerting"
            ]
        
        # Add data-specific recommendations based on common gaps
        if len(recommendations) < 3:
            additional_recs = [
                "Establish data lineage tracking and impact analysis for all data sources",
                "Implement automated anomaly detection for key business metrics",
                "Create data documentation and metadata management system",
                "Design disaster recovery and backup strategies for critical data assets",
                "Establish data retention policies and archival procedures"
            ]
            recommendations.extend(additional_recs[:5-len(recommendations)])
        
        return recommendations[:5]  # Limit to top 5 recommendations