CREATE TABLE artists (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    spotify_id TEXT NOT NULL,
    popularity INT NOT NULL,
    image_url TEXT
);