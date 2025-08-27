"""
Requirements management system for loading and validating agent requirements from YAML files.
"""

import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, Field, validator


class RequirementCriterion(BaseModel):
    """Individual criterion within a requirement category."""
    name: str
    description: Optional[str] = None
    weight: float = 1.0
    
    @validator('weight')
    def weight_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Weight must be positive')
        return v


class RequirementCategory(BaseModel):
    """Category of requirements with multiple criteria."""
    category: str
    description: Optional[str] = None
    criteria: List[RequirementCriterion]
    weight: float = Field(default=25.0, ge=0, le=100)
    
    @validator('criteria')
    def must_have_criteria(cls, v):
        if not v:
            raise ValueError('Category must have at least one criterion')
        return v


class AgentRequirement(BaseModel):
    """Requirements specification for a single agent."""
    type: str
    name: str
    description: str
    requirements: List[RequirementCategory]
    
    @validator('requirements')
    def must_have_requirements(cls, v):
        if not v:
            raise ValueError('Agent must have at least one requirement category')
        return v


class ScoringConfig(BaseModel):
    """Scoring configuration for the review system."""
    scale: str = "0-10"
    weights: Dict[str, float] = Field(default_factory=dict)
    thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "excellent": 8.5,
        "good": 7.0,
        "acceptable": 5.5,
        "needs_improvement": 3.0
    })


class RequirementsSpec(BaseModel):
    """Complete requirements specification."""
    metadata: Dict[str, Any]
    agents: List[AgentRequirement]
    scoring: ScoringConfig


class RequirementsManager:
    """Manages loading, validation, and access to requirements specifications."""
    
    def __init__(self):
        self.requirements: Optional[RequirementsSpec] = None
        self._file_path: Optional[Path] = None
    
    def load_requirements(self, file_path: str) -> RequirementsSpec:
        """Load requirements from YAML file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Requirements file not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            self.requirements = RequirementsSpec(**data)
            self._file_path = path
            return self.requirements
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
        except Exception as e:
            raise ValueError(f"Failed to load requirements: {e}")
    
    def get_agent_requirements(self, agent_type: str) -> AgentRequirement:
        """Get requirements for a specific agent type."""
        if not self.requirements:
            raise ValueError("Requirements not loaded. Call load_requirements() first.")
        
        for agent in self.requirements.agents:
            if agent.type == agent_type:
                return agent
        
        raise ValueError(f"Agent type '{agent_type}' not found in requirements")
    
    def get_all_agents(self) -> List[AgentRequirement]:
        """Get all agent requirements."""
        if not self.requirements:
            raise ValueError("Requirements not loaded. Call load_requirements() first.")
        
        return self.requirements.agents
    
    def get_scoring_config(self) -> ScoringConfig:
        """Get scoring configuration."""
        if not self.requirements:
            raise ValueError("Requirements not loaded. Call load_requirements() first.")
        
        return self.requirements.scoring
    
    def create_sample_requirements(self, file_path: str) -> str:
        """Create a sample requirements file."""
        sample_data = {
            "metadata": {
                "version": "1.0",
                "description": "Launch document review requirements for multi-agent system",
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "created_by": "Launch Doc Reviewer System"
            },
            "agents": [
                {
                    "type": "product_manager",
                    "name": "Product Manager Agent",
                    "description": "Evaluates business strategy, market fit, and product requirements",
                    "requirements": [
                        {
                            "category": "Market Analysis",
                            "description": "Assessment of market opportunity and competitive landscape",
                            "weight": 25,
                            "criteria": [
                                {
                                    "name": "Target Market Definition",
                                    "description": "Clear definition of target market segments and size",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Competitive Analysis",
                                    "description": "Analysis of competitive landscape and differentiation",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Market Opportunity",
                                    "description": "Quantification of market size and growth potential",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Customer Personas",
                                    "description": "Well-defined customer personas and use cases",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Product Strategy",
                            "description": "Product vision, goals, and strategic direction",
                            "weight": 25,
                            "criteria": [
                                {
                                    "name": "Product Vision",
                                    "description": "Clear product vision and value proposition",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Success Metrics",
                                    "description": "Well-defined KPIs and success criteria",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Feature Prioritization",
                                    "description": "Justified feature prioritization and roadmap",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Go-to-Market Strategy",
                                    "description": "Comprehensive go-to-market plan",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Business Case",
                            "description": "Financial justification and business impact",
                            "weight": 25,
                            "criteria": [
                                {
                                    "name": "Revenue Projections",
                                    "description": "Realistic revenue forecasts and assumptions",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Cost Analysis",
                                    "description": "Comprehensive cost structure and analysis",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Risk Assessment",
                                    "description": "Identification and mitigation of key risks",
                                    "weight": 1.0
                                },
                                {
                                    "name": "ROI Calculation",
                                    "description": "Return on investment calculations and timeline",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Stakeholder Alignment",
                            "description": "Stakeholder management and alignment strategy",
                            "weight": 25,
                            "criteria": [
                                {
                                    "name": "Stakeholder Identification",
                                    "description": "Complete identification of key stakeholders",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Approval Process",
                                    "description": "Clear sign-off and approval process",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Communication Plan",
                                    "description": "Comprehensive communication strategy",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Timeline and Milestones",
                                    "description": "Clear project timeline with key milestones",
                                    "weight": 1.0
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "data_scientist",
                    "name": "Data Scientist Agent",
                    "description": "Evaluates data requirements, analytics strategy, and measurement plans",
                    "requirements": [
                        {
                            "category": "Data Requirements",
                            "description": "Data sourcing, quality, and governance requirements",
                            "weight": 30,
                            "criteria": [
                                {
                                    "name": "Data Sources",
                                    "description": "Clear identification of required data sources",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Data Quality Standards",
                                    "description": "Defined data quality requirements and validation",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Data Governance",
                                    "description": "Data governance framework and policies",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Privacy and Compliance",
                                    "description": "Privacy protection and regulatory compliance",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Analytics Strategy",
                            "description": "Measurement methodology and statistical approach",
                            "weight": 30,
                            "criteria": [
                                {
                                    "name": "Key Metrics Definition",
                                    "description": "Well-defined primary and secondary metrics",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Measurement Methodology",
                                    "description": "Clear measurement and analysis methodology",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Statistical Considerations",
                                    "description": "Statistical significance and power analysis",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Experimentation Strategy",
                                    "description": "A/B testing and experimentation framework",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Technical Implementation",
                            "description": "Data infrastructure and technical architecture",
                            "weight": 25,
                            "criteria": [
                                {
                                    "name": "Data Pipeline Architecture",
                                    "description": "Scalable data pipeline design and architecture",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Analytics Tools",
                                    "description": "Selection of appropriate analytics tools and platforms",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Processing Requirements",
                                    "description": "Real-time vs batch processing requirements",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Scalability Planning",
                                    "description": "Scalability considerations and capacity planning",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Reporting and Insights",
                            "description": "Reporting strategy and stakeholder access",
                            "weight": 15,
                            "criteria": [
                                {
                                    "name": "Dashboard Requirements",
                                    "description": "Dashboard and visualization requirements",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Automated Alerting",
                                    "description": "Automated alerting and monitoring strategy",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Visualization Standards",
                                    "description": "Data visualization standards and best practices",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Access Controls",
                                    "description": "Stakeholder access permissions and security",
                                    "weight": 1.0
                                }
                            ]
                        }
                    ]
                },
                {
                    "type": "engineering",
                    "name": "Engineering Agent",
                    "description": "Evaluates technical architecture, implementation plan, and operational readiness",
                    "requirements": [
                        {
                            "category": "Technical Architecture",
                            "description": "System design and technical specifications",
                            "weight": 30,
                            "criteria": [
                                {
                                    "name": "System Architecture",
                                    "description": "Well-documented system architecture and design",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Technology Stack",
                                    "description": "Justified technology choices and stack selection",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Scalability Requirements",
                                    "description": "Scalability requirements and capacity planning",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Security Considerations",
                                    "description": "Security architecture and threat modeling",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Implementation Plan",
                            "description": "Development planning and resource allocation",
                            "weight": 25,
                            "criteria": [
                                {
                                    "name": "Development Timeline",
                                    "description": "Realistic development timeline and phases",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Resource Requirements",
                                    "description": "Clear resource and team requirements",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Dependency Management",
                                    "description": "Identification and management of dependencies",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Testing Strategy",
                                    "description": "Comprehensive testing strategy and coverage",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Operational Readiness",
                            "description": "Production deployment and operational considerations",
                            "weight": 25,
                            "criteria": [
                                {
                                    "name": "Monitoring Strategy",
                                    "description": "Comprehensive monitoring and alerting strategy",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Deployment Procedures",
                                    "description": "Deployment and rollback procedures",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Performance Benchmarks",
                                    "description": "Performance requirements and benchmarks",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Disaster Recovery",
                                    "description": "Disaster recovery and business continuity plan",
                                    "weight": 1.0
                                }
                            ]
                        },
                        {
                            "category": "Quality Assurance",
                            "description": "Code quality and testing standards",
                            "weight": 20,
                            "criteria": [
                                {
                                    "name": "Code Quality Standards",
                                    "description": "Defined code quality standards and practices",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Test Coverage",
                                    "description": "Automated testing coverage and quality gates",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Security Testing",
                                    "description": "Security testing and vulnerability assessment",
                                    "weight": 1.0
                                },
                                {
                                    "name": "Performance Testing",
                                    "description": "Performance testing strategy and benchmarks",
                                    "weight": 1.0
                                }
                            ]
                        }
                    ]
                }
            ],
            "scoring": {
                "scale": "0-10",
                "weights": {
                    "product_manager": 0.4,
                    "data_scientist": 0.3,
                    "engineering": 0.3
                },
                "thresholds": {
                    "excellent": 8.5,
                    "good": 7.0,
                    "acceptable": 5.5,
                    "needs_improvement": 3.0
                }
            }
        }
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(sample_data, f, default_flow_style=False, sort_keys=False, indent=2)
            
            return str(path)
        except Exception as e:
            raise ValueError(f"Failed to create sample requirements: {e}")
    
    def validate_requirements(self) -> bool:
        """Validate the loaded requirements."""
        if not self.requirements:
            raise ValueError("No requirements loaded")
        
        # Validation is handled by Pydantic models
        # Additional custom validation can be added here if needed
        
        # Check that agent weights sum to reasonable total
        total_weight = sum(self.requirements.scoring.weights.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Agent weights should sum to 1.0, got {total_weight}")
        
        return True