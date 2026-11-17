"""
Regenerates the model files used by app.py:
    movie_dict.pkl   (title/movie_id/tags as a dict, loaded into a DataFrame)
    similarity.pkl   (cosine similarity matrix, float32 to halve the size)
    movie_list.pkl   (the DataFrame itself, not used by app.py)

Run from the folder that contains the two TMDB CSV files:
    python generate_models.py

Same pipeline as movie_reco.ipynb.
"""
import ast
import pickle

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# The notebook defines convert3 (top 3 cast) but never uses it, so it ends up
# using the full cast list. False = match the notebook exactly.
# True = only the top 3 billed actors (the usual version of this project).
TOP_3_CAST_ONLY = False


def names(text):
    return [d["name"] for d in ast.literal_eval(text)]


def top3_names(text):
    return [d["name"] for d in ast.literal_eval(text)[:3]]


def directors(text):
    return [d["name"] for d in ast.literal_eval(text) if d["job"] == "Director"]


def squash(items):
    return [s.replace(" ", "") for s in items]


movies = pd.read_csv("tmdb_5000_movies.csv")
credits = pd.read_csv("tmdb_5000_credits.csv")

movies = movies.merge(credits, on="title")
movies = movies[["movie_id", "title", "overview", "genres", "keywords", "cast", "crew"]]
movies.dropna(inplace=True)

movies["genres"] = movies["genres"].apply(names)
movies["keywords"] = movies["keywords"].apply(names)
movies["cast"] = movies["cast"].apply(top3_names if TOP_3_CAST_ONLY else names)
movies["crew"] = movies["crew"].apply(directors)
movies["overview"] = movies["overview"].apply(lambda x: x.split())

for col in ["cast", "crew", "genres", "keywords"]:
    movies[col] = movies[col].apply(squash)

movies["tags"] = (
    movies["overview"] + movies["genres"] + movies["keywords"] + movies["cast"] + movies["crew"]
)

# Reset the index so row i of the DataFrame always matches row i of the matrix
new = movies.drop(columns=["overview", "genres", "keywords", "cast", "crew"]).reset_index(drop=True)
new["tags"] = new["tags"].apply(lambda x: " ".join(x))

cv = CountVectorizer(max_features=5000, stop_words="english")
vector = cv.fit_transform(new["tags"])  # sparse is fine for cosine_similarity

similarity = cosine_similarity(vector).astype("float32")

pickle.dump(new, open("movie_list.pkl", "wb"))
pickle.dump(similarity, open("similarity.pkl", "wb"))
pickle.dump(new.to_dict(), open("movie_dict.pkl", "wb"))

print("movies:", len(new), "| similarity:", similarity.shape, similarity.dtype)


def recommend(title, n=5):
    idx = new[new["title"] == title].index[0]
    ranked = sorted(enumerate(similarity[idx]), reverse=True, key=lambda x: x[1])[1 : n + 1]
    return [new.iloc[i].title for i, _ in ranked]


print("Spider-Man 3 ->", recommend("Spider-Man 3"))
