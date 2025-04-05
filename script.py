import argparse
import os
import re
import subprocess
from typing import Optional, Tuple
import main as mn
from loguru import logger
import yt_dlp


logger.add("youtube_downloader.log", rotation="10 MB", level="INFO")

def sanitize_filename(filename: str) -> str:
    """Remove special characters from filenames."""
    return re.sub(r'[<>:"/\\|?*]', '', filename).strip()

def validate_trim(start: Optional[str], end: Optional[str]) -> Tuple[float, float]:
    """Validate and convert trim settings to seconds."""
    def time_to_seconds(t: str) -> float:
        parts = list(map(float, t.split(':')))
        return sum(x * 60 ** i for i, x in enumerate(reversed(parts)))

    if (start is None) != (end is None):
        raise ValueError("Both start and end times must be provided for trimming")

    if start and end:
        start_sec = time_to_seconds(start)
        end_sec = time_to_seconds(end)
        if start_sec >= end_sec:
            raise ValueError("Start time must be before end time")
        return start_sec, end_sec
    return 0, 0

def download_media(
    url: str,
    media_type: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> None:
    """Download and process media from YouTube."""
    try:
        start_sec, end_sec = validate_trim(start_time, end_time)
        trim = start_time is not None and end_time is not None

        ydl_opts = {
            'logger': logger,
            'progress_hooks': [lambda d: logger.info(f"Progress: {d.get('_percent_str', '?')}")],
            'restrictfilenames': True,
            'windowsfilenames': True,
            'outtmpl': '%(title)s.%(ext)s',
            'postprocessor_args': ['-nostdin'],
            'check_formats': 'selected',  # Verify formats are playable
        }

        if media_type == 'music':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Prefer AVC/h264 codec for better compatibility
            ydl_opts.update({
                'format': '(bestvideo[ext=mp4][vcodec^=avc1]/bestvideo[ext=mp4])+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',  # Force MP4 container
                }],
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.debug(f"All available formats: {info['formats']}")
            # Download the media
            info_dict = ydl.extract_info(url, download=True)
            temp_file = ydl.prepare_filename(info_dict)
            
            if media_type == 'music':
                temp_file = os.path.splitext(temp_file)[0] + '.mp3'

            # Sanitize filename
            sanitized_temp = sanitize_filename(temp_file)
            if temp_file != sanitized_temp:
                os.rename(temp_file, sanitized_temp)
                temp_file = sanitized_temp

        if trim:
            logger.info(f"Trimming from {start_time} to {end_time}")
            base, ext = os.path.splitext(temp_file)
            output_file = f"{base}_trimmed{ext}"

            # Use hardware acceleration if available
            ffmpeg_cmd = [
                'ffmpeg',
                '-hide_banner',
                '-loglevel', 'error',
                '-ss', str(start_sec),
                '-i', temp_file,
                '-to', str(end_sec),
                '-c:v', 'h264_nvenc' if 'nvenc' in subprocess.getoutput('ffmpeg -encoders') else 'libx264',
                '-preset', 'fast',
                '-movflags', '+faststart',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-y',
                output_file
            ]

            try:
                subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                os.replace(output_file, temp_file)
                logger.success(f"Trimmed file: {temp_file}")
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg failed: {e.stderr}")
                raise

        logger.success(f"Download complete: {temp_file}")

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download failed: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='YouTube Downloader')
    parser.add_argument('--default-search',default='ytsearch')
    parser.add_argument('--type', required=False, choices=['music', 'video'])
    parser.add_argument('--start', help='Start time (MM:SS or seconds)')
    parser.add_argument('--end', help='End time (MM:SS or seconds)')
    parser.add_argument('url', nargs='?', default= str(mn.df_select3))

    args = parser.parse_args()

    try:
        if not os.path.exists('assets'):
            os.makedirs('assets')
        
        logger.info(f"Starting {args.type} download")
        download_media(args.url, args.type, args.start, args.end)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        exit(1)

if __name__ == "__main__":
    main()