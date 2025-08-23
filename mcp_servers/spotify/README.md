# Spotify MCP Server

##  Purpose
The **Spotify MCP Server** provides an interface to interact with Spotify through the Model Context Protocol (MCP).  
It allows you to:
- Search for tracks, artists, albums, playlists, shows, and episodes.
- Get stats and descriptions for each item.
- Save songs, albums, and playlists to your Spotify library.
- Follow artists and shows.
- Retrieve user-specific Spotify data.

---

##  Installation & Setup


1) Create a Python Virtual Environment
   

```
    python -m venv venv
```

2) Activate the virtual environment

MacOS / Linux:
   
```
    source venv/bin/activate
```






Windows:
    
```
    venv\Scripts\activate
```

3) Install Dependencies
   
```
    pip install -r requirements.txt
```

## API Credentials Setup


1) Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).

2) Create a new app.

3) Set the Redirect URI to:
https://www.google.com
NOTE: This is an important step — without it, authentication will fail.

The first time you call a tool from this server, you will be asked to authorize Spotify.
After logging in, copy the redirected URL from your browser and paste it into the terminal when prompted.

Done!

## Environment Variables

Create a .env file in the project root with the following variables:

```
SPOTIFY_CLIENT_ID=your_client_id_here

SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

Replace your_client_id_here and your_client_secret_here with the values from your Spotify Developer Dashboard.

## Running the Server

```
python server.py
```

Video Testing Demo :

https://www.youtube.com/watch?v=RTzDY8QyzCM
