from yt_dlp import YoutubeDL

async def stream(video_id: str, video: bool = False):
    ydl_opts = {
        "format": "bestvideo+bestaudio/best" if video else "bestaudio/best",
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            f"https://www.youtube.com/watch?v={video_id}",
            download=False,
        )
        return info["url"]