"""
NTS Radio API client utility.
Handles interactions with the NTS Radio API.
"""
import aiohttp
import json
import html
from src.config.settings import NTS_API_URL


async def fetch_nts_info(channel):
    """
    Fetch NTS live information from the API.
    
    Args:
        channel (int): The NTS channel number (1 or 2)
        
    Returns:
        str: Formatted string with current show information
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(NTS_API_URL) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    # API response has channels indexed from 0
                    channel_idx = channel - 1
                    
                    # Parse the data correctly based on the actual API structure
                    if 'results' in data and isinstance(data['results'], list) and len(data['results']) > channel_idx:
                        channel_data = data['results'][channel_idx]
                        show_name = channel_data.get('now', {}).get('broadcast_title', 'Unknown Show')
                        location_short = channel_data.get('now', {}).get('embeds', {}).get('details', {}).get('location_short')
                        location_long = channel_data.get('now', {}).get('embeds', {}).get('details', {}).get('location_long')
                        
                        # Decode HTML entities in show name and locations
                        show_name = html.unescape(show_name) if show_name else 'Unknown Show'
                        location_short = html.unescape(location_short) if location_short else None
                        location_long = html.unescape(location_long) if location_long else None
                        
                        # Use the short location if available, otherwise use long location
                        location = location_short or location_long or "Unknown Location"
                        
                        channel_symbol = "１ ▶︎" if channel == 1 else "２ ▶︎"
                        return f"{channel_symbol}  {show_name}  －  {location}"
                    else:
                        print(f"Unexpected API structure: {json.dumps(data, indent=2)[:500]}...")
                        return f"Could not parse NTS {channel} data (unexpected structure)"
                except (KeyError, IndexError, TypeError) as e:
                    print(f"Error parsing NTS data: {str(e)}")
                    print(f"API structure: {type(data['results'])}")
                    return f"Error retrieving NTS {channel} info: {str(e)}"
            else:
                return f"Failed to fetch NTS data. Status code: {response.status}"