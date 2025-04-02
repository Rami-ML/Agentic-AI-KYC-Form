from openai import OpenAI
import re

client = OpenAI()  # Will auto-load your API key from env

def call_llm(prompt, model="gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()

def clean_response(text):
    # Remove all markdown bold/italics/bullets
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)        # italics
    return text.strip()
