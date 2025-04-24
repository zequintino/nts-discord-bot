# NTS Stream URLs
NTS_STREAM_URL_1 = "https://stream-relay-geo.ntslive.net/stream"
NTS_STREAM_URL_2 = "https://stream-relay-geo.ntslive.net/stream2"
NTS_API_URL = "https://www.nts.live/api/v2/live"

# Bot settings
BOT_DEFAULT_VOLUME_1 = 0.4
BOT_DEFAULT_VOLUME_2 = 0.4

# Messages
BOT_HEADER = "𝘕𝘛𝘚 ｜ Don't Assume"

# FFMPEG options for streaming
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -filter:a "volume=0.4"',
}