import sys
import os
import argparse

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    import yt_dlp
except ImportError:
    print("Błąd: Brakuje wymaganych bibliotek.")
    print("Uruchom: pip install spotipy yt-dlp")
    sys.exit(1)

# ==========================================================
# KONFIGURACJA SPOTIFY API 
# Podmień poniższe wartości na własne z developer.spotify.com
# ==========================================================
SPOTIPY_CLIENT_ID = 'TWÓJ_CLIENT_ID'
SPOTIPY_CLIENT_SECRET = 'TWÓJ_CLIENT_SECRET'

def get_playlist_tracks(playlist_url, client_id, client_secret):
    """
    Pobiera listę utworów z publicznej playlisty Spotify.
    Zwraca listę stringów w formacie "Artysta - Tytuł".
    """
    print("Łączenie z API Spotify...")
    try:
        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
        results = sp.playlist_tracks(playlist_url)
        tracks = results['items']
        
        # Obsługa paginacji, jeśli playlista ma więcej niż 100 utworów
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])
            
        query_list = []
        for item in tracks:
            track = item.get('track')
            if not track:
                continue
                
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            query_list.append(f"{artist_name} - {track_name}")
            
        print(f"Pomyślnie pobrano {len(query_list)} utworów z playlisty.")
        return query_list

    except Exception as e:
        print(f"Błąd podczas pobierania danych ze Spotify: {e}")
        print("Upewnij się, że link do playlisty jest poprawny oraz że klucze API (Client ID/Secret) zostały ustawione.")
        sys.exit(1)

def download_tracks(track_queries, output_dir):
    """
    Wyszukuje utwory na YouTube i pobiera je używając yt-dlp.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(os.path.abspath(output_dir), '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': True,
        'noplaylist': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for index, query in enumerate(track_queries, 1):
            print(f"\n[{index}/{len(track_queries)}] Wyszukiwanie i pobieranie: {query}")
            try:
                # Prefiks 'ytsearch1:' nakazuje yt-dlp znalezienie 1 wyniku dla danego hasła
                ydl.download([f"ytsearch1:{query} audio"])
            except Exception as e:
                print(f"Błąd przy pobieraniu utworu '{query}': {e}")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    parser = argparse.ArgumentParser(
        description="Skrypt do pobierania publicznych playlist ze Spotify w formie MP3.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Pamiętaj, aby przed uruchomieniem ustawić SPOTIPY_CLIENT_ID oraz SPOTIPY_CLIENT_SECRET w kodzie."
    )
    
    parser.add_argument("playlist_url", help="Link URL do publicznej playlisty Spotify.")
    parser.add_argument("-o", "--output-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "SpotifyDownloads"), help="Katalog zapisu plików MP3.")
    
    args = parser.parse_args()
    
    if SPOTIPY_CLIENT_ID == 'TWÓJ_CLIENT_ID' or SPOTIPY_CLIENT_SECRET == 'TWÓJ_CLIENT_SECRET':
        print("BŁĄD KRYTYCZNY: Nie skonfigurowano poświadczeń Spotify API!")
        print("Edytuj skrypt i wprowadź swoje klucze Client ID oraz Client Secret.")
        sys.exit(1)
        
    # 1. Odczytanie tytułów ze Spotify
    tracks_to_download = get_playlist_tracks(args.playlist_url, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET)
    
    # 2. Wyszukanie i pobranie audio z wykorzystaniem yt-dlp
    if tracks_to_download:
        download_tracks(tracks_to_download, args.output_dir)
        print("\nZakończono pobieranie playlisty!")