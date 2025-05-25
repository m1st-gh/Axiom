from openai import OpenAI, APIError
from typing import List, Dict, Optional, Generator, Any, Union
import asyncio
import functools

from core import logger


class OpenRouterClient:
    """
    A client for interacting with the OpenRouter API using the OpenAI Python library.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(
        self,
        api_key: str,
        site_url: Optional[str] = None,
        app_name: Optional[str] = None,
    ):
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
            raise ValueError("OpenRouter API key is required.")

        self.api_key = api_key
        self.default_headers = {}
        if site_url:
            self.default_headers["HTTP-Referer"] = site_url
        if app_name:
            self.default_headers["X-Title"] = app_name

        self.client = OpenAI(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            default_headers=self.default_headers if self.default_headers else None,
        )

        logger.info("API client initialized")

    def get_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Optional[Union[str, Generator[str, None, None]]]:
        """
        Gets a chat completion from the specified model.

        Args:
            model (str): The model identifier (e.g., "anthropic/claude-3-opus").
            messages (List[Dict[str, str]]): A list of message objects, e.g.,
                                             [{"role": "user", "content": "Hello!"}].
            temperature (float, optional): Controls randomness. Defaults to 0.7.
            max_tokens (Optional[int], optional): Max tokens to generate.
            stream (bool, optional): Whether to stream the response. Defaults to False.
            **kwargs: Additional parameters to pass to the OpenAI API.

        Returns:
            Optional[Union[str, Generator[str, None, None]]]:
                - If stream is False: The content of the completion as a string.
                - If stream is True: A generator yielding chunks of the content.
                - None if an API error occurs (and not streaming).

        Raises:
            APIError: If an API error occurs during a streaming request.
        """
        try:
            logger.debug(f"Requesting completion from model: {model}")

            if stream:
                return self._stream_completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
            else:
                completion = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                    **kwargs,
                )
                if completion.choices and completion.choices[0].message:
                    content = completion.choices[0].message.content
                    logger.debug(f"Received completion: {content[:50]}...")
                    return content
                logger.warning("Received empty completion from API")
                return None

        except APIError as e:
            logger.error(f"API Error: {e}")
            if stream:  # For stream, error is raised to be handled by caller
                raise
            return None

        except Exception as e:
            logger.error(f"An unexpected error occurred with API: {e}")
            if stream:
                raise
            return None

    def _stream_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """Helper for streaming completions."""
        logger.debug(f"Starting streaming completion from model: {model}")

        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

        logger.debug("Completed streaming response")

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Lists available models from the API.

        Returns:
            List[Dict[str, Any]]: A list of model objects.
        """
        try:
            logger.debug("Listing available models")
            models = self.client.models.list()
            model_list = [model.to_dict() for model in models.data]
            logger.info(f"Retrieved {len(model_list)} models")
            return model_list

        except APIError as e:
            logger.error(f"API Error listing models: {e}")
            return []

        except Exception as e:
            logger.error(f"An unexpected error occurred while listing models: {e}")
            return []

    async def get_completion_async(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        """
        Async wrapper for get_completion to use in async contexts.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            functools.partial(
                self.get_completion,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
                **kwargs,
            ),
        )
