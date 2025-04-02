from .utils import call_llm
import json

class Agent:
    def __init__(self, name, model, instructions):
        self.name = name
        self.model = model
        self.instructions = instructions

    def run(self, customer_data):
        prompt = f"""
You are {self.name}, a KYC sub-agent. {self.instructions}

Customer Info:
{json.dumps(customer_data, indent=2)}

Respond clearly and concisely.
"""
        result = call_llm(prompt, model=self.model)
        return result
