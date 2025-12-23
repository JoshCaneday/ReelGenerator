import os
from groq import Groq

class LLM:
    def __init__(self,key=""):
        if key:
            self.client = Groq(api_key=key)
        else:
            self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = "llama-3.3-70b-versatile"

    def get_response(self,query) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": query,
                }
            ],
            model=self.model,
        )
        return chat_completion.choices[0].message.content