# AI Engine

The AI Engine is the core intelligence component of CodeProof. It provides:

- Project analysis and understanding
- Architecture analysis
- Progressive hint generation
- Explanation evaluation
- Patch generation

## Structure

```
ai/
├── models/          # Pydantic data models
├── providers/       # AI provider abstractions (Gemini, OpenRouter)
├── services/        # High-level AI services
├── prompts/         # Prompt templates
└── README.md
```

## Providers

The AI Engine uses a provider abstraction pattern:

- `BaseAIProvider` - Abstract base class
- `GeminiProvider` - Google Gemini implementation
- `OpenRouterProvider` - OpenRouter implementation

Switch providers by changing the provider instance, no code changes needed in services.

## Configuration

Set API keys in `.env`:
- `GEMINI_API_KEY`
- `OPENROUTER_API_KEY`

## Usage

```python
from ai.providers import GeminiProvider, AIProviderConfig
from ai.services import ProjectAnalyzer

config = AIProviderConfig(api_key="...", model="gemini-1.5-pro")
provider = GeminiProvider(config)
analyzer = ProjectAnalyzer(provider)
analysis = await analyzer.analyze(project_snapshot)
```