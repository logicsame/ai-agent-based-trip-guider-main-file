import fastapi
from fastapi import FastAPI, HTTPException, Query, Depends
from models.models import TouristSpot, SearchRequest
import requests
import folium
from typing import List, Dict, Optional, Union
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GroqAPIManager")


async def search_tourist_spots_with_current_location(request: SearchRequest):
    try:
        # Instead of using location string, we'll use latitude and longitude directly
        lat = request.lat
        lon = request.lon
        radius = request.radius
        radius_meters = radius * 1000
        
        # Adjust timeout based on radius size
        timeout_seconds = min(60, 20 + (radius // 10) * 5)
        
        # Use Nominatim reverse geocoding to get country/location info (optional)
        try:
            nominatim_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
            response = requests.get(nominatim_url, headers={'User-Agent': 'TouristApp/1.0'}, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                country = data.get('address', {}).get('country', '')
            else:
                logger.warning(f"Failed to get reverse geocoding information: {response.status_code}")
                country = ''
        except Exception as e:
            logger.warning(f"Error in reverse geocoding: {str(e)}")
            country = ''
        
        # Step 1: Query Overpass API for tourist spots - Primary query
        overpass_url = "https://overpass-api.de/api/interpreter"
        query = f"""
                    [out:json][timeout:{timeout_seconds}];
                    (
                        node["tourism"="attraction"](around:{radius_meters},{lat},{lon});
                        way["tourism"="attraction"](around:{radius_meters},{lat},{lon});
                        relation["tourism"="attraction"](around:{radius_meters},{lat},{lon});
                        node["tourism"="resort"](around:{radius_meters},{lat},{lon});
                        way["tourism"="resort"](around:{radius_meters},{lat},{lon});
                        node["tourism"="hotel"](around:{radius_meters},{lat},{lon});
                        way["tourism"="hotel"](around:{radius_meters},{lat},{lon});
                        node["tourism"="viewpoint"](around:{radius_meters},{lat},{lon});
                        way["tourism"="viewpoint"](around:{radius_meters},{lat},{lon});
                        node["natural"="beach"](around:{radius_meters},{lat},{lon});
                        way["natural"="beach"](around:{radius_meters},{lat},{lon});
                        node["natural"="waterfall"](around:{radius_meters},{lat},{lon});
                        way["natural"="waterfall"](around:{radius_meters},{lat},{lon});
                        node["natural"="forest"](around:{radius_meters},{lat},{lon});
                        way["natural"="forest"](around:{radius_meters},{lat},{lon});
                        relation["natural"="forest"](around:{radius_meters},{lat},{lon});
                        node["landuse"="forest"](around:{radius_meters},{lat},{lon});
                        way["landuse"="forest"](around:{radius_meters},{lat},{lon});
                        relation["landuse"="forest"](around:{radius_meters},{lat},{lon});
                    );
                    out body center;
                    """
        response = requests.post(overpass_url, data={"data": query}, timeout=timeout_seconds)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch tourist spots: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to fetch tourist spots from Overpass API.")

        data = response.json()
        tourist_spots = []

        # Process results from the first query
        for element in data.get('elements', []):
            if 'tags' in element:
                # Skip elements without names
                if 'name' not in element['tags']:
                    continue
                    
                name = element['tags'].get('name')
                
                # Get coordinates
                if element['type'] == 'node':
                    lat_val = element.get('lat', 0)
                    lon_val = element.get('lon', 0)
                else:
                    # For ways and relations, use center point
                    lat_val = element.get('center', {}).get('lat', lat)
                    lon_val = element.get('center', {}).get('lon', lon)
                
                # Determine category with more specific classification
                category = "other"
                if 'tourism' in element['tags']:
                    category = element['tags']['tourism']
                elif 'natural' in element['tags']:
                    category = element['tags']['natural']
                elif 'amenity' in element['tags']:
                    category = element['tags']['amenity']
                
                # Extract location details for better descriptions
                location_details = {
                    'street': element['tags'].get('addr:street', ''),
                    'city': element['tags'].get('addr:city', ''),
                    'state': element['tags'].get('addr:state', ''),
                    'country': element['tags'].get('addr:country', country)
                }
                
                tourist_spots.append(TouristSpot(
                    id=str(element.get('id', '')),
                    name=name,
                    category=category,
                    lat=lat_val,
                    lon=lon_val,
                    tags=element['tags'],
                    location_details=location_details
                ))

        # If we got few results, try a secondary query with expanded categories
        if len(tourist_spots) < 10:
            logger.info(f"Few results found ({len(tourist_spots)}), running secondary query")
            query2 = f"""
                [out:json][timeout:{timeout_seconds}];
                (
                node["historic"](around:{radius_meters},{lat},{lon});
                way["historic"](around:{radius_meters},{lat},{lon});
                relation["historic"](around:{radius_meters},{lat},{lon});
                node["leisure"="park"](around:{radius_meters},{lat},{lon});
                way["leisure"="park"](around:{radius_meters},{lat},{lon});
                node["leisure"="water_park"](around:{radius_meters},{lat},{lon});
                way["leisure"="water_park"](around:{radius_meters},{lat},{lon});
                node["tourism"="museum"](around:{radius_meters},{lat},{lon});
                way["tourism"="museum"](around:{radius_meters},{lat},{lon});
                node["tourism"="gallery"](around:{radius_meters},{lat},{lon});
                way["tourism"="gallery"](around:{radius_meters},{lat},{lon});
                node["amenity"="restaurant"](around:{radius_meters},{lat},{lon})[cuisine];
                way["amenity"="restaurant"](around:{radius_meters},{lat},{lon})[cuisine];
                node["leisure"="nature_reserve"](around:{radius_meters},{lat},{lon});
                way["leisure"="nature_reserve"](around:{radius_meters},{lat},{lon});
                node["boundary"="protected_area"](around:{radius_meters},{lat},{lon});
                way["boundary"="protected_area"](around:{radius_meters},{lat},{lon});
                );
                out body center;
                """
            
            try:
                response2 = requests.post(overpass_url, data={"data": query2}, timeout=timeout_seconds)
                if response2.status_code == 200:
                    data2 = response2.json()
                    
                    # Process additional results
                    for element in data2.get('elements', []):
                        if 'tags' in element and 'name' in element['tags']:
                            name = element['tags'].get('name')
                            
                            # Get coordinates
                            if element['type'] == 'node':
                                lat_val = element.get('lat', 0)
                                lon_val = element.get('lon', 0)
                            else:
                                lat_val = element.get('center', {}).get('lat', lat)
                                lon_val = element.get('center', {}).get('lon', lon)
                            
                            # More specific category classification
                            if 'tourism' in element['tags']:
                                category = element['tags']['tourism']
                            elif 'historic' in element['tags']:
                                category = f"historic_{element['tags']['historic']}"
                            elif 'leisure' in element['tags']:
                                category = f"leisure_{element['tags']['leisure']}"
                            elif 'amenity' in element['tags']:
                                if element['tags'].get('amenity') == 'restaurant' and 'cuisine' in element['tags']:
                                    category = f"restaurant_{element['tags'].get('cuisine')}"
                                else:
                                    category = element['tags']['amenity']
                            else:
                                category = "other"
                            
                            # Extract location details
                            location_details = {
                                'street': element['tags'].get('addr:street', ''),
                                'city': element['tags'].get('addr:city', ''),
                                'state': element['tags'].get('addr:state', ''),
                                'country': element['tags'].get('addr:country', country)
                            }
                            
                            # Check if this spot is already in our list (avoid duplicates)
                            if not any(spot.id == str(element.get('id', '')) for spot in tourist_spots):
                                tourist_spots.append(TouristSpot(
                                    id=str(element.get('id', '')),
                                    name=name,
                                    category=category,
                                    lat=lat_val,
                                    lon=lon_val,
                                    tags=element['tags'],
                                    location_details=location_details
                                ))
                else:
                    logger.warning(f"Secondary query failed: {response2.status_code}")
            except Exception as e:
                logger.warning(f"Error in secondary query: {str(e)}")
                # Continue with the results we have instead of failing completely

        return tourist_spots

    except Exception as e:
        logger.error(f"Error in search_tourist_spots: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")