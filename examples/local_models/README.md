# Local LLM Configuration Examples

This directory contains example environment configuration files for running the Launch Document Reviewer with various local LLM setups.

## Supported Local LLM Providers

### 1. Ollama (Recommended for Beginners)

Ollama is the easiest way to run local LLMs with minimal setup.

**Installation:**
```bash
# macOS/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download/windows
```

**Setup:**
```bash
# Pull a model (this may take a while depending on model size)
ollama pull llama3.1:8b

# Start Ollama (usually runs automatically)
ollama serve

# Test the model
ollama run llama3.1:8b
```

**Configuration:**
Copy `.env.ollama` to your project root as `.env` and modify as needed.

**Popular Models:**
- `llama3.1:8b` - Good balance of performance and capability
- `llama3.2:3b` - Faster, smaller model for quick reviews
- `mistral:7b` - Alternative model with good performance
- `codellama:7b` - Code-focused model for technical documents

### 2. vLLM (High Performance)

vLLM provides optimized inference for local deployment with OpenAI-compatible API.

**Installation:**
```bash
pip install vllm
```

**Setup:**
```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000
```

**Configuration:**
Copy `.env.vllm` to your project root as `.env` and modify as needed.

### 3. text-generation-webui (oobabooga)

A popular web interface for running local LLMs with extensive model support.

**Installation:**
```bash
git clone https://github.com/oobabooga/text-generation-webui.git
cd text-generation-webui
pip install -r requirements.txt
```

**Setup:**
```bash
# Start with API support
python server.py --api --listen --model-dir models/
```

**Configuration:**
Copy `.env.text-generation-webui` to your project root as `.env` and modify as needed.

## Model Recommendations by Use Case

### Fast Reviews (Lower Resource Requirements)
- **Ollama**: `llama3.2:3b`, `phi3:3.8b`
- **vLLM**: `meta-llama/Llama-3.2-3B-Instruct`
- **Memory**: ~4-6GB RAM

### Balanced Performance
- **Ollama**: `llama3.1:8b`, `mistral:7b`
- **vLLM**: `meta-llama/Llama-3.1-8B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3`
- **Memory**: ~8-12GB RAM

### High-Quality Reviews (Higher Resource Requirements)
- **Ollama**: `llama3.1:70b`
- **vLLM**: `meta-llama/Llama-3.1-70B-Instruct`
- **Memory**: 48GB+ RAM (consider model quantization)

### Technical/Code Documents
- **Ollama**: `codellama:7b`, `codellama:13b`
- **vLLM**: `codellama/CodeLlama-7B-Instruct-hf`
- **Memory**: ~8-16GB RAM

## Usage Examples

### Using with Ollama
```bash
# Set environment
cp examples/local_models/.env.ollama .env

# Run review
python -m src.main review \
  --doc "https://docs.google.com/document/d/your-doc-id" \
  --requirements requirements.yaml \
  --llm-provider ollama \
  --llm-model llama3.1:8b
```

### Using with vLLM
```bash
# Set environment
cp examples/local_models/.env.vllm .env

# Run review
python -m src.main review \
  --doc "https://docs.google.com/document/d/your-doc-id" \
  --requirements requirements.yaml \
  --llm-provider local \
  --base-url http://localhost:8000
```

## Performance Tips

1. **Model Size vs Performance**: Smaller models (3B-7B parameters) run faster but may provide less detailed analysis. Larger models (70B+) give better results but require more resources.

2. **Hardware Considerations**:
   - **CPU**: Models can run on CPU but will be slower
   - **GPU**: NVIDIA GPUs with CUDA provide significant speedup
   - **Memory**: Ensure sufficient RAM/VRAM for your chosen model

3. **Batch Processing**: For multiple documents, consider keeping the local service running rather than starting/stopping for each review.

4. **Model Quantization**: Use quantized models (like Q4, Q8 variants) to reduce memory usage with minimal quality loss.

## Troubleshooting

### Common Issues

**Connection refused errors:**
- Ensure your local LLM service is running
- Check the correct port and URL
- Use `python -m src.main check-setup` to verify connectivity

**Out of memory errors:**
- Try a smaller model (3B instead of 8B)
- Use quantized versions
- Reduce context length in the model configuration

**Slow performance:**
- Ensure GPU acceleration is enabled if available
- Consider using a smaller model for faster processing
- Check system resources and close other memory-intensive applications

**Model not found errors:**
- For Ollama: Run `ollama pull <model-name>` first
- For vLLM: Ensure the model path is correct and the model is downloaded
- Check model naming conventions for each provider

### Getting Help

- Check service logs for detailed error messages
- Use the `check-setup` command to diagnose configuration issues
- Refer to the specific LLM provider's documentation for advanced configuration options