import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Eres un tutor experto en matemáticas. Resuelves problemas de todos los niveles. Explica paso a paso en español."""

def solve_math_problem(problem: str) -> str:
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": problem}
        ],
        max_tokens=1024
    )
    return response.choices[0].message.content
    
