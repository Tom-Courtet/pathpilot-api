from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

async def generate_response(prompt: str) -> str:
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error when communicating with Gemini : {str(e)}"

async def generate_structured_response(prompt: str, response_schema) -> dict:
    """Génère une réponse structurée via Gemini en utilisant un schéma Pydantic."""
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type='application/json',
            response_schema=response_schema,
        ),
    )
    return response.parsed