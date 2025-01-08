# app.py
from fastapi import FastAPI, HTTPException
from typing import List
from models import Movie, Review, get_movies, get_movie, create_review, get_recommendations

app = FastAPI()

@app.get("/movies", response_model=List[Movie])
def read_movies(page: int = 1, limit: int = 10):
    return get_movies(page, limit)

@app.get("/movies/{id}", response_model=Movie)
def read_movie(id: int):
    movie = get_movie(id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@app.post("/reviews", response_model=Review)
def add_review(review: Review):
    return create_review(review)

@app.get("/recommendations", response_model=List[Movie])
def recommendations():
    return get_recommendations()
