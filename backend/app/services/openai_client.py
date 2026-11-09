from openai import OpenAI

from app.core.config import settings

# the sdk default is a 600s timeout with 2 retries, which can pin a worker thread for
# half an hour while the browser gave up long ago. one shared client, one set of rules
client = OpenAI(api_key=settings.openai_api_key, timeout=15, max_retries=1)

# carries a body on purpose: the frontend reads a bare 504 as "server unreachable"
AI_TIMEOUT_DETAIL = "the AI service took too long to respond, please try again"
