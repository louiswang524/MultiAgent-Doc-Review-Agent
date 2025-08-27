#!/usr/bin/env python3
"""
Launch Document Reviewer CLI
Multi-agent system for evaluating launch documents using LLMs.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

from .launch_doc_reviewer import LaunchDocReviewer
from .requirements_manager import RequirementsManager
from .utils.llm_client import LLMClientFactory
from .requirements_wizard import run_requirements_wizard
from .template_manager import get_template_manager

# Load environment variables
load_dotenv()

# Initialize rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(verbose):
    """Launch Document Reviewer - Multi-agent LLM system for evaluating launch documents."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option('--doc', '-d', required=True, help='Google Docs URL to review')
@click.option('--requirements', '-r', required=True, help='Path to requirements YAML file')
@click.option('--output', '-o', help='Output file for JSON results')
@click.option('--llm-provider', help='LLM provider (openai, anthropic, ollama, local)')
@click.option('--llm-model', help='Specific LLM model to use')
@click.option('--base-url', help='Base URL for local LLM services (ollama/local)')
@click.option('--google-credentials', help='Path to Google API credentials')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text', help='Output format')
def review(doc, requirements, output, llm_provider, llm_model, base_url, google_credentials, output_format):
    """Review a launch document from Google Docs."""
    
    async def run_review():
        try:
            # Validate inputs
            if not Path(requirements).exists():
                console.print(f"[red]Error: Requirements file not found: {requirements}[/red]")
                sys.exit(1)
            
            # Check for available providers
            available_providers = LLMClientFactory.get_available_providers()
            if not available_providers:
                console.print("[red]Error: No LLM providers available. Please configure at least one.[/red]")
                console.print("Configuration options:")
                console.print("  - Set OPENAI_API_KEY for OpenAI")
                console.print("  - Set ANTHROPIC_API_KEY for Anthropic") 
                console.print("  - Install aiohttp for local models (ollama/local)")
                sys.exit(1)
            
            # Show startup info
            console.print(Panel.fit("🚀 Launch Document Reviewer", style="blue bold"))
            console.print(f"Document: {doc}")
            console.print(f"Requirements: {requirements}")
            console.print(f"Available LLM providers: {', '.join(available_providers)}")
            
            # Initialize reviewer
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                task = progress.add_task("Initializing reviewer...", total=None)
                
                try:
                    reviewer = LaunchDocReviewer(
                        llm_provider=llm_provider,
                        llm_model=llm_model,
                        base_url=base_url,
                        google_credentials_path=google_credentials
                    )
                    progress.update(task, description="✅ Reviewer initialized")
                except Exception as e:
                    progress.update(task, description=f"❌ Initialization failed: {e}")
                    console.print(f"[red]Error initializing reviewer: {e}[/red]")
                    sys.exit(1)
                
                # Run review
                progress.update(task, description="Running document review...")
                try:
                    result = await reviewer.review_document(doc, requirements)
                    progress.update(task, description="✅ Review completed")
                except Exception as e:
                    progress.update(task, description=f"❌ Review failed: {e}")
                    console.print(f"[red]Error during review: {e}[/red]")
                    sys.exit(1)
            
            # Display results
            if output_format == 'json':
                result_dict = {
                    'document_url': result.document_url,
                    'document_title': result.document_title,
                    'review_timestamp': result.review_timestamp.isoformat(),
                    'overall_score': result.overall_score,
                    'summary': result.summary,
                    'confidence_level': result.confidence_level,
                    'agent_reviews': [
                        {
                            'agent_name': review.agent_name,
                            'agent_type': review.agent_type,
                            'score': review.overall_score,
                            'summary': review.summary,
                            'key_issues': review.key_issues,
                            'recommendations': review.recommendations,
                            'confidence_level': review.confidence_level,
                            'category_evaluations': [
                                {
                                    'category': cat.category,
                                    'score': cat.score,
                                    'weight': cat.weight,
                                    'reasoning': cat.reasoning
                                }
                                for cat in review.category_evaluations
                            ]
                        }
                        for review in result.agent_reviews
                    ],
                    'key_recommendations': result.key_recommendations
                }
                
                if output:
                    with open(output, 'w') as f:
                        json.dump(result_dict, f, indent=2)
                    console.print(f"[green]Results saved to {output}[/green]")
                else:
                    console.print(json.dumps(result_dict, indent=2))
            else:
                # Text format
                display_review_results(result)
                
                if output:
                    with open(output, 'w') as f:
                        f.write(reviewer.format_review_results(result))
                    console.print(f"[green]Results saved to {output}[/green]")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Review cancelled by user[/yellow]")
            sys.exit(1)
        except Exception as e:
            logger.exception("Unexpected error during review")
            console.print(f"[red]Unexpected error: {e}[/red]")
            sys.exit(1)
    
    # Run async function
    asyncio.run(run_review())


@cli.command()
@click.option('--file', '-f', default='requirements.yaml', help='Requirements file path')
def init_requirements(file):
    """Initialize a sample requirements file."""
    try:
        req_manager = RequirementsManager()
        output_path = req_manager.create_sample_requirements(file)
        
        console.print(Panel.fit("📋 Sample Requirements Created", style="green bold"))
        console.print(f"Created: {output_path}")
        console.print("\nNext steps:")
        console.print("1. Edit the requirements file to match your needs")
        console.print("2. Set up your LLM API keys in environment variables")
        console.print("3. Configure Google API credentials for document access")
        console.print("4. Run: launch-doc-reviewer review --doc <url> --requirements <file>")
        
    except Exception as e:
        console.print(f"[red]Error creating requirements file: {e}[/red]")
        sys.exit(1)


@cli.command()
def setup_requirements():
    """Interactive wizard to create customized requirements."""
    try:
        output_file = run_requirements_wizard()
        console.print(f"\n[green]🎉 Success! Your custom requirements have been saved.[/green]")
        console.print(f"File: {output_file}")
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Review and adjust the generated requirements if needed")
        console.print("2. Set up your LLM provider (API keys or local models)")
        console.print("3. Configure Google API credentials")
        console.print(f"4. Run: python -m src.main review --doc <url> --requirements {output_file}")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error during requirements setup: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--type', 'doc_type', help='Filter templates by document type')
@click.option('--difficulty', help='Filter templates by difficulty (beginner/intermediate/advanced)')
@click.option('--industry', help='Filter templates by industry (healthcare, financial_services, etc.)')
def list_templates(doc_type, difficulty, industry):
    """List available requirements templates."""
    try:
        template_manager = get_template_manager()
        
        if doc_type or difficulty or industry:
            templates = template_manager.get_recommendations(doc_type, difficulty, industry)
            filter_info = f"type: {doc_type or 'any'}, difficulty: {difficulty or 'any'}, industry: {industry or 'any'}"
            console.print(f"[bold]Filtered Templates[/bold] ({filter_info})")
        else:
            templates = template_manager.list_templates()
        
        if not templates:
            console.print("[yellow]No templates found matching your criteria.[/yellow]")
            return
            
        template_manager.display_templates()
        
        console.print(f"\n[dim]Found {len(templates)} template(s). Use 'use-template' command to apply one.[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error listing templates: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('template_id', type=int)
@click.option('--file', '-f', default='requirements.yaml', help='Output requirements file path')
@click.option('--preview', is_flag=True, help='Preview template without saving')
def use_template(template_id, file, preview):
    """Use a predefined requirements template."""
    try:
        template_manager = get_template_manager()
        template = template_manager.get_template_by_id(template_id)
        
        if not template:
            console.print(f"[red]Template {template_id} not found. Use 'list-templates' to see available options.[/red]")
            sys.exit(1)
        
        if preview:
            template_manager.preview_template(template)
            return
        
        # Load and save template
        requirements = template_manager.load_template_requirements(template)
        
        # Update metadata
        requirements['metadata']['last_updated'] = 'auto-generated'
        requirements['metadata']['created_from_template'] = template.name
        
        with open(file, 'w', encoding='utf-8') as f:
            yaml.dump(requirements, f, default_flow_style=False, sort_keys=False, indent=2)
        
        console.print(Panel.fit(f"📋 Template Applied: {template.name}", style="green bold"))
        console.print(f"Requirements saved to: {file}")
        console.print(f"Template type: {template.document_type}")
        console.print(f"Difficulty: {template.difficulty}")
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print("1. Review and customize the requirements if needed")
        console.print("2. Set up your LLM provider")
        console.print("3. Run your first review!")
        
    except Exception as e:
        console.print(f"[red]Error applying template: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('requirements_file', type=click.Path(exists=True))
def validate_requirements(requirements_file):
    """Validate a requirements YAML file for errors and best practices."""
    try:
        template_manager = get_template_manager()
        issues = template_manager.validate_requirements_file(requirements_file)
        template_manager.display_validation_results(requirements_file, issues)
        
        # Exit with error code if there are errors
        if issues['errors']:
            sys.exit(1)
        
    except Exception as e:
        console.print(f"[red]Error validating requirements file: {e}[/red]")
        sys.exit(1)


@cli.command()
def list_industries():
    """List available industry-specific templates."""
    try:
        template_manager = get_template_manager()
        industries = template_manager.get_industries()
        
        if not industries:
            console.print("[yellow]No industry-specific templates available.[/yellow]")
            return
        
        console.print(Panel.fit("🏭 Available Industries", style="blue bold"))
        console.print("Use these industry names with --industry flag:")
        
        for industry in industries:
            industry_key = industry.lower().replace(' ', '_')
            console.print(f"  • {industry} (--industry {industry_key})")
        
        console.print(f"\n[dim]Found {len(industries)} industry-specific template(s).[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error listing industries: {e}[/red]")
        sys.exit(1)


@cli.command()
def check_setup():
    """Check system setup and configuration."""
    console.print(Panel.fit("🔍 System Setup Check", style="blue bold"))
    
    # Check Python version
    python_version = sys.version_info
    console.print(f"Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 8):
        console.print("[red]⚠️ Python 3.8+ required[/red]")
    else:
        console.print("[green]✅ Python version OK[/green]")
    
    # Check LLM providers
    available_providers = LLMClientFactory.get_available_providers()
    console.print(f"Available LLM providers: {available_providers if available_providers else 'None'}")
    
    if not available_providers:
        console.print("[yellow]⚠️ No LLM providers configured[/yellow]")
        console.print("Configuration options:")
        console.print("  - OPENAI_API_KEY (for OpenAI)")
        console.print("  - ANTHROPIC_API_KEY (for Anthropic)")
        console.print("  - aiohttp installed (for local models)")
    else:
        for provider in available_providers:
            if provider in ['ollama', 'local']:
                # Check if local services are reachable
                base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434') if provider == 'ollama' else os.getenv('LOCAL_BASE_URL', 'http://localhost:8000')
                service_available = LLMClientFactory.check_local_service_availability(base_url)
                status = "✅" if service_available else "⚠️"
                console.print(f"{status} {provider.capitalize()} service: {base_url}")
            else:
                console.print(f"✅ {provider.capitalize()}: configured")
    
    # Check Google credentials
    google_creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if google_creds and Path(google_creds).exists():
        console.print("[green]✅ Google credentials configured[/green]")
    else:
        console.print("[yellow]⚠️ Google credentials not found[/yellow]")
        console.print("Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
    
    # Check dependencies
    try:
        import openai, anthropic, googleapiclient, aiohttp
        console.print("[green]✅ All dependencies installed[/green]")
    except ImportError as e:
        console.print(f"[red]⚠️ Missing dependency: {e}[/red]")


def display_review_results(result):
    """Display review results in rich format."""
    
    # Overall score panel
    score_color = "green" if result.overall_score >= 7 else "yellow" if result.overall_score >= 5 else "red"
    score_panel = Panel.fit(
        f"Overall Score: {result.overall_score}/10\n{result.summary}",
        title="📊 Review Results",
        border_style=score_color
    )
    console.print(score_panel)
    
    # Agent scores table
    table = Table(title="🤖 Agent Evaluations", show_header=True, header_style="bold magenta")
    table.add_column("Agent", style="cyan", no_wrap=True)
    table.add_column("Score", justify="center")
    table.add_column("Confidence", justify="center")
    table.add_column("Summary", style="dim")
    
    for review in result.agent_reviews:
        score_style = "green" if review.overall_score >= 7 else "yellow" if review.overall_score >= 5 else "red"
        table.add_row(
            review.agent_name,
            f"[{score_style}]{review.overall_score}/10[/{score_style}]",
            review.confidence_level,
            review.summary[:80] + "..." if len(review.summary) > 80 else review.summary
        )
    
    console.print(table)
    
    # Recommendations
    if result.key_recommendations:
        console.print("\n📝 Key Recommendations:")
        for i, rec in enumerate(result.key_recommendations[:5], 1):
            console.print(f"{i}. {rec}")
    
    # Metadata
    console.print(f"\n📄 Document: {result.document_title}")
    console.print(f"🔗 URL: {result.document_url}")
    console.print(f"⏰ Review Date: {result.review_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == '__main__':
    cli()