import fastapi
from fastapi import FastAPI, HTTPException
from models.models import AskQuestionRequest
from api_manager import GroqKeyManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GroqAPIManager")


key_manager = GroqKeyManager()




async def ask_question(request: AskQuestionRequest):
    try:
        # Debug: Log the incoming request
        logger.info(f"Incoming request: {request}")

        # Check if the question is about weather or rain
        weather_keywords = ['rain', 'weather', 'forecast', 'precipitation', 'sunny', 'cloudy', 'storm', 'thunder']
        is_weather_question = any(keyword in request.question.lower() for keyword in weather_keywords)

        # Get weather data with forecast
        current_weather_data = request.weather_data

        if is_weather_question and current_weather_data and current_weather_data.forecast:

            forecast = current_weather_data.forecast

            # Debug: Log the forecast data
            logger.info(f"Forecast data: {forecast}")

            # Check if question mentions time periods
            two_days_keywords = ['next 2 days', 'next two days', '2 days', 'two days', '48 hours', 'tomorrow']
            is_two_days = any(keyword in request.question.lower() for keyword in two_days_keywords)

            # Create a weather-specific response based on the forecast
            if 'rain' in request.question.lower() or 'precipitation' in request.question.lower() or 'storm' in request.question.lower():
                if is_two_days:
                    # 2-day forecast
                    day1 = forecast['day1']
                    day2 = forecast['day2']

                    day1_intensity = "light" if day1['max_precipitation'] < 1 else "moderate" if day1['max_precipitation'] < 5 else "heavy"
                    day2_intensity = "light" if day2['max_precipitation'] < 1 else "moderate" if day2['max_precipitation'] < 5 else "heavy"

                    if day1['rain_chance'] and day2['rain_chance']:
                        weather_answer = f"Yes, there's a chance of rain at {request.spot_name} in the next 2 days. Today: {day1_intensity} rain for approximately {day1['rain_hours']} hours. Tomorrow: {day2_intensity} rain for approximately {day2['rain_hours']} hours."
                    elif day1['rain_chance']:
                        weather_answer = f"There's a chance of {day1_intensity} rain today at {request.spot_name} for approximately {day1['rain_hours']} hours, but tomorrow looks dry based on current forecasts."
                    elif day2['rain_chance']:
                        weather_answer = f"Today looks dry at {request.spot_name}, but tomorrow there's a chance of {day2_intensity} rain for approximately {day2['rain_hours']} hours."
                    else:
                        weather_answer = f"No rain is expected at {request.spot_name} for the next 2 days based on current forecasts. The current weather is {current_weather_data.description} at {current_weather_data.temperature}°C."
                else:
                    # Default to 24-hour forecast
                    hours = forecast['day1']['rain_hours']
                    intensity = "light" if forecast['day1']['max_precipitation'] < 1 else "moderate" if forecast['day1']['max_precipitation'] < 5 else "heavy"
                    if forecast['day1']['rain_chance']:
                        weather_answer = f"Yes, there's a chance of {intensity} rain in the next 24 hours at {request.spot_name}. Rain is expected for approximately {hours} hours."
                    else:
                        weather_answer = f"No rain is expected at {request.spot_name} in the next 24 hours based on current forecasts. The current weather is {current_weather_data.description} at {current_weather_data.temperature}°C."
        
                return weather_answer
            else:
                # For general weather questions
                if is_two_days:
                    day1_forecast = f"Today: {current_weather_data.description}, {current_weather_data.temperature}°C. Rain is {'expected' if forecast['day1']['rain_chance'] else 'not expected'}."
                    day2_forecast = f"Tomorrow: Rain is {'expected' if forecast['day2']['rain_chance'] else 'not expected'}."
                    weather_answer = f"{day1_forecast} {day2_forecast}"
                else:
                    rain_info = f"Rain is {'expected' if forecast['day1']['rain_chance'] else 'not expected'} in the next 24 hours."
                    weather_answer = f"Current weather at {request.spot_name} is {current_weather_data.description} at {current_weather_data.temperature}°C. {rain_info}"
        
                return weather_answer
        else:
            # Handle non-weather questions or cases where weather data is unavailable
            spot_info = {
                'name': request.spot_name,
                'category': request.spot_category.replace('_', ' '),
                'location': f"{request.location}, {request.country}",
                'tags': {},  # Assuming tags are not available in the request
                'weather': f"{current_weather_data.description}, {current_weather_data.temperature}°C" if current_weather_data else "unknown"
            }

            if current_weather_data and 'forecast' in current_weather_data:
                spot_info['weather_forecast'] = f"Rain {'expected' if current_weather_data.forecast['day1']['rain_chance'] else 'not expected'} in next 24 hours"

            # Define the prompt for non-weather questions
            prompt = f"""You are a local tour guide with deep knowledge about {request.spot_name}, a {request.spot_category.replace('_', ' ')} in {request.location}, {request.country}. 
            Here's the available information: {spot_info}.
            A visitor has asked: '{request.question}'
            Provide a concise, accurate answer (80-100 words) based only on this data and logical inferences from the category and weather. 
            Avoid speculation beyond the provided information. Answer in a friendly, direct tone as if speaking to the visitor."""
            
            messages = [
                {"role": "system", "content": "You are a knowledgeable local tour guide providing authentic, accurate answers about tourist destinations based on given data."},
                {"role": "user", "content": prompt}
            ]
            
            # Call the LLM
            completion = key_manager.execute_with_fallback(
                lambda client, msgs: client.chat.completions.create(
                    model="llama-3.3-70b-specdec",
                    messages=msgs,
                    temperature=0.3,
                    max_tokens=150,
                ),
                messages
            )
            
            return completion.choices[0].message.content

    except Exception as e:
        logger.error(f"Error in ask_question: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")