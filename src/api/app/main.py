import asyncpg
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Artist(BaseModel):
    name: str
    spotify_id: str
    popularity: int
    image_url: str

app = FastAPI()

@app.post("/artists")
async def create_artist(artist: Artist):
    conn = await asyncpg.connect(user=os.getenv("PG_USER"), password=os.getenv("PG_PASSWORD"),
                                 database=os.getenv("PG_DATABASE"), host=os.getenv("PG_HOST"))
    await conn.execute("INSERT INTO artists (name, spotify_id, popularity, image_url) VALUES ($1, $2, $3, $4)", 
                       artist.name, artist.spotify_id, artist.popularity, artist.image_url)
    await conn.close()
    return {"message": "Artist created"}

@app.get("/artists")
async def read_artists():
    conn = await asyncpg.connect(user=os.getenv("PG_USER"), password=os.getenv("PG_PASSWORD"),
                                 database=os.getenv("PG_DATABASE"), host=os.getenv("PG_HOST"))
    rows = await conn.fetch("SELECT * FROM artists")
    artists = []
    for row in rows:
        artist = dict(row)
        artist["id"] = str(artist["id"])
        artists.append(artist)
    await conn.close()
    return artists

@app.get("/artists/{artist_id}")
async def read_artist(artist_id: int):
    conn = await asyncpg.connect(user=os.getenv("PG_USER"), password=os.getenv("PG_PASSWORD"),
                                 database=os.getenv("PG_DATABASE"), host=os.getenv("PG_HOST"))
    row = await conn.fetchrow("SELECT * FROM artists WHERE id = $1", artist_id)
    await conn.close()
    print("row")
    print(row)
    if not row:
        return {"message": "Artist not found"}
    artist = dict(row)
    return artist

@app.put("/artists/{id}")
async def update_artist(id: int, name: str = None, followers: int = None, popularity: int = None):
    conn = await asyncpg.connect(user=os.getenv("PG_USER"), password=os.getenv("PG_PASSWORD"),
                                 database=os.getenv("PG_DATABASE"), host=os.getenv("PG_HOST"))
    result = await conn.execute(
        "UPDATE artists SET name = COALESCE($2, name), followers = COALESCE($3, followers), popularity = COALESCE($4, popularity) WHERE id = $1",
                                id, name, followers, popularity
        )
    if result == "UPDATE 0": 
        raise HTTPException(status_code=404, detail="Artist not found")
    return {"message": "Artist updated successfully"}

@app.delete("/artists/{id}")
async def delete_artist(id: int):
    conn = await asyncpg.connect(user=os.getenv("PG_USER"), password=os.getenv("PG_PASSWORD"),
                                 database=os.getenv("PG_DATABASE"), host=os.getenv("PG_HOST"))
    result= await conn.execute("DELETE FROM artists WHERE id = $1", id)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Artist not found")
    return {"message": "Artist deleted successfully"}