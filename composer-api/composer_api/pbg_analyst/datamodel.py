import openai
import os

class ProcessBigraphAnalyst:
    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = self.api_key

    def generate_text(self, prompt, max_tokens=100):
        customized_prompt = self._customize_prompt(prompt)
        response = openai.Completion.create(
            engine="text-davinci-003",  # Adjust based on available models and their capabilities
            prompt=customized_prompt,
            max_tokens=max_tokens
        )
        return response.choices[0].text.strip()

    def _customize_prompt(self, prompt):
        # Customize the prompt to simulate "Process-Bigraph Analyst" behavior
        # You can prepend or append information to the prompt that guides the AI in generating responses
        # that match the intended expertise and style of "Process-Bigraph Analyst"
        customized_prompt = f"[Process-Bigraph Analyst Simulation]: {prompt}"
        return customized_prompt
