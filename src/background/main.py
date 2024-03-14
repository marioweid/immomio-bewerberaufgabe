import httpx
import asyncpg
import asyncio
import os
import base64

from apscheduler.schedulers.asyncio  import AsyncIOScheduler

print("Started...")

async def get_token():
    print("get_token")
    client_id = os.getenv("SPOTIFY_ID")
    client_secret = os.getenv("SPOTIFY_SECRET")
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes),"utf-8")

    headers = {
        "Authorization":"Basic " + auth_base64,
        "Content-Type":"application/x-www-form-urlencoded"
    }
    body = {"grant_type": "client_credentials"}
    async with httpx.AsyncClient() as client:
        response = await client.post("https://accounts.spotify.com/api/token", data=body, headers=headers)
    data = response.json()

    return data["access_token"]

async def get_artists():
    token = await get_token()
    headers = {
        "Authorization": f"Bearer {token}",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.spotify.com/v1/search", params={"q": "genre:pop", "type": "artist"}, headers=headers)
    data = response.json()
    print("spotify_artists_request")
    print(data)
    artists = data["artists"]["items"]
    print("Successfully fetched data")
    return artists

async def save_artists(artists):
    conn = await asyncpg.connect(user=os.getenv("PG_USER"), password=os.getenv("PG_PASSWORD"), 
                                 database=os.getenv("PG_DATABASE"), host=os.getenv("PG_HOST"))
    for artist in artists:
        existing_artist = await conn.fetchrow("SELECT * FROM artists WHERE spotify_id = $1", artist["id"])
        if existing_artist:
            if existing_artist["name"] != artist["name"] or existing_artist["popularity"] != artist["popularity"] or (existing_artist["image_url"] is None) != (artist["images"] is None) or (existing_artist["image_url"] is not None and existing_artist["image_url"] != artist["images"][0]["url"]):
                await conn.execute("UPDATE artists SET name = $1, popularity = $2, image_url = $3 WHERE spotify_id = $4", artist["name"], artist["popularity"], artist["images"][0]["url"] if artist["images"] else None, artist["id"])
        else:
            await conn.execute("INSERT INTO artists (name, spotify_id, popularity, image_url) VALUES ($1, $2, $3, $4)", artist["name"], artist["id"], artist["popularity"], artist["images"][0]["url"] if artist["images"] else None)
    await conn.close()

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job("interval", minutes=30)
async def update_artists():
    print("Scheduling update_artists()")
    artists = await get_artists()
    await save_artists(artists)

scheduler.start()

try:
    asyncio.get_event_loop().run_forever()
except (KeyboardInterrupt, SystemExit):
    pass