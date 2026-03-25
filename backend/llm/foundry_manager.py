import openai
from foundry_local import FoundryLocalManager
import time
import requests

class FoundryEngine:
    def __init__(self, reflex_model="qwen-reflex", reason_model="deepseek-reason"):
        self.reflex_model_name = reflex_model
        self.reason_model_name = reason_model
        
        self.manager = FoundryLocalManager()
        base = self.manager.service_uri if getattr(self.manager, 'service_uri', None) else "http://localhost:4500"
        self.base_url = f"{base}/v1" if not base.endswith("/v1") else base
        
        if not self._check_connection():
            print("Foundry Service not detected. Starting via SDK...")
            try:
                self.manager.start_service()
                # Wait for startup
                for _ in range(10):
                    if self._check_connection():
                        break
                    time.sleep(2)
            except Exception as e:
                print(f"Failed to start Foundry Service: {e}")

        self.client = openai.OpenAI(
            base_url=self.base_url,
            api_key="foundry" 
        )
        
        # Verify models and pre-warm
        try:
            models = self.client.models.list()
            print(f"Connected to Foundry at {self.base_url}")
            print(f"Models available: {[m.id for m in models.data]}")
            self._warmup()
        except Exception as e:
            print(f"Warning: Could not connect to Foundry: {e}")

    def _warmup(self):
        """Sends a dummy token to each engine to ensure they are loaded in VRAM."""
        print(f"Pre-warming engines: {self.reflex_model_name}, {self.reason_model_name}...")
        try:
            # Warm up Reflex
            self.client.chat.completions.create(
                model=self.reflex_model_name,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=1
            )
            # Warm up Reason
            self.client.chat.completions.create(
                model=self.reason_model_name,
                messages=[{"role": "user", "content": "think"}],
                max_tokens=1
            )
            print("Engines warmed up.")
        except Exception as e:
            print(f"Warmup failed: {e}")

    def _check_connection(self):
        try:
            requests.get(f"{self.base_url}/models", timeout=2)
            return True
        except:
            return False

    def fast_reflex(self, prompt, system_prompt="You are a helpful assistant."):
        """
        Uses the smaller, faster model (Qwen) for quick tasks like formatting or agenda.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.reflex_model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Reflex Error: {e}")
            return None

    def deep_reason(self, context, query):
        """
        Uses the larger thinking model (DeepSeek) for complex RAG or compliance tasks.
        """
        try:
            # DeepSeek R1 prompt engineering typically benefits from 'Chain of Thought' or specific preamble
            messages = [
                {"role": "system", "content": "You are a deep thinking compliance auditor and facilitator. Analyze the context carefully."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"}
            ]
            
            # Using stream=True as per spec to allow future UI streaming, 
            # though for now we might consume it fully or yield it.
            # Returning the generator for the consumer to handle.
            return self.client.chat.completions.create(
                model=self.reason_model_name,
                messages=messages,
                stream=True
            )
        except Exception as e:
            print(f"Reasoning Error: {e}")
            return None  
