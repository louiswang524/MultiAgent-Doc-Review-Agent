from setuptools import setup, find_packages

setup(
    name="launch-doc-reviewer",
    version="1.0.0",
    description="LLM-powered multi-agent system for reviewing launch documents from Google Docs",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "anthropic>=0.7.0",
        "google-auth>=2.0.0",
        "google-auth-oauthlib>=1.0.0",
        "google-auth-httplib2>=0.2.0",
        "google-api-python-client>=2.0.0",
        "pyyaml>=6.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "requests>=2.25.0",
    ],
    entry_points={
        'console_scripts': [
            'launch-doc-reviewer=src.main:cli',
        ],
    },
    python_requires=">=3.8",
)