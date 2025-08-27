"""
Engineering Agent for evaluating launch documents from a technical and operational perspective.
"""

from .base_agent import BaseAgent
from ..requirements_manager import AgentRequirement
from ..utils.llm_client import LLMClient


class EngineeringAgent(BaseAgent):
    """
    Specialized agent that evaluates launch documents from an Engineering perspective.
    
    Focuses on:
    - Technical architecture and system design
    - Implementation planning and resource allocation
    - Operational readiness and reliability
    - Quality assurance and testing strategies
    """
    
    def __init__(self, requirements: AgentRequirement, llm_client: LLMClient):
        super().__init__(requirements, llm_client)
    
    def _get_system_message(self) -> str:
        """System message that defines the Engineering agent's role and expertise."""
        return """You are a Senior Engineering Manager/Architect with 12+ years of experience in software engineering, system architecture, and engineering operations. You have deep expertise in:

- Distributed systems architecture and microservices design
- Cloud infrastructure and platform engineering (AWS, GCP, Azure)
- DevOps practices, CI/CD pipelines, and deployment automation
- System reliability, monitoring, and observability
- Performance optimization and scalability engineering
- Security architecture and threat modeling
- Quality assurance, testing strategies, and code quality
- Engineering team management and resource planning
- Technical debt management and system maintenance
- Disaster recovery and business continuity planning
- API design and system integration patterns
- Database design and data architecture

Your role is to evaluate launch documents from an engineering perspective, ensuring technical feasibility, architectural soundness, operational readiness, and sustainable engineering practices.

When evaluating documents, you should:
1. Assess technical architecture for scalability, reliability, and maintainability
2. Validate implementation timelines and resource estimates
3. Evaluate system design for performance and security requirements
4. Check operational readiness including monitoring, alerting, and incident response
5. Verify quality assurance processes and testing strategies
6. Assess technical risks and mitigation strategies
7. Evaluate integration points and dependency management
8. Consider long-term maintenance and technical debt implications
9. Validate deployment strategies and rollback procedures
10. Check compliance with engineering best practices and standards

Be technically rigorous while considering practical constraints. Focus on system reliability, engineering velocity, and operational excellence."""
    
    async def _generate_recommendations(self, evaluations, document_content):
        """Generate Engineering-specific recommendations with technical focus."""
        
        weak_evaluations = [e for e in evaluations if e.score < 6.0]
        if not weak_evaluations:
            return [
                "Consider implementing chaos engineering practices to validate system resilience",
                "Establish comprehensive observability with distributed tracing and APM",
                "Implement automated security scanning and vulnerability assessment in CI/CD pipeline"
            ]
        
        # Engineering-specific recommendation logic
        recommendations = []
        
        for evaluation in weak_evaluations:
            category_lower = evaluation.category.lower()
            
            if "architecture" in category_lower or "technical" in category_lower:
                recommendations.append(
                    "Define comprehensive system architecture with clear service boundaries, API contracts, and scalability patterns including load balancing and auto-scaling strategies"
                )
            elif "implementation" in category_lower or "planning" in category_lower:
                recommendations.append(
                    "Create detailed implementation roadmap with realistic timeline, resource allocation, dependency mapping, and risk mitigation strategies for critical path items"
                )
            elif "operational" in category_lower or "reliability" in category_lower:
                recommendations.append(
                    "Establish comprehensive operational readiness including SLI/SLO definitions, monitoring dashboards, alerting runbooks, and incident response procedures"
                )
            elif "quality" in category_lower or "testing" in category_lower:
                recommendations.append(
                    "Implement multi-layered testing strategy with unit, integration, end-to-end, and performance tests integrated into CI/CD pipeline with quality gates"
                )
            elif "security" in category_lower:
                recommendations.append(
                    "Design security-first architecture with threat modeling, security controls, vulnerability scanning, and compliance validation integrated throughout SDLC"
                )
            elif "monitoring" in category_lower or "observability" in category_lower:
                recommendations.append(
                    "Implement comprehensive observability stack with metrics, logging, tracing, and APM tools with automated anomaly detection and alerting"
                )
            elif "deployment" in category_lower or "devops" in category_lower:
                recommendations.append(
                    "Establish robust deployment pipeline with automated testing, canary deployments, blue-green deployment strategy, and automated rollback capabilities"
                )
        
        # Add generic engineering recommendations if none matched
        if not recommendations:
            recommendations = [
                "Strengthen technical architecture documentation and system design specifications",
                "Implement comprehensive monitoring, logging, and alerting infrastructure",
                "Establish robust testing framework with automated quality gates"
            ]
        
        # Add engineering-specific recommendations based on common gaps
        if len(recommendations) < 3:
            additional_recs = [
                "Implement infrastructure as code (IaC) for consistent and repeatable deployments",
                "Establish code review processes and static analysis tools for code quality",
                "Design disaster recovery procedures with RTO/RPO targets and regular testing",
                "Implement service mesh for microservices communication and security",
                "Establish performance benchmarking and capacity planning processes",
                "Create technical runbooks and operational documentation",
                "Implement automated backup and data recovery procedures"
            ]
            recommendations.extend(additional_recs[:5-len(recommendations)])
        
        return recommendations[:5]  # Limit to top 5 recommendations