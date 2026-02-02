"""DON'T WORK - Local AI analyzer using Ollama for offline/private analysis."""

from dataclasses import dataclass
from typing import Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False


@dataclass
class LocalAIResponse:
    """Response from local Ollama model."""
    content: str
    model: str
    success: bool = True
    error: Optional[str] = None
    # Note: Ollama doesn't provide token counts by default
    tokens_used: int = 0


class OllamaAnalyzer:
    """
    Local AI analyzer using Ollama.

    Supported models (run `ollama list` to see installed):
    - phi3: Fast, good for simple tasks (~3.8B)
    - llama3.2: Balanced performance (~2GB for 3B, ~4.7GB for 8B)
    - mistral: Good general purpose (~4.1GB)
    - qwen2.5: Strong reasoning (~4.7GB for 7B)
    - deepseek-r1: Advanced reasoning (various sizes)

    Install a model: `ollama pull phi3`
    """

    # Common models with their approximate context lengths
    MODELS = {
        "phi3": "phi3:latest",                    # 3.8B params, 128k context
        "phi3-mini": "phi3:mini",          # Smaller variant
        "llama3.2": "llama3.2",            # 3B default
        "llama3.2-1b": "llama3.2:1b",      # Smallest, fastest
        "mistral": "mistral",              # 7B params
        "qwen2.5": "qwen2.5",              # 7B default
        "qwen2.5-coder": "qwen2.5-coder",  # Code-focused
        "deepseek-r1": "deepseek-r1",      # Reasoning model
    }

    def __init__(self, model: str = "phi3"):
        if not OLLAMA_AVAILABLE:
            raise ImportError(
                "Ollama is not installed. Install it with: pip install ollama\n"
                "Also ensure Ollama server is running: https://ollama.ai"
            )

        # Resolve model alias or use directly
        self.model = self.MODELS.get(model, model)

        # Verify model is available
        self._check_model()

    def _check_model(self):
        """Check if the model is installed locally."""
        try:
            models = ollama.list()
            installed = [m.model for m in models.models] if hasattr(models, 'models') else []

            # Check if our model (or a variant) is installed
            model_base = self.model.split(':')[0]
            if not any(model_base in m for m in installed):
                print(f"⚠️ Model '{self.model}' may not be installed.")
                print(f"   Installed models: {installed}")
                print(f"   Install with: ollama pull {self.model}")
        except Exception as e:
            print(f"⚠️ Could not verify model availability: {e}")

    def analyze(
        self,
        content: str,
        prompt: str,
        max_tokens: int = 4096,  # Not directly used by Ollama, but kept for compatibility
        verbose: bool = True
    ) -> LocalAIResponse:
        """
        Analyze content using local Ollama model.

        Args:
            content: The content to analyze
            prompt: System prompt with instructions
            max_tokens: Max response tokens (Ollama uses num_predict)
            verbose: Print progress information

        Returns:
            LocalAIResponse with the analysis result
        """
        import time

        input_chars = len(content) + len(prompt)
        input_tokens_est = input_chars // 4

        if verbose:
            print(f"🤖 [Ollama] Starting inference with {self.model}...")
            print(f"   Input: ~{input_tokens_est} tokens ({input_chars} chars)")
            print(f"   ⏳ Processing (local models can take 30-120s)...", end="", flush=True)

        start_time = time.time()

        try:
            # Combine system and user prompt for better local model compatibility
            # Local models like Phi-3 often perform better with a single prompt
            combined_prompt = f"### System\n{prompt}\n\n### User\n{content}\n\n### Assistant\n"

            # Use streaming to show progress
            full_response = ""
            token_count = 0
            last_dot_time = start_time
            first_token_received = False
            eval_time = 0

            if verbose:
                print(f"   ⏳ Evaluating prompt (this can take 1-3 mins for large inputs)...", end="", flush=True)

            for chunk in ollama.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": combined_prompt}
                ],
                options={
                    "num_predict": max_tokens,
                    "temperature": 0.1,  # Low temperature for consistent JSON
                    "num_ctx": 8192,     # Ensure context is large enough for scraped content
                },
                stream=True
            ):
                if not first_token_received:
                    first_token_received = True
                    eval_time = time.time() - start_time
                    if verbose:
                        print(f" Done! ({eval_time:.1f}s)")
                        print(f"   ✍️ Generating response...", end="", flush=True)

                if chunk.message and chunk.message.content:
                    full_response += chunk.message.content
                    token_count += 1

                    # Print a dot every 2 seconds to show generation progress
                    if verbose and time.time() - last_dot_time > 2:
                        print(".", end="", flush=True)
                        last_dot_time = time.time()

            elapsed = time.time() - start_time
            gen_time = elapsed - eval_time
            tokens_per_sec = token_count / gen_time if token_count > 0 and gen_time > 0 else 0

            if verbose:
                print(f" Done!")
                print(f"   ✅ Processed in {elapsed:.1f}s (Eval: {eval_time:.1f}s, Gen Speed: {tokens_per_sec:.1f} tok/s)")

            return LocalAIResponse(
                content=full_response,
                model=self.model,
                tokens_used=token_count
            )

        except ollama.ResponseError as e:
            elapsed = time.time() - start_time
            if verbose:
                print(f" Error after {elapsed:.1f}s")
            return LocalAIResponse(
                content="",
                model=self.model,
                success=False,
                error=f"Ollama error: {e}"
            )
        except Exception as e:
            elapsed = time.time() - start_time
            if verbose:
                print(f" Error after {elapsed:.1f}s")
            return LocalAIResponse(
                content="",
                model=self.model,
                success=False,
                error=str(e)
            )

    def extract_json(self, content: str, schema_description: str) -> LocalAIResponse:
        """Extract structured JSON from content."""
        prompt = f"""Extract information and return ONLY valid JSON, no markdown.

Schema:
{schema_description}

Rules:
- Return ONLY the JSON object, no explanation
- Use null for missing fields
- Be precise and factual"""

        return self.analyze(content, prompt)


def is_ollama_available() -> bool:
    """Check if Ollama is installed and server is running."""
    if not OLLAMA_AVAILABLE:
        return False
    try:
        ollama.list()
        return True
    except Exception:
        return False
