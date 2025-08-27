"""
Interactive requirements setup wizard for easy configuration of agent requirements.
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .requirements_manager import RequirementsManager


@dataclass
class RequirementTemplate:
    """Template for a requirement category."""
    name: str
    description: str
    criteria: List[str]
    default_weight: int
    importance: str  # "essential", "important", "optional"


class RequirementsWizard:
    """Interactive wizard for setting up agent requirements."""
    
    def __init__(self):
        self.console = Console()
        self.requirements_manager = RequirementsManager()
        
        # Predefined templates for different focus areas
        self.pm_templates = self._get_pm_templates()
        self.ds_templates = self._get_ds_templates()
        self.eng_templates = self._get_eng_templates()
    
    def run_interactive_setup(self) -> str:
        """Run the interactive setup wizard."""
        self.console.print(Panel.fit("🧙 Requirements Setup Wizard", style="blue bold"))
        self.console.print("Let's create customized requirements for your launch document review.\n")
        
        # Get basic information
        doc_type = self._get_document_type()
        focus_areas = self._get_focus_areas()
        industry = self._get_industry()
        
        # Configure each agent
        pm_config = self._configure_agent("Product Manager", self.pm_templates, focus_areas)
        ds_config = self._configure_agent("Data Scientist", self.ds_templates, focus_areas)
        eng_config = self._configure_agent("Engineering", self.eng_templates, focus_areas)
        
        # Set scoring weights
        weights = self._configure_scoring_weights()
        
        # Generate requirements
        requirements = self._generate_requirements(
            doc_type, industry, pm_config, ds_config, eng_config, weights
        )
        
        # Save to file
        output_file = self._save_requirements(requirements)
        
        self.console.print(f"\n[green]✅ Requirements saved to: {output_file}[/green]")
        self.console.print("You can now use this file for document reviews!")
        
        return output_file
    
    def _get_document_type(self) -> str:
        """Get the type of document being reviewed."""
        self.console.print("[bold]Step 1: Document Type[/bold]")
        
        options = {
            "1": "Product Launch",
            "2": "Feature Release",
            "3": "Technical Specification",
            "4": "Business Proposal",
            "5": "Research Project",
            "6": "Custom"
        }
        
        table = Table(title="Document Types")
        table.add_column("Option", style="cyan")
        table.add_column("Type", style="white")
        
        for key, value in options.items():
            table.add_row(key, value)
        
        self.console.print(table)
        
        choice = Prompt.ask(
            "What type of document will you be reviewing?",
            choices=list(options.keys()),
            default="1"
        )
        
        if choice == "6":
            return Prompt.ask("Enter custom document type")
        
        return options[choice]
    
    def _get_focus_areas(self) -> List[str]:
        """Get the focus areas for the review."""
        self.console.print("\n[bold]Step 2: Focus Areas[/bold]")
        self.console.print("Select the areas most important for your review (you can choose multiple):")
        
        focus_options = [
            ("market", "Market Analysis & Strategy"),
            ("technical", "Technical Implementation"),
            ("data", "Data & Analytics"),
            ("business", "Business Case & Financials"),
            ("operations", "Operational Readiness"),
            ("compliance", "Compliance & Governance"),
            ("user", "User Experience & Research"),
            ("performance", "Performance & Scalability")
        ]
        
        selected_areas = []
        
        for key, description in focus_options:
            if Confirm.ask(f"Include {description}?", default=False):
                selected_areas.append(key)
        
        return selected_areas if selected_areas else ["market", "technical", "business"]
    
    def _get_industry(self) -> str:
        """Get the industry context."""
        self.console.print("\n[bold]Step 3: Industry Context[/bold]")
        
        industries = {
            "1": "Technology/Software",
            "2": "E-commerce/Retail",
            "3": "Financial Services",
            "4": "Healthcare/Medical",
            "5": "Manufacturing",
            "6": "Media/Entertainment",
            "7": "Education",
            "8": "Generic/Other"
        }
        
        table = Table(title="Industries")
        table.add_column("Option", style="cyan")
        table.add_column("Industry", style="white")
        
        for key, value in industries.items():
            table.add_row(key, value)
        
        self.console.print(table)
        
        choice = Prompt.ask(
            "What industry does this relate to?",
            choices=list(industries.keys()),
            default="8"
        )
        
        return industries[choice]
    
    def _configure_agent(self, agent_name: str, templates: List[RequirementTemplate], focus_areas: List[str]) -> Dict:
        """Configure requirements for a specific agent."""
        self.console.print(f"\n[bold]Step 4: {agent_name} Agent Configuration[/bold]")
        
        # Filter templates based on focus areas and importance
        relevant_templates = self._filter_templates(templates, focus_areas)
        
        # Show recommended categories
        self.console.print(f"[dim]Recommended categories for {agent_name}:[/dim]")
        for i, template in enumerate(relevant_templates[:3], 1):
            self.console.print(f"  {i}. {template.name} ({template.importance})")
        
        # Let user customize
        if Confirm.ask(f"Use recommended categories for {agent_name}?", default=True):
            selected_templates = relevant_templates[:3]
        else:
            selected_templates = self._manual_template_selection(templates)
        
        # Adjust weights
        return self._adjust_category_weights(selected_templates)
    
    def _filter_templates(self, templates: List[RequirementTemplate], focus_areas: List[str]) -> List[RequirementTemplate]:
        """Filter templates based on focus areas."""
        # Simple scoring based on focus areas
        scored_templates = []
        
        for template in templates:
            score = 0
            template_lower = template.name.lower()
            
            for focus in focus_areas:
                if focus in template_lower or any(focus in criterion.lower() for criterion in template.criteria):
                    score += 2 if template.importance == "essential" else 1
            
            scored_templates.append((score, template))
        
        # Sort by score and importance
        scored_templates.sort(key=lambda x: (x[0], x[1].importance == "essential"), reverse=True)
        return [template for score, template in scored_templates]
    
    def _manual_template_selection(self, templates: List[RequirementTemplate]) -> List[RequirementTemplate]:
        """Allow manual selection of templates."""
        self.console.print("\n[dim]Available categories:[/dim]")
        
        table = Table()
        table.add_column("ID", style="cyan")
        table.add_column("Category", style="white")
        table.add_column("Importance", style="yellow")
        table.add_column("Description", style="dim")
        
        for i, template in enumerate(templates, 1):
            table.add_row(
                str(i),
                template.name,
                template.importance,
                template.description[:50] + "..." if len(template.description) > 50 else template.description
            )
        
        self.console.print(table)
        
        selected = []
        while len(selected) < 5:  # Max 5 categories
            choice = Prompt.ask(
                f"Select category {len(selected) + 1} (enter number, or 'done' to finish)",
                default="done"
            )
            
            if choice.lower() == "done":
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(templates) and templates[idx] not in selected:
                    selected.append(templates[idx])
                else:
                    self.console.print("[red]Invalid selection or already selected[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number or 'done'[/red]")
        
        return selected
    
    def _adjust_category_weights(self, templates: List[RequirementTemplate]) -> Dict:
        """Adjust weights for selected categories."""
        if len(templates) <= 1:
            return {"categories": templates, "weights": {template.name: 100 for template in templates}}
        
        self.console.print(f"\n[dim]Adjusting weights for {len(templates)} categories (must sum to 100%)[/dim]")
        
        weights = {}
        remaining = 100
        
        for i, template in enumerate(templates):
            if i == len(templates) - 1:  # Last category gets remaining weight
                weights[template.name] = remaining
                self.console.print(f"{template.name}: [yellow]{remaining}%[/yellow] (remaining)")
            else:
                default_weight = min(template.default_weight, remaining - (len(templates) - i - 1))
                weight = IntPrompt.ask(
                    f"Weight for {template.name}",
                    default=default_weight
                )
                weight = min(weight, remaining - (len(templates) - i - 1))
                weights[template.name] = weight
                remaining -= weight
                self.console.print(f"{template.name}: [yellow]{weight}%[/yellow]")
        
        return {"categories": templates, "weights": weights}
    
    def _configure_scoring_weights(self) -> Dict[str, float]:
        """Configure weights between different agents."""
        self.console.print("\n[bold]Step 5: Agent Scoring Weights[/bold]")
        self.console.print("How much should each agent's evaluation contribute to the overall score?")
        
        presets = {
            "1": {"pm": 0.5, "ds": 0.25, "eng": 0.25, "desc": "Business-focused (PM heavy)"},
            "2": {"pm": 0.33, "ds": 0.33, "eng": 0.34, "desc": "Balanced across all agents"},
            "3": {"pm": 0.2, "ds": 0.3, "eng": 0.5, "desc": "Technical-focused (Engineering heavy)"},
            "4": {"pm": 0.3, "ds": 0.5, "eng": 0.2, "desc": "Data-driven (Data Science heavy)"},
            "5": {"pm": 0, "ds": 0, "eng": 0, "desc": "Custom weights"}
        }
        
        table = Table(title="Weight Presets")
        table.add_column("Option", style="cyan")
        table.add_column("PM", justify="center")
        table.add_column("DS", justify="center")
        table.add_column("Eng", justify="center")
        table.add_column("Description", style="dim")
        
        for key, preset in presets.items():
            if key != "5":
                table.add_row(
                    key,
                    f"{int(preset['pm']*100)}%",
                    f"{int(preset['ds']*100)}%",
                    f"{int(preset['eng']*100)}%",
                    preset['desc']
                )
            else:
                table.add_row(key, "-", "-", "-", preset['desc'])
        
        self.console.print(table)
        
        choice = Prompt.ask(
            "Select weight distribution",
            choices=list(presets.keys()),
            default="2"
        )
        
        if choice == "5":
            # Custom weights
            pm_weight = IntPrompt.ask("Product Manager weight (0-100)", default=40) / 100
            remaining = 100 - int(pm_weight * 100)
            ds_weight = IntPrompt.ask(f"Data Scientist weight (0-{remaining})", default=30) / 100
            eng_weight = (100 - int(pm_weight * 100) - int(ds_weight * 100)) / 100
            
            return {
                "product_manager": pm_weight,
                "data_scientist": ds_weight,
                "engineering": eng_weight
            }
        else:
            preset = presets[choice]
            return {
                "product_manager": preset["pm"],
                "data_scientist": preset["ds"],
                "engineering": preset["eng"]
            }
    
    def _generate_requirements(self, doc_type: str, industry: str, pm_config: Dict, 
                             ds_config: Dict, eng_config: Dict, weights: Dict) -> Dict:
        """Generate the final requirements structure."""
        
        agents = []
        
        # Product Manager
        if pm_config["categories"]:
            pm_requirements = []
            for template in pm_config["categories"]:
                pm_requirements.append({
                    "category": template.name,
                    "description": template.description,
                    "weight": pm_config["weights"][template.name],
                    "criteria": [{"name": criterion, "weight": 1.0} for criterion in template.criteria]
                })
            
            agents.append({
                "type": "product_manager",
                "name": "Product Manager Agent",
                "description": f"Evaluates {doc_type} from business and product strategy perspective",
                "requirements": pm_requirements
            })
        
        # Data Scientist
        if ds_config["categories"]:
            ds_requirements = []
            for template in ds_config["categories"]:
                ds_requirements.append({
                    "category": template.name,
                    "description": template.description,
                    "weight": ds_config["weights"][template.name],
                    "criteria": [{"name": criterion, "weight": 1.0} for criterion in template.criteria]
                })
            
            agents.append({
                "type": "data_scientist",
                "name": "Data Scientist Agent",
                "description": f"Evaluates data and analytics aspects of {doc_type}",
                "requirements": ds_requirements
            })
        
        # Engineering
        if eng_config["categories"]:
            eng_requirements = []
            for template in eng_config["categories"]:
                eng_requirements.append({
                    "category": template.name,
                    "description": template.description,
                    "weight": eng_config["weights"][template.name],
                    "criteria": [{"name": criterion, "weight": 1.0} for criterion in template.criteria]
                })
            
            agents.append({
                "type": "engineering",
                "name": "Engineering Agent",
                "description": f"Evaluates technical implementation and operational readiness of {doc_type}",
                "requirements": eng_requirements
            })
        
        return {
            "metadata": {
                "version": "1.0",
                "description": f"Custom requirements for {doc_type} review in {industry}",
                "document_type": doc_type,
                "industry": industry,
                "created_with": "Requirements Wizard",
                "last_updated": "auto-generated"
            },
            "agents": agents,
            "scoring": {
                "scale": "0-10",
                "weights": weights,
                "thresholds": {
                    "excellent": 8.5,
                    "good": 7.0,
                    "acceptable": 5.5,
                    "needs_improvement": 3.0
                }
            }
        }
    
    def _save_requirements(self, requirements: Dict) -> str:
        """Save requirements to file."""
        # Generate filename based on document type and industry
        doc_type = requirements["metadata"]["document_type"].lower().replace(" ", "-")
        industry = requirements["metadata"]["industry"].lower().replace("/", "-").replace(" ", "-")
        filename = f"requirements-{doc_type}-{industry}.yaml"
        
        output_path = Path(filename)
        
        # Make sure we don't overwrite
        counter = 1
        while output_path.exists():
            name_part = output_path.stem
            extension = output_path.suffix
            output_path = Path(f"{name_part}-{counter}{extension}")
            counter += 1
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(requirements, f, default_flow_style=False, sort_keys=False, indent=2)
        
        return str(output_path)
    
    def _get_pm_templates(self) -> List[RequirementTemplate]:
        """Get Product Manager requirement templates."""
        return [
            RequirementTemplate(
                name="Market Analysis",
                description="Assessment of market opportunity and competitive landscape",
                criteria=[
                    "Target market clearly defined with size and demographics",
                    "Competitive landscape analyzed with differentiation strategy",
                    "Market opportunity quantified with TAM/SAM/SOM",
                    "Customer personas identified with pain points and needs"
                ],
                default_weight=25,
                importance="essential"
            ),
            RequirementTemplate(
                name="Product Strategy",
                description="Product vision, goals, and strategic direction",
                criteria=[
                    "Product vision and value proposition clearly articulated",
                    "Success metrics and KPIs defined with baselines",
                    "Feature prioritization justified with user impact",
                    "Product roadmap aligned with business objectives"
                ],
                default_weight=25,
                importance="essential"
            ),
            RequirementTemplate(
                name="Business Case",
                description="Financial justification and business impact",
                criteria=[
                    "Revenue projections with realistic assumptions",
                    "Cost analysis including development and operational costs",
                    "Risk assessment with mitigation strategies",
                    "ROI calculations with timeline and break-even analysis"
                ],
                default_weight=25,
                importance="important"
            ),
            RequirementTemplate(
                name="Go-to-Market Strategy",
                description="Launch and marketing strategy",
                criteria=[
                    "Launch timeline with key milestones defined",
                    "Marketing channels and customer acquisition strategy",
                    "Pricing strategy with competitive analysis",
                    "Sales enablement and channel partner strategy"
                ],
                default_weight=15,
                importance="important"
            ),
            RequirementTemplate(
                name="Stakeholder Management",
                description="Stakeholder alignment and communication",
                criteria=[
                    "Key stakeholders identified with roles and responsibilities",
                    "Communication plan with regular updates and feedback loops",
                    "Decision-making process clearly defined",
                    "Change management strategy for organizational impact"
                ],
                default_weight=10,
                importance="optional"
            )
        ]
    
    def _get_ds_templates(self) -> List[RequirementTemplate]:
        """Get Data Scientist requirement templates."""
        return [
            RequirementTemplate(
                name="Data Requirements",
                description="Data sourcing, quality, and governance",
                criteria=[
                    "Data sources identified with availability and access methods",
                    "Data quality requirements and validation rules specified",
                    "Data governance framework with privacy and compliance",
                    "Data collection and storage strategy defined"
                ],
                default_weight=30,
                importance="essential"
            ),
            RequirementTemplate(
                name="Analytics Strategy",
                description="Measurement methodology and KPI framework",
                criteria=[
                    "Key metrics and KPIs clearly defined with business relevance",
                    "Measurement methodology with statistical rigor",
                    "Baseline establishment and target setting",
                    "Reporting frequency and stakeholder access defined"
                ],
                default_weight=25,
                importance="essential"
            ),
            RequirementTemplate(
                name="Experimentation Framework",
                description="A/B testing and experimental design",
                criteria=[
                    "Hypothesis formation with clear success criteria",
                    "Experimental design with proper controls and randomization",
                    "Sample size calculations and statistical power analysis",
                    "Results interpretation and decision-making framework"
                ],
                default_weight=20,
                importance="important"
            ),
            RequirementTemplate(
                name="Technical Implementation",
                description="Data infrastructure and analytics tooling",
                criteria=[
                    "Data pipeline architecture with ETL/ELT processes",
                    "Analytics tools and platforms selection",
                    "Real-time vs batch processing requirements",
                    "Scalability and performance considerations"
                ],
                default_weight=15,
                importance="important"
            ),
            RequirementTemplate(
                name="Machine Learning",
                description="ML models and predictive analytics",
                criteria=[
                    "Model requirements and performance targets",
                    "Training data availability and quality",
                    "Model validation and monitoring strategy",
                    "MLOps pipeline for model deployment and maintenance"
                ],
                default_weight=10,
                importance="optional"
            )
        ]
    
    def _get_eng_templates(self) -> List[RequirementTemplate]:
        """Get Engineering requirement templates."""
        return [
            RequirementTemplate(
                name="Technical Architecture",
                description="System design and technical specifications",
                criteria=[
                    "System architecture documented with component interactions",
                    "Technology stack justified with trade-offs explained",
                    "Scalability requirements and capacity planning",
                    "Security architecture with threat modeling"
                ],
                default_weight=30,
                importance="essential"
            ),
            RequirementTemplate(
                name="Implementation Plan",
                description="Development timeline and resource planning",
                criteria=[
                    "Development timeline with realistic estimates",
                    "Resource requirements and team allocation",
                    "Dependencies identified and managed",
                    "Risk mitigation strategies for technical challenges"
                ],
                default_weight=25,
                importance="essential"
            ),
            RequirementTemplate(
                name="Quality Assurance",
                description="Testing strategy and code quality",
                criteria=[
                    "Testing strategy with unit, integration, and E2E tests",
                    "Code quality standards and review processes",
                    "Performance testing and benchmarking",
                    "Security testing and vulnerability assessment"
                ],
                default_weight=20,
                importance="important"
            ),
            RequirementTemplate(
                name="Operational Readiness",
                description="Production deployment and monitoring",
                criteria=[
                    "Monitoring and alerting strategy with SLI/SLO definitions",
                    "Deployment strategy with rollback procedures",
                    "Incident response and on-call procedures",
                    "Capacity planning and auto-scaling configuration"
                ],
                default_weight=15,
                importance="important"
            ),
            RequirementTemplate(
                name="DevOps and Infrastructure",
                description="CI/CD and infrastructure management",
                criteria=[
                    "CI/CD pipeline with automated testing and deployment",
                    "Infrastructure as Code with version control",
                    "Environment management and configuration",
                    "Backup and disaster recovery procedures"
                ],
                default_weight=10,
                importance="optional"
            )
        ]


def run_requirements_wizard() -> str:
    """Convenience function to run the requirements wizard."""
    wizard = RequirementsWizard()
    return wizard.run_interactive_setup()