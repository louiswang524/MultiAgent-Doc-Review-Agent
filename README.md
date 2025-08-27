# Launch Document Reviewer

An LLM-powered multi-agent system for comprehensive review of product launch documents. The system uses specialized AI agents (Product Manager, Data Scientist, and Engineering) to evaluate launch documents from Google Docs and provide detailed scores and recommendations.

## Features

- **Multi-Agent Review**: Three specialized AI agents evaluate documents from different perspectives
- **LLM-Powered Analysis**: Uses OpenAI GPT-4 or Anthropic Claude for intelligent document analysis  
- **Google Docs Integration**: Directly fetches and analyzes documents from Google Docs
- **Flexible Requirements**: Customizable evaluation criteria through YAML configuration
- **Detailed Scoring**: Provides scores (0-10) for each category and overall assessment
- **Actionable Recommendations**: Generates specific, actionable improvement suggestions
- **Multiple Output Formats**: Text and JSON output options
- **CLI Interface**: Easy-to-use command-line interface with rich formatting

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd launch-doc-reviewer-python

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

### 2. Setup API Keys

Create a `.env` file with your API keys:

```bash
# Choose your LLM provider
OPENAI_API_KEY=your_openai_api_key_here
# OR
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Set provider preference (optional)
LLM_PROVIDER=openai  # or 'anthropic'

# Google API credentials
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/google_credentials.json
```

### 3. Setup Google API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Docs API
4. Create credentials (OAuth 2.0 or Service Account)
5. Download the credentials JSON file
6. Set the path in your `.env` file

### 4. Initialize Requirements

```bash
python -m src.main init-requirements --file requirements.yaml
```

This creates a sample requirements file that you can customize for your needs.

### 5. Run Your First Review

```bash
python -m src.main review \
  --doc "https://docs.google.com/document/d/your-doc-id" \
  --requirements requirements.yaml \
  --output results.json
```

## Usage

### Basic Review Command

```bash
python -m src.main review --doc <google-docs-url> --requirements <requirements-file>
```

### Advanced Options

```bash
python -m src.main review \
  --doc "https://docs.google.com/document/d/abc123" \
  --requirements custom_requirements.yaml \
  --output review_results.json \
  --format json \
  --llm-provider anthropic \
  --llm-model claude-3-sonnet-20240229
```

### Check System Setup

```bash
python -m src.main check-setup
```

### Help

```bash
python -m src.main --help
python -m src.main review --help
```

## Architecture

### Agents

**Product Manager Agent**
- Evaluates market analysis and business strategy
- Assesses product-market fit and competitive positioning  
- Reviews business case and financial projections
- Checks stakeholder alignment and go-to-market strategy

**Data Scientist Agent**
- Analyzes data requirements and quality standards
- Evaluates analytics strategy and measurement methodology
- Reviews technical implementation of data systems
- Assesses reporting and data governance plans

**Engineering Agent**
- Examines technical architecture and system design
- Reviews implementation timeline and resource planning
- Evaluates operational readiness and reliability
- Assesses quality assurance and testing strategies

### Requirements Configuration

Requirements are defined in YAML format with the following structure:

```yaml
metadata:
  version: "1.0"
  description: "Launch document review requirements"

agents:
  - type: "product_manager"
    name: "Product Manager Agent"
    requirements:
      - category: "Market Analysis"
        weight: 25
        criteria:
          - name: "Target Market Definition"
            description: "Clear definition of target market"
            weight: 1.0

scoring:
  scale: "0-10"
  weights:
    product_manager: 0.4
    data_scientist: 0.3
    engineering: 0.3
```

## Example Output

```
🚀 Launch Document Reviewer

📊 Review Results
Overall Score: 7.2/10
Good launch document readiness with some gaps. Strong coverage from Product Manager Agent perspective(s).

🤖 Agent Evaluations
┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Agent               ┃ Score   ┃ Confidence ┃ Summary                                                                          ┃
┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Product Manager     │ 8.1/10  │ High       │ Excellent product strategy coverage. Strong business case and market analysis   │
│ Data Scientist      │ 6.7/10  │ Medium     │ Good data strategy with gaps in technical implementation                         │
│ Engineering Agent   │ 6.8/10  │ Medium     │ Moderate technical coverage with significant operational gaps                    │
└─────────────────────┴─────────┴────────────┴──────────────────────────────────────────────────────────────────────────────┘

📝 Key Recommendations:
1. [DATA_SCIENTIST] Define comprehensive data quality framework with monitoring and alerting
2. [ENGINEERING] Establish comprehensive operational readiness including SLI/SLO definitions  
3. [DATA_SCIENTIST] Implement rigorous measurement methodology with statistical testing
```

## Requirements File Customization

Edit the generated `requirements.yaml` file to customize evaluation criteria:

- **Add/remove criteria**: Modify the criteria list for each category
- **Adjust weights**: Change category and criteria weights to reflect priorities
- **Modify scoring**: Update scoring thresholds and agent weights
- **Add descriptions**: Provide detailed descriptions for better LLM understanding

## Troubleshooting

### Common Issues

**"No LLM providers configured"**
- Ensure API keys are set in environment variables
- Check `.env` file is in the correct location
- Verify API keys are valid and have sufficient credits

**"Google authentication failed"**
- Verify Google credentials file path is correct
- Ensure Google Docs API is enabled in your project
- Check that credentials have necessary permissions

**"Document not found"**
- Verify Google Docs URL is publicly accessible or shared with your service account
- Check document ID extraction from URL
- Ensure document is not deleted or moved

**"Rate limiting errors"**
- Implement delays between API calls
- Consider upgrading API plan limits
- Use different API keys for different agents

### Debug Mode

Enable verbose logging for debugging:

```bash
python -m src.main --verbose review --doc <url> --requirements <file>
```

## Development

### Project Structure

```
src/
├── agents/                 # Agent implementations
│   ├── base_agent.py      # Base agent class
│   ├── product_manager_agent.py
│   ├── data_scientist_agent.py
│   └── engineering_agent.py
├── utils/                 # Utility modules
│   ├── llm_client.py      # LLM API client
│   └── google_docs_client.py  # Google Docs API client
├── launch_doc_reviewer.py # Main orchestrator
├── requirements_manager.py # Requirements management
└── main.py               # CLI interface

examples/                  # Example files
config/                   # Configuration files
tests/                    # Test files
```

### Running Tests

```bash
python -m pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Search existing GitHub issues
3. Create a new issue with detailed information
4. Include logs and configuration (remove sensitive data)