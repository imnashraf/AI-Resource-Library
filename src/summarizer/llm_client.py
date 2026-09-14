"""Multi-provider resilient LLM client supporting Groq, OpenAI, Anthropic, and Ollama."""

import os
import time
import random
import logging
from typing import Optional, List
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger("summarizer.llm_client")


class LLMClient:
    """Multi-provider LLM interface with polite rate limiting and automated fallbacks."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        min_delay_seconds: float = 2.0,
    ):
        self.provider = provider or os.getenv("LLM_PROVIDER", "groq").lower()
        self.primary_model = model or os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        self.min_delay = min_delay_seconds
        self._last_call_time: float = 0.0

        # Model cascade for Groq
        self.groq_model_cascade = [
            self.primary_model,
            "qwen/qwen3.8-27b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.6-27b",
        ]

        # Initialize clients
        self.groq_client = None
        if os.getenv("GROQ_API_KEY"):
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            except Exception as e:
                logger.warning("Failed to initialize Groq client: %s", e)

        self.openai_client = None
        if os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)

    def _wait_for_rate_limit(self) -> None:
        """Enforce request rate limit spacing to avoid hitting RPM/TPM caps."""
        now = time.time()
        elapsed = now - self._last_call_time
        target_delay = self.min_delay + random.uniform(0.2, 0.6)

        if elapsed < target_delay:
            time.sleep(target_delay - elapsed)

        self._last_call_time = time.time()

    def generate_summary(self, system_prompt: str, user_prompt: str) -> str:
        """Generate structured text with rate limiting, retries, and fallback cascade."""
        if self.groq_client:
            return self._generate_with_groq_cascade(system_prompt, user_prompt)
        elif self.openai_client:
            return self._generate_with_openai(system_prompt, user_prompt)
        else:
            raise RuntimeError(
                "No active LLM provider found! Please set GROQ_API_KEY or OPENAI_API_KEY in .env"
            )

    def _generate_with_groq_cascade(self, system_prompt: str, user_prompt: str) -> str:
        """Try models in the Groq cascade with exponential backoff on rate limits."""
        last_error = None

        for model_name in self.groq_model_cascade:
            attempt = 0
            max_attempts = 3

            while attempt < max_attempts:
                attempt += 1
                self._wait_for_rate_limit()

                try:
                    logger.debug("Calling Groq model: %s (attempt %d/%d)", model_name, attempt, max_attempts)
                    response = self.groq_client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=0.2,
                        max_tokens=950,
                    )
                    content = response.choices[0].message.content
                    if content and len(content.strip()) > 100:
                        return content.strip()
                    logger.warning("Empty response from Groq model %s, retrying...", model_name)

                except Exception as exc:
                    last_error = exc
                    err_str = str(exc)
                    logger.warning("Groq call failed on %s (attempt %d): %s", model_name, attempt, err_str)

                    # If daily token limit reached, immediately break to next model
                    if "tokens per day" in err_str.lower() or "tpd" in err_str.lower():
                        logger.info("Daily limit reached on %s. Cascading to next model...", model_name)
                        break

                    # If rate limit (429/413), back off
                    if "429" in err_str or "rate limit" in err_str.lower() or "413" in err_str:
                        backoff = (2 ** attempt) * 2.0 + random.uniform(1.0, 2.0)
                        logger.info("Rate limit hit. Backing off for %.2fs...", backoff)
                        time.sleep(backoff)
                    elif "model_not_found" in err_str:
                        break  # Immediately try next model in cascade
                    else:
                        time.sleep(2.0)

        # If Groq cascade exhausted, try OpenAI if available
        if self.openai_client:
            logger.info("Groq cascade exhausted. Falling back to OpenAI...")
            return self._generate_with_openai(system_prompt, user_prompt)

        raise RuntimeError(f"All LLM generation attempts failed. Last error: {last_error}")

    def _generate_with_openai(self, system_prompt: str, user_prompt: str) -> str:
        """Fallback generator using OpenAI API."""
        self._wait_for_rate_limit()
        response = self.openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=2200,
        )
        return response.choices[0].message.content.strip()
