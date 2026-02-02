import os
import time
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

load_dotenv()


@dataclass
class AIResponse:
    content: str
    model: str
    tokens_used: int
    success: bool = True
    error: Optional[str] = None


class AIAnalyzer:
    MODELS = {
        "fast": "llama-3.1-8b-instant",
        "smart": "llama-3.3-70b-versatile",
        "mixtral": "mixtral-8x7b-32768",
        "large-input-token": "groq/compound"
    }

    def __init__(self, model: str = "smart", requests_per_minute: int = 25):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        self.client = Groq(api_key=api_key)
        self.model = self.MODELS.get(model, model)
        self.min_interval = 60.0 / requests_per_minute
        self.last_request = 0

    def _rate_limit(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()

    def analyze(
        self,
        content: str,
        prompt: str,
        max_tokens: int = 4096
    ) -> AIResponse:
        self._rate_limit()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content}
                ],
                max_tokens=max_tokens,
                temperature=0.1,
            )

            return AIResponse(
                content=response.choices[0].message.content,
                model=self.model,
                tokens_used=response.usage.total_tokens
            )

        except Exception as e:
            return AIResponse(
                content="",
                model=self.model,
                tokens_used=0,
                success=False,
                error=str(e)
            )

    def extract_json(self, content: str, schema_description: str) -> AIResponse:
        prompt = f"""Extract information and return ONLY valid JSON, no markdown.

Schema:
{schema_description}

Rules:
- Return ONLY the JSON object
- Use null for missing fields
- Be precise and factual"""

        return self.analyze(content, prompt)
