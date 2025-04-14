from openai import OpenAI
from . import config

# Initialize the OpenAI client
client = OpenAI(api_key=config.OPENAI_API_KEY)

def search_web(query, system_prompt=None):
    """Performs a web search using the configured search model."""
    response = client.responses.create(
        model=config.SEARCH_MODEL,
        tools=[{
            "type": "web_search_preview",
            "user_location": {
                "type": "approximate",
                "country": "GB",
                "city": "London",
                "region": "London",
            }
        }],
        input=query,
        instructions=system_prompt
    )
    return response.output_text

def reason(query, system_prompt=None):
    """Generates a response using the configured reasoning model."""
    response = client.responses.create(
        model=config.REASONING_MODEL,
        input=query,
        instructions=system_prompt
    )
    return response.output_text 