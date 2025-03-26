from flask import Flask, request, jsonify, abort
from flask_restx import Api, Resource
import requests
from bs4 import BeautifulSoup
import os
import base64
from dotenv import load_dotenv
load_dotenv()


# Initialize Flask and Flask-RESTx
app = Flask(__name__)
api = Api(app)

# Fetch the access token from Secret Manager
secret_id = os.environ.get('CLIENT_SECRET')
access_token_genius = os.environ.get('CLIENT_ACCESS_TOKEN')


################ ^ GENIUS ACCESS ABOVE ################

# Global variable to track access token and expiryaccess_token = None
token_expiry = 0

#     return access_token
SPOTIFY_BASE_URL = 'https://api.spotify.com/v1'

spotify_client_id = os.environ.get('SPOTIFY_CLIENT_ID')
spotify_client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET')

client_credentials = f'{spotify_client_id}:{spotify_client_secret}'

encodeed_credentials = base64.b64encode(client_credentials.encode("utf-8")).decode("utf-8")

AUTH_HEADER = {'Authorization': f'Basic {encodeed_credentials}',
          'Content-Type' : 'application/x-www-form-urlencoded'}  # Authentifcation is typically passed into the HTTP 


response = requests.post("https://accounts.spotify.com/api/token", headers=AUTH_HEADER, data={"grant_type": "client_credentials"})


token_info = response.json()

access_token = token_info['access_token']

SPOTIFY_HEADER = {'Authorization' : f'Bearer {access_token}'}


################ ^ SPOTIFY ACCESS ABOVE ################
# Genius API credentials
if not access_token_genius:
    print("Error: Access token cannot be None!")
else:
    print("Access Token is good!")


# Get access to the genius api
GENIUS_BASE_URL = "https://api.genius.com"
GENIUS_HEADERS = {"Authorization": f"Bearer {access_token_genius}"}

# Get access to the spotify api
SPOTIFY_BASE_URL = 'https://api.spotify.com/v1'

class MusicInfo:
    # Fetch song ID by searching with artist name and song title
    def Get_Song_Id_By_Search(self, artist_name, song_title):
        search_query = f"{song_title} {artist_name}"
        search_url = f"{GENIUS_BASE_URL}/search?q={search_query}"
        response = requests.get(search_url, headers=GENIUS_HEADERS)
        if response.status_code == 200:
            data = response.json()
            for hit in data["response"]["hits"]:
                song = hit["result"]
                primary_artist = song["primary_artist"]["name"].lower()
                if song_title.lower() in song["title"].lower() and artist_name.lower() in primary_artist:
                    return song["id"]
        return None


# Scrape a Genius webpage for lyrics
class ScrapeLyrics:
    # Scrape lyrics using song ID
    def Lyric(self, song_id):
        url = f"https://genius.com/songs/{song_id}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        lyrics_data = soup.find_all('div', attrs={'data-lyrics-container': "true"})
        lyrics = "".join([i.get_text(separator=" ").strip() for i in lyrics_data])
        return lyrics.replace('[', '\n\n[').replace(']', ']\n\n')

# Get the lyrics
class Lyrics(Resource):

    # get will retrive the song data from the firebase database
    def get(self):
        artist_name = request.args.get('artist_name')
        song_title = request.args.get('song_title')

        # Check if artist name and song title are provided
        if not artist_name or not song_title:
            return {"Error": "Missing artist_name or song_title"}, 400

        artist_key = artist_name.lower().replace(" ", "_")

    # put will write data to the firbase database.
    def put(self):
        artist_name = request.args.get('artist_name')
        song_title = request.args.get('song_title')

        # Check if artist name and song title are provided
        if not artist_name or not song_title:
            return {"error": "Missing artist_name or song_title"}, 400

        # Fetch song ID from Genius API
        song_id = MusicInfo().Get_Song_Id_By_Search(artist_name, song_title)
        if not song_id:
            return {"Error": "Song not found"}, 404

        # Scrape lyrics for the song
        lyrics = ScrapeLyrics().Lyric(song_id)

        # Create song data to add/update
        new_song = {
            "song_title": song_title,
            "lyrics": lyrics
        }
        return jsonify({"message": "Song added/updated successfully!"})

# Get artist data from Spotify
class Spotify(Resource):
    def get(self, artist_name):

        search_url = f"{SPOTIFY_BASE_URL}/search"

        params = {
            'q': artist_name,   # This will basically set up the query to search for the artist_name
            'type': 'artist',   # Handles type specifacation
            'limit': 1  # Limit will specify how many results get loaded in
        }

        response = requests.get(search_url, headers=SPOTIFY_HEADER, params=params)
        if response.status_code != 200:
            return {'Error': 'Couldn\'t fetch artist info', 'status_code': response.status_code}, response.status_code

        data = response.json()

        # In the case that artist is empty we will be using get
        artists = data.get('artists', {}).get('items', [])

        if not artists:
            return {'Error': 'Couldn\'t find artist'}, 404

        artist = artists[0]  # The first result if the artist list will be the most accurate searched result
        artist_id = artist.get('id')
        
        ####################Get Artist ^ above########################

        params = {
            'include_group' : 'album'
        }

        album_url = f'{SPOTIFY_BASE_URL}/artists/{artist_id}/albums'

        response = requests.get(album_url, headers=SPOTIFY_HEADER, params=params)

        data = response.json()

        # Some artist done have albums so will need to check for null cases
        albums = data.get('items', [])
        album_list = []


        # Go through all of the found albums
        for album in albums:
            if album.get('album_type') == 'album':  # Only get full albums, not singles or compilations
                album_name = album.get('name', '')
                release_date = album.get('release_date', '')
                
                # Get the tracks of the album by making a request for the album's details
                album_id = album.get('id')
                album_url = f'{SPOTIFY_BASE_URL}/albums/{album_id}'
                album_response = requests.get(album_url, headers=SPOTIFY_HEADER)
                
                if album_response.status_code == 200:
                    album_data = album_response.json()
                    track_list = [track['name'] for track in album_data.get('tracks', {}).get('items', [])]
                else:
                    track_list = []  # In case of failure to get the tracks

                # Store the album data in the list as a dictionary
                album_info = {
                    'name': album_name,
                    'released': release_date,
                    'tracks': track_list
                }

                album_list.append(album_info)

        # Parse the data
        artist_info = {
            'name': artist.get('name'),
            'spotify id' : artist.get('id'),
            'followers': artist.get('followers', {}).get('total', 0),
            'genres': artist.get('genres', []),
            #'popularity': artist.get('popularity'),
            'albums' : album_list,
            'num albums' : len(album_list)
        }
        return artist_info, 200

@app.route('/lyrics-test')
def lyrics_test():
    artist = request.args.get('artist_name')
    title = request.args.get('song_title')
    song_id = MusicInfo().Get_Song_Id_By_Search(artist, title)
    if not song_id:
        return {"error": "Song not found on Genius"}, 404
    lyrics = ScrapeLyrics().Lyric(song_id)
    return jsonify({"lyrics": lyrics})

@app.route('/spotify-test')
def spotify_test():
    artist_name = request.args.get('artist_name')
    if not artist_name:
        return {"error": "Missing artist_name"}, 400

    spotify_info, status_code = Spotify().get(artist_name=artist_name)
    return jsonify(spotify_info), status_code

# Add routes to the API
api.add_resource(Lyrics, '/lyrics')

if __name__ == '__main__':
    app.run(debug=True)
