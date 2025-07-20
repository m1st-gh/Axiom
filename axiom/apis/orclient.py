from openai import OpenAI, APIError
from typing import List, Dict, Optional, Any, MutableMapping
from axiom import logger


class OpenRouterClient:
    """
    A client for interacting with the OpenRouter API using the OpenAI Python library.
    """

    BASE_URL: str = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        site_url: Optional[str] = None,
        app_name: Optional[str] = None,
    ) -> None:
        """
        Initializes the OpenRouterClient.

        Args:
            api_key (str): Your OpenRouter API key.
            site_url (str, optional): Your site URL, for OpenRouter analytics.
                                      Sent as HTTP-Referer.
            app_name (str, optional): Your app name, for OpenRouter analytics.
                                      Sent as X-Title.
        """
        if not api_key:
            logger.error("OpenRouter API key is required.")
            raise ValueError("OpenRouter API key is required.")

        self.api_key: str = api_key
        self.default_headers: MutableMapping[str, str] = {}
        if site_url:
            self.default_headers["HTTP-Referer"] = site_url
        if app_name:
            self.default_headers["X-Title"] = app_name

        self.client: OpenAI = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            default_headers=self.default_headers if self.default_headers else None,
        )

    def get_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Gets a chat completion from the specified model.

        Args:
            model (str): The model identifier (e.g., "anthropic/claude-3-opus").
            messages (List[Dict[str, str]]): A list of message objects, e.g.,
                                             [{"role": "user", "content": "Hello!"}].
            temperature (float, optional): Controls randomness. Defaults to 0.7.
            max_tokens (Optional[int], optional): Max tokens to generate.
            **kwargs: Additional parameters to pass to the OpenAI API.

        Returns:
            Optional[str]: The content of the completion as a string, or None if an error occurs.

        Raises:
            APIError: If an API error occurs.
        """
        logger.info(f"Requesting completion for model: {model}")
        try:
            params: Dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": False,
                **kwargs,
            }
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            completion: Any = self.client.chat.completions.create(**params)

            if completion.choices and completion.choices[0].message:
                content: Optional[str] = completion.choices[0].message.content
                logger.info(f"Received completion from model: {model}")
                return content
            logger.warning(f"No completion content received for model: {model}")
            return None

        except APIError as e:
            logger.error(f"OpenRouter API error: {e}")
            raise

        except Exception as e:
            logger.error(f"An unexpected error occurred during completion: {e}")
            raise
