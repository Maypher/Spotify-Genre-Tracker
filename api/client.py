from api.auth import Authenticator
from functools import wraps
import requests
from dataclasses import dataclass
from typing import List, Dict

class Client:
    pass

@dataclass
class CurrentTrack:
    """
    Information about the currently playing track.

    ---
    # Parameters
    - `artists_names`: A list of the artist that created the song.
    - `artists_id`: A list of the ids of the artists that created the song.
    - `song_title`: The title of the currently playing song.
    - `song_id`: The ID of the song in the Spotify API
    - `progress_ms`: The time in ms since the song started.
    - `progress_s`: The time since the song started in seconds.
    """
    artists_names: List[str]
    artist_ids: List[str]
    song_title: str
    song_id: str
    genres: List[str]
    progress_ms: int

    @property
    def progress_s(self) -> int:
        return self.progress_ms / 1000

def requires_authentication(func):
    @wraps(func)
    def wrapper(client: Client, *args, **kwargs):
        if not client.authenticator.is_token_valid():
            client.authenticator.refresh_tokens()
        return func(client, *args, *kwargs)
    return wrapper

class Client:
    BASE_URL: str = "https://api.spotify.com/v1/"
    authenticator: Authenticator

    def __init__(self) -> None:
        # todo try to load refresh token from database
        self.authenticator = Authenticator()

    def get_current_track(self) -> CurrentTrack | None:
        """
        Returns the currently playing song in the form of `CurrentTrack`. Returns `None` if no track is being played
        """
        request_url = Client.BASE_URL + "me/player/currently-playing"        
        res = self._protected_request(request_url, "GET")

        if res.status_code == 200:
            res_dict = dict(res.json())

            song = res_dict.get("item")

            # Don't keep track of anything that's not a song (podcasts and audio books)
            if song.get("type") != "track":
                return None

            artists = song.get("artists")

            artists_names = [artist.get("name") for artist in artists]
            artists_ids = [artist.get("id") for artist in artists]
            song_title = song.get("name")
            song_id = song.get("id")
            progress_ms = res_dict.get("progress_ms")

            genres = []

            for id in artists_ids:
                artist_genres = self.get_artist(id).get("genres")
                genres += artist_genres
             
            current_track = CurrentTrack(artists_names, artists_ids, song_title, song_id, genres, progress_ms)

            return current_track 
        return None

    def get_artist(self, artist_id: str) -> Dict:
        """
        Returns the artist identified by the given id.
        """

        url = Client.BASE_URL + f"artists/{artist_id}"

        res = self._protected_request(url, "GET")

        return res.json()

    @requires_authentication
    def _protected_request(self, url: str, method: str) -> requests.Response:
        headers = {
            "Authorization": f"Bearer {self.authenticator.access_token}"
        }

        return requests.request(method=method, url=url, headers=headers)
