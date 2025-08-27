# Requirements Setup Guide

The Launch Document Reviewer now provides multiple ways to easily set up requirements for each agent, making it much more user-friendly.

## Setup Options

### 1. Interactive Wizard (Recommended for beginners)
```bash
python -m src.main setup-requirements
```
- Guided step-by-step setup
- Asks questions about your document type and focus areas
- Automatically generates customized requirements
- Perfect for first-time users

### 2. Predefined Templates
```bash
# List all available templates
python -m src.main list-templates

# Filter by industry
python -m src.main list-templates --industry healthcare

# Filter by difficulty
python -m src.main list-templates --difficulty beginner

# Use a specific template
python -m src.main use-template 1 --file my-requirements.yaml

# Preview template before using
python -m src.main use-template 1 --preview
```

### 3. Industry-Specific Templates

Available industries:
- **Healthcare**: HIPAA compliance, clinical workflows, patient data protection
- **Financial Services**: PCI-DSS, SOX compliance, fraud detection, regulatory requirements  
- **Software/SaaS**: Scalability, APIs, user analytics, platform architecture

```bash
# List available industries
python -m src.main list-industries

# Find healthcare-specific templates
python -m src.main list-templates --industry healthcare
```

### 4. Basic Template Generation
```bash
python -m src.main init-requirements --file basic-requirements.yaml
```

## Available Templates

| Template | Industry | Difficulty | Description |
|----------|----------|------------|-------------|
| Basic Product Launch | General | Beginner | Simple product launch requirements |
| Agile Feature Release | Software | Intermediate | Sprint-based feature development |
| Comprehensive Technical Spec | Software | Advanced | Complex technical architecture reviews |
| FinTech Product Launch | Financial | Advanced | Financial services with compliance focus |
| Healthcare Product Launch | Healthcare | Advanced | Medical technology with HIPAA compliance |
| SaaS Platform Launch | Software | Intermediate | Scalable platform with analytics focus |

## Validation & Quality Assurance

### Validate Your Requirements File
```bash
python -m src.main validate-requirements my-requirements.yaml
```

The validator checks for:
- **Errors**: Missing required sections, invalid structure
- **Warnings**: Missing recommended fields, weight inconsistencies
- **Suggestions**: Optional improvements for better evaluation

### Preview Templates
```bash
python -m src.main use-template 1 --preview
```
Shows what agents, categories, and criteria are included before applying.

## Quick Start Examples

### For a simple product launch:
```bash
python -m src.main use-template 1  # Basic Product Launch
```

### For a healthcare app:
```bash
python -m src.main list-templates --industry healthcare
python -m src.main use-template 4  # Healthcare Product Launch
```

### For custom requirements:
```bash
python -m src.main setup-requirements  # Interactive wizard
```

## File Structure

Requirements files follow this structure:
```yaml
metadata:
  version: "1.0"
  description: "Your project description"
  template_name: "Template Name"
  difficulty: "beginner|intermediate|advanced"
  industry: "healthcare|financial_services|software"

agents:
  - type: "product_manager"
    name: "Product Manager Agent"
    requirements:
      - category: "Market Analysis"
        weight: 40
        criteria: [...]

scoring:
  weights:
    product_manager: 0.4
    data_scientist: 0.3
    engineering: 0.3
```

## Tips for Success

1. **Start Simple**: Use basic templates first, then customize
2. **Validate Often**: Run `validate-requirements` before using files
3. **Industry Focus**: Use industry templates for compliance requirements
4. **Weight Balance**: Ensure category weights sum to 100% per agent
5. **Agent Balance**: Ensure agent weights sum to 1.0 in scoring section

The system now makes it much easier to create professional requirements files without needing deep YAML knowledge or understanding the complex agent structure.