# Genius + Spotify Lyrics & Artist Info API (Flask)

This Flask app lets you search for lyrics from Genius and fetch artist album data from Spotify. It uses web scraping and the Spotify API to provide quick music info from just an artist name and song title.

## Features

- 🔍 Get lyrics by scraping [Genius.com](https://genius.com)
- 🎧 Get artist info and albums from [Spotify](https://spotify.com)
- ✅ Test endpoints for fast local development
- 🌱 Environment variable support with `.env`

---

## Requirements

- Python 3.7+
- `pip install -r requirements.txt`

You’ll also need API credentials from:
- [Genius API](https://genius.com/developers)
- [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)

---

## .env File Setup

Create a `.env` file in the root of the project with the following:

```env
# Genius API
CLIENT_ID=your_genius_client_id
CLIENT_SECRET=your_genius_client_secret
CLIENT_ACCESS_TOKEN=your_genius_access_token

# Spotify API
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
```

## Run Locally
```sh
python main.py
```

**Example Test**:
`http://127.0.0.1:5000/lyrics-test?artist_name=21+Savage&song_title=No+Heart`
`http://127.0.0.1:5000/spotify-test?artist_name=21+Savage`

## API Endpoints
`GET /lyrics-test`
Scrapes lyrics for a given song.

**Query params**:

- artist_name
- song_title

```http
GET /lyrics-test?artist_name=21 Savage&song_title=No Heart
```

`GET /spotify-test`
Returns artist info and albums from Spotify.

**Query params**:

- artist_name

```http
GET /spotify-test?artist_name=21 Savage
```

## Notes
- Lyrics are scraped directly from Genius using BeautifulSoup.

- Spotify token is generated on startup using Client Credentials flow.

- This app is meant for local/testing usage. Don’t push your .env or tokens to GitHub!

