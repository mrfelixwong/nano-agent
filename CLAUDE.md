# Development Notes

## Commands

```bash
python -m nano_agent run "Calculate 15% of 200"
python -m nano_agent playground
./smoke.sh
```

## Architecture

- Agent: observe-think-act loop
- Tools: calculator, unit_convert, date_calc  
- Model: Ollama local LLM
- Judge: validates outputs

## Testing

Smoke tests cover percentage math, unit conversion, and date calculations.