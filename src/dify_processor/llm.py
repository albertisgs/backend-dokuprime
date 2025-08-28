from openai import OpenAI
from langchain_ollama import OllamaEmbeddings
from .prompt import Prompt

class LLM:
    def __init__(self, llm_base_url, llm_model, llm_api_key, embedding_base_url, embedding_model):
        if llm_base_url:
            self.llm_client = OpenAI(
                base_url=llm_base_url,
                api_key=llm_api_key
            )
        else:
            self.llm_client = OpenAI(api_key=llm_api_key)
        self.llm_model = llm_model
        
        self.embedding_client = OllamaEmbeddings(
            base_url=embedding_base_url,
            model=embedding_model
        )

        self.prompt = Prompt()

        print("LLM Initialized")

    def call_llm_api(self, prompt):
        """Call LLM using OpenAI-compatible API."""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return ""

    def extract_document_info(self, chunk_text):
        """Extract document topic and chunk description using OpenAI-compatible LLM."""
        
        document_topic = self.call_llm_api(self.prompt.chunk_topic(chunk_text))
        chunk_description = self.call_llm_api(self.prompt.chunk_description(chunk_text))
        
        return document_topic, chunk_description
