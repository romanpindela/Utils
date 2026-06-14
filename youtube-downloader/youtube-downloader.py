import sys
import os
import argparse
import subprocess
import shutil
from urllib.parse import urlparse

# Automatyczna instalacja brakujących bibliotek
try:
    import yt_dlp
except ImportError:
    print("Notice: Required library 'yt-dlp' is not installed. Installing it now...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
        print("Successfully installed 'yt-dlp'.\n")
        import yt_dlp
    except Exception as e:
        print(f"Error: Failed to install 'yt-dlp' automatically. Please run 'pip install yt-dlp' manually. Details: {e}")
        sys.exit(1)

def check_js_runtime():
    if not shutil.which("deno") and not shutil.which("node"):
        print("================================================================================")
        print("CRITICAL WARNING: No JavaScript runtime found (Node.js or Deno).")
        print("YouTube now requires a JS runtime to bypass its anti-bot protections.")
        print("Without it, your downloads will likely fail with 'HTTP Error 403: Forbidden'.")
        print("\nTo fix this on Windows, open PowerShell and run:")
        print("    irm https://deno.land/install.ps1 | iex")
        print("\nAfter installation, RESTART your terminal and run this script again.")
        print("================================================================================\n")

def download_videos(file_path, output_dir, resolution):
    check_js_runtime()
    
    if not os.path.isfile(file_path):
        print(f"Error: The provided path '{file_path}' does not exist or is not a valid file.")
        return

    current_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_path = os.path.abspath(os.path.join(current_dir, 'auth', 'cookies.txt'))
    
    if not os.path.exists(cookie_path):
        print("--------------------------------------------------------------------------------")
        print(f"Notice: Cookie file not found at '{cookie_path}'")
        print("If you need to download age-restricted, private, or premium videos, you must")
        print("provide your browser cookies.")
        print("\nHow to set it up:")
        print("1. Install the 'Get cookies.txt LOCALLY' add-on for Google Chrome.")
        print("2. Go to YouTube, click the extension, and export your cookies.")
        print("3. Create an 'auth' directory next to this script and save the file as 'cookies.txt'.")
        print("--------------------------------------------------------------------------------\n")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except Exception as e:
            print(f"Error: Failed to create output directory '{output_dir}'. Details: {e}")
            sys.exit(1)

    ydl_opts = {
        # Dynamic resolution based on user input
        # Defaults to best video under target resolution + best audio
        'format': f'bestvideo[height<={resolution}]+bestaudio/best', 
        
        'outtmpl': os.path.join(os.path.abspath(output_dir), '%(title)s.%(ext)s'),
        'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
        'quiet': False,
        'no_warnings': False,
        # Jawne pozwolenie na użycie Node.js jako środowiska JS, jeśli Deno jest niedostępny
        'js_runtimes': {
            'deno': {}, 
            'node': {}
        },
        # Force mobile clients to bypass 403 Forbidden errors
        'extractor_args': {
            'youtube': ['player_client=ios,android']
        }
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Automatically trim garbage from links (keep only what's before '&')
            links = [line.strip().split('&')[0] for line in f if line.strip()]

        if not links:
            print("The file is empty.")
            return

        print(f"Found {len(links)} links. Starting download...\n")

        for index, link in enumerate(links, 1):
            try:
                # Automatyczne wyciąganie domeny z linku i ustawianie jako Referer
                parsed_url = urlparse(link)
                dynamic_referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
                
                current_opts = ydl_opts.copy()
                current_opts['http_headers'] = {'Referer': dynamic_referer}

                with yt_dlp.YoutubeDL(current_opts) as ydl:
                    print(f"\n[{index}/{len(links)}] Downloading clean link: {link} (Referer: {dynamic_referer})")
                    ydl.download([link])
            except Exception as e:
                print(f"Error downloading {link}: {e}")

        print("\nFinished processing the list.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Display help if no arguments are provided
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    epilog_text = """
Authentication (For Private & Age-Restricted Videos):
If you need to download age-restricted, private, or premium videos, you must
provide your browser cookies.

How to set it up:
1. Install the 'Get cookies.txt LOCALLY' add-on for Google Chrome.
2. Go to YouTube.com, click the extension, and export your cookies in Netscape format.
3. Create an 'auth' directory next to this script and save the file as 'cookies.txt'.

Author Information:
Author:  Roman Pindela
Email:   roman.pindela@gmail.com
GitHub:  https://github.com/romanpindela
Version: 1.0.0
"""
    parser = argparse.ArgumentParser(
        description="A Python script to batch download videos from YouTube and other platforms up to 1080p.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog_text
    )
    
    parser.add_argument("file_path", help="Path to the text file containing video links (one link per line).")
    parser.add_argument("-o", "--output-dir", default=os.path.dirname(os.path.abspath(__file__)), help="Directory where videos will be saved. Defaults to the script's directory.")
    parser.add_argument("-r", "--resolution", default="1080", help="Maximum vertical resolution to download (e.g., 720, 1080, 1440, 2160). Defaults to 1080.")
    parser.add_argument("-v", "--version", action="version", version="YouTube Downloader v1.0.0 by Roman Pindela")
    
    args = parser.parse_args()
    download_videos(args.file_path, args.output_dir, args.resolution)