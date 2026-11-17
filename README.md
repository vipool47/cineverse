# CineVerse

CineVerse is a movie recommendation web app built with **Python** and
**Streamlit**. It uses precomputed movie similarity data to recommend
five movies based on a title selected by the user.

## Features

-   **Movie recommendations:** Get five similar movies based on the
    selected movie.
-   **Movie details:** View posters, release dates, ratings,
    descriptions, and directors.
-   **Trailer links:** Open available movie trailers on YouTube.
-   **IMDb links:** Open the movie's IMDb page when an IMDb ID is
    available.
-   **Trending movies:** See trending movies in the sidebar.
-   **Feeling Lucky:** Pick a random movie from the dataset.
-   **Mood selector:** Choose a mood from Adventure, Happy, Thrilling,
    Romantic, or Random.
-   **Dark mode toggle:** Switch the app's page styling between dark and
    light themes.

## Tech Stack

-   Python
-   Streamlit
-   Pandas
-   Requests
-   Pickle
-   TMDB API

## Project Files

The application expects these files in the project directory:

  -----------------------------------------------------------------------
  File                                Purpose
  ----------------------------------- -----------------------------------
  `app.py`                            Main Streamlit application

  `movie_dict.pkl`                    Serialized movie dataset used to
                                      build the movie DataFrame

  `similarity.pkl`                    Precomputed similarity data used by
                                      the recommendation algorithm
  -----------------------------------------------------------------------

The `.pkl` files are required to run the application. They are loaded
when the app starts.

## Getting Started

### 1. Clone the repository

``` bash
git clone https://github.com/vipool47/cineverse.git
cd cineverse
```

### 2. Create and activate a virtual environment

``` bash
python -m venv venv
```

**Linux / macOS:**

``` bash
source venv/bin/activate
```

**Windows:**

``` powershell
venv\Scripts\activate
```

### 3. Install dependencies

``` bash
pip install streamlit pandas requests
```

### 4. Configure your TMDB API key

Create an API key through your [TMDB
account](https://www.themoviedb.org/settings/api).
and set it in app.py


### 5. Run the application

``` bash
streamlit run app.py
```

Streamlit will provide a local URL in the terminal, usually
`http://localhost:8501`.

## How Recommendations Work

1.  The app loads the movie dataset from `movie_dict.pkl`.
2.  The selected movie is located in the dataset.
3.  Its similarity scores are read from `similarity.pkl`.
4.  Movies are sorted by similarity score, excluding the selected movie
    itself.
5.  The top five matching movies are displayed.
6.  Additional movie information is fetched from TMDB.


