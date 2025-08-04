from .base import get_spotify_token
import requests

def search_tracks(query:str, type:str="track" ,limit:int=10) -> dict:
    """Search for tracks on Spotify."""
    try:
        access_token = get_spotify_token()
        search_url= 'https://api.spotify.com/v1/search'
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        # The query must be URL encoded
        params = {
            'q': query,
            'type': type,  # e.g., 'track', 'album', 'artist'
            'limit': 10  # optional: limit number of results
        }

        response = requests.get(search_url, headers=headers, params=params)
        results = response.json()
        
        output=[]

        for track in results[type+"s"]['items']:
            if type=="track":
                output.append({
                    'name': track['name'],
                    'artists': track['artists'],
                    'album': track['album']['name'],
                    'release_date': track['album']['release_date']
                })
            elif type=="album":
                output.append({
                    'name': track['name'],
                    'artists': track['artists'],
                    'release_date': track['release_date']
                })
            elif type=="artist":
                output.append({
                    'name': track['name'],
                    'genres': track['genres'],
                    'popularity': track['popularity']
                })
            elif type=="playlist":
                output.append({
                    'name': track['name'],
                    'owner': track['owner']['display_name'],
                    'tracks_count': track['tracks']['total']
                })
            elif type=="show":
                output.append({
                    'name': track['name'],
                    'publisher': track['publisher'],
                    'total_episodes': track['total_episodes']
                })
            elif type=="episode":
                output.append({
                    'name': track['name'],
                    'release_date': track['release_date']
                })
            elif type=="audiobook":
                output.append({
                    'name': track['name'],
                    'authors': track['authors'],
                   
                })
            return output
    except requests.RequestException as e:
        print(f"An error occurred while searching for tracks: {e}")
        return {"error": str(e)}
            