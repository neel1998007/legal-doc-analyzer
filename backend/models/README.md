# LLM Models for Legal Document Analyzer

## Current Setup: Ollama

### Model Details
- **Platform**: Ollama (https://ollama.ai)
- **Model**: llama2:7b
- **Size**: ~3.8 GB (managed automatically by Ollama)
- **Installation**: Automatic via `ollama pull llama2:7b`

### Usage
```bash
# Test the model
ollama run llama2:7b "Hello, how are you?"

# In Python (for future RAG integration)
import subprocess
result = subprocess.run(['ollama', 'run', 'llama2:7b', prompt], 
                       capture_output=True, text=True)