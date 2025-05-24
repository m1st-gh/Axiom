from openai import OpenAI, APIError
from typing import List, Dict, Optional, Generator, Any


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

    def get_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Optional[str | Generator[str, None, None]]:
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
            Optional[str | Generator[str, None, None]]:
                - If stream is False: The content of the completion as a string.
                - If stream is True: A generator yielding chunks of the content.
                - None if an API error occurs (and not streaming).

        Raises:
            APIError: If an API error occurs during a streaming request.
        """
        try:
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
                    return completion.choices[0].message.content
                return None
        except APIError as e:
            print(f"OpenRouter API Error: {e}")
            if stream:  # For stream, error is raised to be handled by caller
                raise
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Lists available models from OpenRouter (via the OpenAI compatible endpoint).
        Note: This might not list ALL models on OpenRouter, but those exposed
        through the OpenAI-compatible /models endpoint. For a full list,
        refer to OpenRouter documentation or their site.

        Returns:
            List[Dict[str, Any]]: A list of model objects.
        """
        try:
            models = self.client.models.list()
            return [model.to_dict() for model in models.data]
        except APIError as e:
            print(f"OpenRouter API Error listing models: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred while listing models: {e}")
            return []


# --- Example Usage ---
if __name__ == "__main__":
    # IMPORTANT: Replace with your actual OpenRouter API key
    # It's best to use environment variables for API keys in real applications
    import os

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    if not OPENROUTER_API_KEY:
        print("Please set the OPENROUTER_API_KEY environment variable.")
        # You can set a dummy key for basic testing if you don't make calls
        # OPENROUTER_API_KEY = "sk-or-v1-dummy-key-for-testing-init"
    else:
        # Initialize the client
        # Optionally provide your site URL and app name for OpenRouter analytics
        or_client = OpenRouterClient(
            api_key=OPENROUTER_API_KEY,
            site_url="https://myawesomesite.com",
            app_name="MyCoolApp",
        )

        # --- Example 1: Get a simple completion ---
        print("\n--- Example 1: Simple Completion ---")
        messages_simple = [
            {"role": "user", "content": "Hello! What's a fun fact about Python?"}
        ]
        # You can find model IDs on openrouter.ai
        # e.g., "mistralai/mistral-7b-instruct", "google/gemini-pro", "anthropic/claude-3-haiku"
        response_simple = or_client.get_completion(
            model="mistralai/mistral-7b-instruct",
            messages=messages_simple,
            temperature=0.5,
            max_tokens=150,
        )
        if response_simple:
            print(f"Model Response: {response_simple}")
        else:
            print("Failed to get a response.")

        # --- Example 2: Streaming completion ---
        print("\n--- Example 2: Streaming Completion ---")
        messages_stream = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a short story about a brave robot."},
        ]
        try:
            print("Streaming Model Response:")
            full_streamed_response = ""
            for chunk in or_client.get_completion(
                model="google/gemini-pro",  # Or another model
                messages=messages_stream,
                stream=True,
                max_tokens=200,
            ):
                print(chunk, end="", flush=True)
                full_streamed_response += chunk
            print("\n--- End of Stream ---")
            # print(f"Full streamed response: {full_streamed_response}")
        except APIError as e:
            print(f"\nError during streaming: {e}")
        except Exception as e:
            print(f"\nAn unexpected error during streaming: {e}")

        # --- Example 3: List available models (via OpenAI compatible endpoint) ---
        print("\n--- Example 3: List Models ---")
        available_models = or_client.list_models()
        if available_models:
            print(f"Found {len(available_models)} models:")
            for model_info in available_models[:5]:  # Print first 5
                print(f"  ID: {model_info.get('id')}")
        else:
            print("Could not retrieve model list or no models found.")
