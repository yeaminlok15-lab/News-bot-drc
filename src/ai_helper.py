import google.generativeai as genai
import logging
from src.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')

async def generate_summary(text: str, language: str = "English") -> str:
    if not GEMINI_API_KEY or not text.strip():
        return "No summary available."
    
    prompt = f"Summarize the following news article in exactly 2-3 lines in {language}. Keep it professional and concise:\n\n{text}"
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"AI Summary Error: {e}")
        return "Summary could not be generated."
      
