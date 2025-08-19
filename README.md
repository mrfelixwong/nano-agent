# nano-agent
A tiny agent you can read in one sitting. Works locally with **Ollama**. Prints **traces**, a tiny **judge**, and **cost metrics**.

## Quickstart
```bash
brew install ollama
ollama run llama3.1
python -m nano_agent run "Add 8.5% to 3.03e12 exactly"
python -m nano_agent run "Convert 72 F to C"
python -m nano_agent run "days_between 2025-01-01 2025-08-18"
