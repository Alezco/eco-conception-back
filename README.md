# eco-conception-back
Atelier d'éco-conception back-end

## Scénario Technique

Vous travaillez pour une entreprise technologique qui développe une plateforme de recommandation de films pour les utilisateurs. La plateforme utilise une API backend pour gérer les données des films, les avis des utilisateurs, et les recommandations personnalisées. Votre objectif est de construire cette API tout en appliquant des techniques d'éco-conception pour minimiser l'empreinte écologique et optimiser les performances.

### Etape 1 : Configuration Initiale

**Objectif : Mettre en place un environnement Docker avec FastAPI et SQLite.**

***requirements.txt***

```shell
fastapi
uvicorn
pydantic
sqlite
```

### Etape 2 : Création de l'API de Base

**`app.py`**

```python

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


```

***Code pour `models.py`***

```python
# models.py
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

class Movie(BaseModel):
    id: int
    title: str
    genre: str

class Review(BaseModel):
    movie_id: int
    rating: float
    comment: str

def get_db_connection():
    conn = sqlite3.connect('test.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS movies (
                            id INTEGER PRIMARY KEY,
                            title TEXT NOT NULL,
                            genre TEXT NOT NULL)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS reviews (
                            id INTEGER PRIMARY KEY,
                            movie_id INTEGER,
                            rating REAL,
                            comment TEXT,
                            FOREIGN KEY (movie_id) REFERENCES movies (id))''')

init_db()

def get_movies(page: int = 1, limit: int = 10) -> List[Movie]:
    offset = (page - 1) * limit
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies LIMIT ? OFFSET ?', (limit, offset))
        return [Movie(**row) for row in cursor.fetchall()]

def get_movie(id: int) -> Optional[Movie]:
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies WHERE id = ?', (id,))
        row = cursor.fetchone()
        return Movie(**row) if row else None

def create_review(review: Review) -> Review:
    with get_db_connection() as conn:
        conn.execute('INSERT INTO reviews (movie_id, rating, comment) VALUES (?, ?, ?)',
                     (review.movie_id, review.rating, review.comment))
        conn.commit()
        return review

def get_recommendations() -> List[Movie]:
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies ORDER BY RANDOM() LIMIT 5')
        return [Movie(**row) for row in cursor.fetchall()]

```

#### Exécution de l'Application

**Installation des dépendances**

```shell
pip install -r requirements.txt
uvicorn app:app --reload
```

**Mesure des Performances Initiales**

```shell
ab -n 1000 -c 10 http://127.0.0.1:8000/movies
```

**Population de la base de données avec des données factices**

- Installatoin de `faker`

Ajoutons `faker` à notre fichier de prérequis `requirements.txt`.

```shell
fastapi
uvicorn
pydantic
sqlite
# On rajoute faker
faker
```

Script pour Populer la Base de Données

Créons un script pour générer et insérer des données factices dans la base de données SQLite.

`populate_db.py`
```python
from faker import Faker
import sqlite3

fake = Faker()

def create_fake_movie():
    return {
        'title': fake.sentence(nb_words=3),
        'genre': fake.word(ext_word_list=['Action', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Thriller', 'Western'])
    }

def create_fake_review(movie_id):
    return {
        'movie_id': movie_id,
        'rating': fake.random_int(min=1, max=5),
        'comment': fake.sentence()
    }

def populate_db():
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    # Populate movies table
    movies = [create_fake_movie() for _ in range(100000)]
    cursor.executemany('INSERT INTO movies (title, genre) VALUES (:title, :genre)', movies)
    
    # Get all movie IDs
    cursor.execute('SELECT id FROM movies')
    movie_ids = [row[0] for row in cursor.fetchall()]

    # Populate reviews table
    reviews = [create_fake_review(movie_id) for movie_id in movie_ids for _ in range(fake.random_int(min=1, max=10))]
    cursor.executemany('INSERT INTO reviews (movie_id, rating, comment) VALUES (:movie_id, :rating, :comment)', reviews)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    populate_db()
```

### Etape 3 : Introduction à l'Éco-Conception - Pagination

**Implémentation de la Pagination**

Modification de la route GET `/movies` pour ajouter la pagination.

-   Mise à Jour `main.py`
```python
@app.get("/movies", response_model=List[Movie])
def read_movies(page: int = 1, limit: int = 10):
    return get_movies(page, limit)
```

**Mesure des Performances après l'implémentation de la pagination**

```shell
ab -n 1000 -c 10 http://127.0.0.1:8000/movies
```

### Etape 4 : Mise en oeuvre du caching avec Redis

Maintenant que l'API de base est fonctionnelle et que nous avons ajouté la pagination, passons à `docker-compose` pour intégrer `Redis` pour le caching et optimiser la base de données.

**Ajout du fichier `Dockerfile`**
```shell
# Dockerfile
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY app/requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste de l'application
COPY app .

# Commande pour lancer l'application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Ajout du fichier `docker-compose.yml`
```shell
version: '3.8'

services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app
    environment:
      - DATABASE_URL=sqlite:///./test.db
    command: uvicorn app:app --host 0.0.0.0 --port 8000

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

**Mise à jour du `main.py` pour le caching avec `redis`**
```python
# app.py
import redis
import json
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from models import Movie, Review, get_movies, get_movie, create_review, get_recommendations

app = FastAPI()

r = redis.Redis(host='redis', port=6379, db=0)

def get_redis_connection():
    return r

@app.get("/movies", response_model=List[Movie])
def read_movies(page: int = 1, limit: int = 10, redis_conn=Depends(get_redis_connection)):
    cache_key = f"movies:{page}:{limit}"
    cached_movies = redis_conn.get(cache_key)
    
    if cached_movies:
        return json.loads(cached_movies)
    
    movies = get_movies(page, limit)
    redis_conn.setex(cache_key, 3600, json.dumps([movie.dict() for movie in movies]))  # Cache for 1 hour
    return movies
```
**Exécution avec `docker-compose`**
```shell
docker-compose up --build
```

## Conclusion

...
