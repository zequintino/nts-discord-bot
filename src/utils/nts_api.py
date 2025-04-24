import aiohttp
import html
from src.config.settings import NTS_API_URL


async def fetch_nts_data():
    """Fetch raw data from NTS API (command function)"""
    async with aiohttp.ClientSession() as session:
        async with session.get(NTS_API_URL) as response:
            if response.status == 200:
                return await response.json()
            return None


def parse_channel_info(data, channel):
    """Parse channel information from API data (query function)"""
    if not data or 'results' not in data:
        return None
    
    # API response has channels indexed from 0
    channel_idx = channel - 1
    
    if not isinstance(data['results'], list) or len(data['results']) <= channel_idx:
        return None
        
    return data['results'][channel_idx]


def extract_show_details(channel_data):
    """Extract and format show details from channel data (query function)"""
    if not channel_data or 'now' not in channel_data:
        return None
        
    show_name = channel_data.get('now', {}).get('broadcast_title', 'Unknown Show')
    location_short = channel_data.get('now', {}).get('embeds', {}).get('details', {}).get('location_short')
    location_long = channel_data.get('now', {}).get('embeds', {}).get('details', {}).get('location_long')
    
    show_name = html.unescape(show_name) if show_name else 'Unknown Show'
    location_short = html.unescape(location_short) if location_short else None
    location_long = html.unescape(location_long) if location_long else None
    
    location = location_short or location_long or "Unknown Location"
    
    return {
        'show_name': show_name,
        'location': location
    }


def format_channel_display(channel, show_details):
    """Format the channel display string (query function)"""
    channel_symbol = "１ ▶︎" if channel == 1 else "２ ▶︎"
    return f"{channel_symbol}  {show_details['show_name']}  －  {show_details['location']}"


class NTSRadioInfo:
    """Class to handle NTS Radio information retrieval and formatting"""
    
    @staticmethod
    async def get_channel_data(channel):
        """Get raw channel data (command function)"""
        data = await fetch_nts_data()
        if not data:
            return None
            
        return parse_channel_info(data, channel)
    
    @staticmethod
    async def get_show_details(channel):
        """Get structured show details (command + query function)"""
        channel_data = await NTSRadioInfo.get_channel_data(channel)
        if not channel_data:
            return None
            
        return extract_show_details(channel_data)
    
    @staticmethod
    async def get_formatted_display(channel):
        """Get formatted display string (command + query function)"""
        show_details = await NTSRadioInfo.get_show_details(channel)
        if not show_details:
            return f"Could not retrieve information for NTS {channel}"
            
        return format_channel_display(channel, show_details)

    @staticmethod
    async def get_rich_channel_info(channel):
        """Get comprehensive channel information including show details, mixcloud links, etc.
        
        This demonstrates the flexibility of our architecture by providing rich data access
        that can be used for advanced features.
        
        Args:
            channel: The NTS channel number (1 or 2)
            
        Returns:
            dict: Rich information about the current broadcast or None if unavailable
        """
        channel_data = await NTSRadioInfo.get_channel_data(channel)
        if not channel_data or 'now' not in channel_data:
            return None
            
        now_data = channel_data.get('now', {})
        
        # Extract basic information
        show_details = extract_show_details(channel_data)
        if not show_details:
            return None
            
        # Extract additional rich information
        rich_info = {
            **show_details,  # Include basic show details
            'channel': channel,
            'episode_id': now_data.get('episode_id'),
            'start_timestamp': now_data.get('start_timestamp'),
            'end_timestamp': now_data.get('end_timestamp'),
        }
        
        # Extract media links if available
        embeds = now_data.get('embeds', {})
        if 'media' in embeds:
            rich_info['media'] = {
                'mixcloud_url': embeds.get('media', {}).get('mixcloud_url'),
                'soundcloud_url': embeds.get('media', {}).get('soundcloud_url')
            }
            
        # Extract more details if available
        if 'details' in embeds:
            details = embeds.get('details', {})
            rich_info['details'] = {
                'description': html.unescape(details.get('description', '')) if details.get('description') else None,
                'genre': details.get('genre'),
                'location_long': html.unescape(details.get('location_long', '')) if details.get('location_long') else None
            }
            
        return rich_info
    
    @staticmethod
    async def get_both_channels_info():
        """Get information for both NTS channels simultaneously
        
        Returns:
            tuple: (channel1_info, channel2_info) - Each element is either a dictionary with show details
                  or None if information couldn't be retrieved
        """
        data = await fetch_nts_data()
        if not data:
            return None, None
            
        channel1_data = parse_channel_info(data, 1)
        channel2_data = parse_channel_info(data, 2)
        
        channel1_details = extract_show_details(channel1_data) if channel1_data else None
        channel2_details = extract_show_details(channel2_data) if channel2_data else None
        
        return channel1_details, channel2_details


# Keep the original function for backward compatibility
async def fetch_nts_info(channel):
    """Legacy function for backward compatibility"""
    try:
        return await NTSRadioInfo.get_formatted_display(channel)
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error processing NTS data: {str(e)}")
        return f"Error retrieving NTS {channel} info: {str(e)}"