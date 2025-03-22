import fastapi
from fastapi import FastAPI, HTTPException, Query, Depends
from models.models import PlaceDescriptionRequest
from fastapi.responses import HTMLResponse
import folium
import logging
from api_manager import GroqKeyManager

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GroqAPIManager")




key_manager = GroqKeyManager()

async def generate_description(request: PlaceDescriptionRequest):
    try:
        # Generate a description using the Groq API
        prompt = f"""Create a concise, natural description (100 - 120 words) for this tourist spot:
                - Name: '{request.spot_name}'
                - Category: {request.spot_category.replace('_', ' ')}
                - Location: {request.location}, {request.country}

                Focus only on:
                1. What makes this place special or unique (be specific to the actual location if possible)
                2. One activity visitors typically enjoy here (tailored to the type of location)
                3. A practical tip based on the current weather: {request.weather_data.description if request.weather_data else 'unknown'}, {request.weather_data.temperature if request.weather_data else ''}°C

                Write as an experienced tour guide in simple, direct language. Avoid generic phrases like "worth visiting" or "popular destination."
                """
        
        messages = [
            {"role": "system", "content": "You are a knowledgeable local tour guide providing authentic information about tourist destinations. Your descriptions sound natural and engaging, like a real person talking."},
            {"role": "user", "content": prompt}
        ]
        
        completion = key_manager.execute_with_fallback(
            lambda client, msgs: client.chat.completions.create(
                model="llama-3.3-70b-specdec",
                messages=msgs,
                temperature=0.3,
                max_tokens=200,
            ),
            messages
        )
        
        return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Error in generate_description: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")