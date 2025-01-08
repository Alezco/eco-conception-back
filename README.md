# eco-conception-back
Atelier d'éco-conception back-end

## Scénario Technique

Vous travaillez pour une entreprise technologique qui développe une plateforme de recommandation de films pour les utilisateurs. La plateforme utilise une API backend pour gérer les données des films, les avis des utilisateurs, et les recommandations personnalisées. Votre objectif est de construire cette API tout en appliquant des techniques d'éco-conception pour minimiser l'empreinte écologique et optimiser les performances.
### Etape 1 : Configuration Initiale avec Docker, FastAPI, Prometheus et Grafana

**1.1 Préparer l'environnement de base avec Docker**

Commencez par la structure suivante : 

```shell

eco-conception-back/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── prometheus/

```

**1.2 Définir `requirements.txt`**

```shell
fastapi
uvicorn
pydantic
```

**1.3 Créer les fichiers de configuration de Prometheus et Grafana**

Dans prometheus/, ajoutez le fichier prometheus.yml :

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "fastapi"
    static_configs:
      - targets: ["fastapi:8000"]

  - job_name: "docker"
    static_configs:
      - targets: ["localhost:9323"]

```
__Explication : Ce fichier configure Prometheus pour surveiller l'API FastAPI et les conteneurs Docker.__

Ajoutez un fichier Dockerfile dans grafana/ pour configurer un conteneur Grafana qui surveille notre API avec un tableau de bord personnalisable.

**1.4 Configurer `Dockerfile`**

Créez un fichier Dockerfile pour l'API en FastAPI :

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```

**1.5 Configurer `docker-compose.yml`**

Associez les services FastAPI, Prometheus et Grafana dans `docker-compose.yml` :

```yaml
version: "3.8"

services:
  fastapi:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app

  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - --config.file=/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - my_network

  grafana:
    image: grafana/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secret
    ports:
      - "3000:3000"
    volumes:
      - grafana:/var/lib/grafana
    networks:
      - my_network

volumes:
  grafana:

networks:
  my_network:
    driver: bridge

```

**1.6 Exécution de l'application**

```shell
docker compose up --build
```

Contrôle : Après le démarrage, accédez à Grafana sur http://localhost:3000. L'identifiant (par défaut) est `admin`, et le mot de passe est celui renseigné dans `GF_SECURITY_ADMIN_PASSWORD` (`docker-compose.yml`), ici `secret`. Ensuite, ajoutez Prometheus comme source de données (http://prometheus:9090). 

Pour remonter les métriques de FastAPI à Grafana, utilisez [Prometheus FastAPI Instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator)

Vous pourrez visualiser les premières métriques de FastAPI.

### Etape 2 : Création de l’API de Base avec FastAPI et SQLite

1. Créez le fichier app/main.py avec des endpoints de base. 
2. Ajoutez app/models.py : Pour gérer les modèles de données et les connexions à SQLite.

**`main.py`**

```python
from fastapi import FastAPI, HTTPException
from typing import List
from models import Movie, Review, get_movies, get_movie, create_review, get_recommendations

app = FastAPI()

# Endpoint pour obtenir la liste complète des films
@app.get("/movies", response_model=List[Movie])
def read_movies():
    return get_movies()

# Endpoint pour obtenir les détails d'un film spécifique
@app.get("/movies/{id}", response_model=Movie)
def read_movie(id: int):
    movie = get_movie(id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Film non trouvé")
    return movie

# Endpoint pour ajouter un avis
@app.post("/reviews", response_model=Review)
def add_review(review: Review):
    return create_review(review)

# Endpoint pour obtenir des recommandations de films
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

# Définition des modèles de données

class Movie(BaseModel):
    id: int
    title: str
    genre: str

class Review(BaseModel):
    movie_id: int
    rating: float
    comment: str

# Fonction pour obtenir une connexion à la base de données SQLite
def get_db_connection():
    conn = sqlite3.connect('test.db')
    conn.row_factory = sqlite3.Row
    return conn

# Fonction pour initialiser la base de données
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

# Fonction pour récupérer tous les films
def get_movies() -> List[Movie]:
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies')
        return [Movie(**row) for row in cursor.fetchall()]

# Fonction pour récupérer un film spécifique par son ID
def get_movie(id: int) -> Optional[Movie]:
    with get_db_connection() as conn:
        cursor = conn.execute('SELECT * FROM movies WHERE id = ?', (id,))
        row = cursor.fetchone()
        return Movie(**row) if row else None

# Fonction pour ajouter un avis pour un film
def create_review(review: Review) -> Review:
    with get_db_connection() as conn:
        conn.execute('INSERT INTO reviews (movie_id, rating, comment) VALUES (?, ?, ?)',
                     (review.movie_id, review.rating, review.comment))
        conn.commit()
        return review

# Fonction pour obtenir des recommandations de films (exemple : sélection aléatoire)
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
Si vous n'avez pas Apache Benchmark sur votre machine, installez la dépendance et lancez :
```shell
ab -n 1000 -c 10 http://127.0.0.1:8000/movies
```


### Etape 3 : Population de la base de données avec des données factices

1. Ajoutez faker pour générer des données fictives : Ajoutez `faker` à `requirements.txt` pour enrichir la base de données. 
2. Créez populate_db.py : Exécutez ce script pour remplir la base de données avec des films et des critiques factices.

**`populate_db.py`**

```python
from faker import Faker
import sqlite3
import sys

# Initialiser Faker pour générer des données fictives
fake = Faker()

# Fonction pour créer un film fictif
def create_fake_movie():
    return {
        'title': fake.sentence(nb_words=3),
        'genre': fake.word(ext_word_list=['Action', 'Comedy', 'Drama', 'Fantasy', 'Horror', 'Mystery', 'Romance', 'Thriller', 'Western'])
    }

# Fonction pour créer un avis fictif pour un film
def create_fake_review(movie_id):
    return {
        'movie_id': movie_id,
        'rating': fake.random_int(min=1, max=5),
        'comment': fake.sentence()
    }

# Fonction pour peupler la base de données avec des films et des avis fictifs
def populate_db(num_movies: int):
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()

    # Peupler la table des films
    movies = [create_fake_movie() for _ in range(num_movies)]
    cursor.executemany('INSERT INTO movies (title, genre) VALUES (:title, :genre)', movies)

    # Récupérer tous les IDs des films insérés
    cursor.execute('SELECT id FROM movies')
    movie_ids = [row[0] for row in cursor.fetchall()]

    # Peupler la table des avis pour chaque film avec un nombre d'avis aléatoire
    reviews = [
        create_fake_review(movie_id)
        for movie_id in movie_ids
        for _ in range(fake.random_int(min=1, max=5))
    ]
    cursor.executemany('INSERT INTO reviews (movie_id, rating, comment) VALUES (:movie_id, :rating, :comment)', reviews)

    # Enregistrer les modifications et fermer la connexion
    conn.commit()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            num_movies = int(sys.argv[1])
            print(f"Création de {num_movies} films et de leurs avis associés...")
            populate_db(num_movies)
            print("Base de données peuplée avec succès.")
        except ValueError:
            print("Le nombre de films doit être un entier.")
    else:
        print("Usage: python populate_db.py <nombre_de_films>")

```
Exéution du script pour peupler la base de données avec 100 films :

```shell
python populate_db.py 1000000
```

Observation des performances : Utilisez Prometheus et Grafana pour observer la consommation de ressources avant et après la génération de données.

### Etape 4 : Introduction de la pagination

Appliquez la pagination pour optimiser la récupération des données :

```python
@app.get("/movies", response_model=List[Movie])
def read_movies(page: int = 1, limit: int = 10):
    return get_movies(page, limit)

```
Contrôle : Mesurez à nouveau les performances pour observer l'impact de la pagination.

### Etape 5 : Implémentation de la Mise en Cache

Redis est ajouté pour réduire les temps de réponse pour des requêtes répétitives.

1. Ajoutez Redis à docker-compose.yml

```yaml

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"

```

2. Mettre à jour main.py pour inclure le caching

```python
import redis
import json

r = redis.Redis(host='redis', port=6379, db=0)

@app.get("/movies", response_model=List[Movie])
def read_movies(page: int = 1, limit: int = 10):
    cache_key = f"movies:{page}:{limit}"
    cached_movies = r.get(cache_key)
    if cached_movies:
        return json.loads(cached_movies)

    movies = get_movies(page, limit)
    r.setex(cache_key, 3600, json.dumps([movie.dict() for movie in movies]))
    return movies

```

Contrôle : Lancez plusieurs requêtes pour /movies et observez comment Redis réduit les temps de réponse pour des requêtes similaires.


### Etape 6 : Optimisation de la Base de Données avec des Index

1. Ajout d'Index

Améliorez les performances des requêtes en ajoutant des index. Utilisez les commandes suivantes dans le shell SQLite :

```sql
-- Index sur le titre des films
CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title);

-- Index sur l'identifiant du film dans la table des avis
CREATE INDEX IF NOT EXISTS idx_reviews_movie_id ON reviews(movie_id);

```

Exécutez les commandes ci-dessus dans le shell SQLite pour ajouter des index sur les colonnes `title` de la table `movies` et `movie_id` de la table `reviews`.



### Etape 7 : Ajout d'un proxy avec Nginx pour la gestion du cache Redis

1. Configurez Nginx pour optimiser le flux de requêtes et améliorer les performances de cache :

Créez un fichier nginx.conf avec le code suivant :

```nginx
events {
    # Configuration minimale pour satisfaire NGINX
    worker_connections 1024;
}
http {
    # Déclaration de la zone de cache
    proxy_cache_path /var/cache/nginx/redis_cache levels=1:2 keys_zone=redis_cache:10m max_size=1g inactive=60m use_temp_path=off;

    server {
        listen 80;

        location / {
            proxy_pass http://fastapi:8000;
            proxy_cache redis_cache;
            proxy_cache_valid 200 1h;
        }

        location /static/ {
            alias /app/static/;
        }
    }
}
```

2. Mettre à jour docker-compose.yml pour inclure Nginx :

```yaml
services:
  nginx:
    image: nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - fastapi
      - redis
```
