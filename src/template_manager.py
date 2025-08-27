"""
Template manager for handling predefined requirements templates.
"""

import os
import yaml
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel


@dataclass
class RequirementTemplate:
    """Represents a requirements template."""
    name: str
    description: str
    document_type: str
    difficulty: str
    file_path: str
    metadata: Dict


class TemplateManager:
    """Manages predefined requirements templates."""
    
    def __init__(self):
        self.console = Console()
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.templates = self._load_templates()
    
    def _load_templates(self) -> List[RequirementTemplate]:
        """Load all available templates from the templates directory."""
        templates = []
        
        if not self.templates_dir.exists():
            return templates
        
        for template_file in self.templates_dir.glob("requirements-*.yaml"):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                metadata = data.get('metadata', {})
                template = RequirementTemplate(
                    name=metadata.get('template_name', template_file.stem),
                    description=metadata.get('description', 'No description available'),
                    document_type=metadata.get('document_type', 'Unknown'),
                    difficulty=metadata.get('difficulty', 'intermediate'),
                    file_path=str(template_file),
                    metadata=metadata
                )
                templates.append(template)
                
            except Exception as e:
                print(f"Warning: Could not load template {template_file}: {e}")
        
        return sorted(templates, key=lambda t: (t.difficulty, t.name))
    
    def list_templates(self) -> List[RequirementTemplate]:
        """Get all available templates."""
        return self.templates
    
    def display_templates(self):
        """Display available templates in a nice format."""
        if not self.templates:
            self.console.print("[yellow]No templates found. You can create requirements from scratch.[/yellow]")
            return
        
        self.console.print(Panel.fit("📋 Available Requirements Templates", style="blue bold"))
        
        table = Table(title="Requirements Templates")
        table.add_column("ID", style="cyan", width=4)
        table.add_column("Name", style="white", width=22)
        table.add_column("Type", style="green", width=15)
        table.add_column("Level", style="yellow", width=12)
        table.add_column("Industry", style="magenta", width=12)
        table.add_column("Description", style="dim")
        
        for i, template in enumerate(self.templates, 1):
            difficulty_color = {
                'beginner': 'green',
                'intermediate': 'yellow', 
                'advanced': 'red'
            }.get(template.difficulty, 'white')
            
            industry = template.metadata.get('industry', 'General').replace('_', ' ').title()
            
            table.add_row(
                str(i),
                template.name,
                template.document_type,
                f"[{difficulty_color}]{template.difficulty}[/{difficulty_color}]",
                industry,
                template.description[:50] + "..." if len(template.description) > 50 else template.description
            )
        
        self.console.print(table)
    
    def get_template_by_id(self, template_id: int) -> Optional[RequirementTemplate]:
        """Get a template by its display ID."""
        if 1 <= template_id <= len(self.templates):
            return self.templates[template_id - 1]
        return None
    
    def get_template_by_name(self, name: str) -> Optional[RequirementTemplate]:
        """Get a template by name."""
        for template in self.templates:
            if template.name.lower() == name.lower():
                return template
        return None
    
    def load_template_requirements(self, template: RequirementTemplate) -> Dict:
        """Load the full requirements from a template."""
        try:
            with open(template.file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise ValueError(f"Could not load template {template.name}: {e}")
    
    def create_custom_template(self, name: str, description: str, requirements: Dict) -> str:
        """Create a new template from requirements."""
        # Generate filename from name
        filename = f"requirements-{name.lower().replace(' ', '-')}.yaml"
        template_path = self.templates_dir / filename
        
        # Ensure templates directory exists
        self.templates_dir.mkdir(exist_ok=True)
        
        # Add metadata
        if 'metadata' not in requirements:
            requirements['metadata'] = {}
        
        requirements['metadata'].update({
            'template_name': name,
            'description': description,
            'custom_template': True,
            'created_date': '2024-01-01'
        })
        
        # Save template
        with open(template_path, 'w', encoding='utf-8') as f:
            yaml.dump(requirements, f, default_flow_style=False, sort_keys=False, indent=2)
        
        # Reload templates to include the new one
        self.templates = self._load_templates()
        
        return str(template_path)
    
    def get_recommendations(self, document_type: str = None, difficulty: str = None, industry: str = None) -> List[RequirementTemplate]:
        """Get recommended templates based on criteria."""
        filtered = self.templates
        
        if document_type:
            filtered = [t for t in filtered if document_type.lower() in t.document_type.lower()]
        
        if difficulty:
            filtered = [t for t in filtered if t.difficulty == difficulty.lower()]
        
        if industry:
            filtered = [t for t in filtered if t.metadata.get('industry', '').lower() == industry.lower()]
        
        return filtered[:3]  # Top 3 recommendations
    
    def get_industries(self) -> List[str]:
        """Get list of available industries from templates."""
        industries = set()
        for template in self.templates:
            industry = template.metadata.get('industry')
            if industry:
                industries.add(industry.replace('_', ' ').title())
        return sorted(list(industries))
    
    def preview_template(self, template: RequirementTemplate):
        """Show a preview of what the template includes."""
        try:
            requirements = self.load_template_requirements(template)
            
            self.console.print(Panel.fit(f"📖 Template Preview: {template.name}", style="blue bold"))
            
            # Show metadata
            self.console.print(f"[bold]Type:[/bold] {template.document_type}")
            self.console.print(f"[bold]Difficulty:[/bold] {template.difficulty}")
            self.console.print(f"[bold]Description:[/bold] {template.description}\n")
            
            # Show agents and categories
            agents = requirements.get('agents', [])
            for agent in agents:
                agent_name = agent.get('name', 'Unknown Agent')
                self.console.print(f"[bold cyan]{agent_name}:[/bold cyan]")
                
                requirements_list = agent.get('requirements', [])
                for req in requirements_list:
                    category = req.get('category', 'Unknown')
                    weight = req.get('weight', 0)
                    criteria_count = len(req.get('criteria', []))
                    self.console.print(f"  • {category} ({weight}% weight, {criteria_count} criteria)")
                
                self.console.print()
            
            # Show scoring
            scoring = requirements.get('scoring', {})
            weights = scoring.get('weights', {})
            if weights:
                self.console.print("[bold]Agent Weights:[/bold]")
                for agent_type, weight in weights.items():
                    percentage = int(weight * 100)
                    self.console.print(f"  • {agent_type.replace('_', ' ').title()}: {percentage}%")
            
        except Exception as e:
            self.console.print(f"[red]Error previewing template: {e}[/red]")
    
    def validate_requirements_file(self, file_path: str) -> Dict[str, List[str]]:
        """Validate a requirements YAML file and return issues."""
        issues = {
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                requirements = yaml.safe_load(f)
        except Exception as e:
            issues['errors'].append(f"Cannot load YAML file: {e}")
            return issues
        
        # Check required top-level sections
        required_sections = ['metadata', 'agents', 'scoring']
        for section in required_sections:
            if section not in requirements:
                issues['errors'].append(f"Missing required section: {section}")
        
        # Validate metadata
        if 'metadata' in requirements:
            metadata = requirements['metadata']
            recommended_metadata = ['version', 'description', 'template_name', 'difficulty']
            for field in recommended_metadata:
                if field not in metadata:
                    issues['warnings'].append(f"Missing recommended metadata field: {field}")
        
        # Validate agents
        if 'agents' in requirements:
            agents = requirements['agents']
            if not isinstance(agents, list) or len(agents) == 0:
                issues['errors'].append("Agents section must be a non-empty list")
            else:
                for i, agent in enumerate(agents):
                    if not isinstance(agent, dict):
                        issues['errors'].append(f"Agent {i+1} must be a dictionary")
                        continue
                    
                    # Check required agent fields
                    required_agent_fields = ['type', 'name', 'requirements']
                    for field in required_agent_fields:
                        if field not in agent:
                            issues['errors'].append(f"Agent {i+1} missing required field: {field}")
                    
                    # Validate requirements within agent
                    if 'requirements' in agent:
                        if not isinstance(agent['requirements'], list):
                            issues['errors'].append(f"Agent {i+1} requirements must be a list")
                        else:
                            total_weight = 0
                            for j, req in enumerate(agent['requirements']):
                                if 'weight' in req:
                                    total_weight += req['weight']
                                if 'criteria' not in req:
                                    issues['warnings'].append(f"Agent {i+1}, requirement {j+1} has no criteria")
                                elif len(req['criteria']) == 0:
                                    issues['warnings'].append(f"Agent {i+1}, requirement {j+1} has empty criteria")
                            
                            if abs(total_weight - 100) > 1:
                                issues['warnings'].append(f"Agent {i+1} requirement weights sum to {total_weight}%, should be 100%")
        
        # Validate scoring
        if 'scoring' in requirements:
            scoring = requirements['scoring']
            if 'weights' in scoring:
                weights = scoring['weights']
                total_weight = sum(weights.values())
                if abs(total_weight - 1.0) > 0.01:
                    issues['warnings'].append(f"Agent scoring weights sum to {total_weight:.2f}, should be 1.0")
            
            if 'thresholds' not in scoring:
                issues['suggestions'].append("Consider adding scoring thresholds for better evaluation")
        
        return issues
    
    def display_validation_results(self, file_path: str, issues: Dict[str, List[str]]):
        """Display validation results in a user-friendly format."""
        self.console.print(Panel.fit(f"📋 Validation Results: {Path(file_path).name}", style="blue bold"))
        
        if not any(issues.values()):
            self.console.print("[green]✅ Requirements file is valid![/green]")
            return
        
        if issues['errors']:
            self.console.print("[red bold]❌ Errors (must fix):[/red bold]")
            for error in issues['errors']:
                self.console.print(f"  • [red]{error}[/red]")
            self.console.print()
        
        if issues['warnings']:
            self.console.print("[yellow bold]⚠️ Warnings (recommended to fix):[/yellow bold]")
            for warning in issues['warnings']:
                self.console.print(f"  • [yellow]{warning}[/yellow]")
            self.console.print()
        
        if issues['suggestions']:
            self.console.print("[blue bold]💡 Suggestions (optional improvements):[/blue bold]")
            for suggestion in issues['suggestions']:
                self.console.print(f"  • [blue]{suggestion}[/blue]")
            self.console.print()
        
        # Summary
        error_count = len(issues['errors'])
        warning_count = len(issues['warnings'])
        suggestion_count = len(issues['suggestions'])
        
        if error_count > 0:
            self.console.print(f"[red]Found {error_count} error(s) that must be fixed.[/red]")
        elif warning_count > 0:
            self.console.print(f"[yellow]Found {warning_count} warning(s). File is usable but could be improved.[/yellow]")
        else:
            self.console.print(f"[green]No issues found! File has {suggestion_count} optional suggestions.[/green]")


def get_template_manager() -> TemplateManager:
    """Get a template manager instance."""
    return TemplateManager()