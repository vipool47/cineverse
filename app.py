import concurrent.futures
import os
import pickle
import random
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="MovieVerse",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------
st.markdown(
    """
    <style>
        .stApp {
            background:
                radial-gradient(circle at 15% 0%, rgba(91, 75, 160, 0.16), transparent 30%),
                var(--background-color);
        }

        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero {
            padding: 1.8rem 2rem;
            border: 1px solid rgba(128, 128, 128, 0.22);
            border-radius: 18px;
            background: linear-gradient(
                120deg,
                rgba(91, 75, 160, 0.20),
                rgba(40, 120, 150, 0.10)
            );
            margin-bottom: 1.5rem;
        }

        .hero h1 {
            margin: 0;
            font-size: clamp(2rem, 4vw, 3rem);
            letter-spacing: -1.5px;
        }

        .hero p {
            margin: 0.55rem 0 0;
            opacity: 0.78;
            font-size: 1.05rem;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px;
        }

        .movie-title {
            font-size: 1.05rem;
            font-weight: 650;
            line-height: 1.35;
            min-height: 2.8rem;
            margin-top: 0.65rem;
        }

        .muted {
            opacity: 0.7;
            font-size: 0.9rem;
        }

        div.stButton > button {
            border-radius: 10px;
            font-weight: 600;
            min-height: 2.7rem;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.16);
        }

        footer {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# Configuration and data loading
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
API_KEY = os.getenv("TMDB_API_KEY", "add_your_api_key_here")
TMDB_BASE_URL = "https://api.themoviedb.org/3"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"


@st.cache_resource
def load_movie_data():
    """Load the existing precomputed movie dataset and similarity matrix."""
    with open(BASE_DIR / "similarity.pkl", "rb") as file:
        similarity_data = pickle.load(file)

    with open(BASE_DIR / "movie_dict.pkl", "rb") as file:
        movie_data = pickle.load(file)

    movie_frame = pd.DataFrame(movie_data)
    return similarity_data, movie_frame


try:
    similarity, movies = load_movie_data()
except FileNotFoundError as error:
    st.error(f"Required dataset file not found: {error.filename}")
    st.info("Make sure movie_dict.pkl and similarity.pkl are in the project directory.")
    st.stop()
except Exception as error:
    st.error(f"Could not load the movie dataset: {error}")
    st.stop()


if movies.empty or "title" not in movies.columns:
    st.error("The movie dataset is empty or does not contain a 'title' column.")
    st.stop()


# ---------------------------------------------------------------------
# TMDB API helpers
# ---------------------------------------------------------------------
def tmdb_get(endpoint, params=None):
    """Send a request to TMDB and return its JSON response."""
    request_params = {"api_key": API_KEY}
    if params:
        request_params.update(params)

    response = requests.get(
        f"{TMDB_BASE_URL}/{endpoint.lstrip('/')}",
        params=request_params,
        timeout=8,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_director(movie_id):
    try:
        data = tmdb_get(f"movie/{movie_id}/credits")
        for crew_member in data.get("crew", []):
            if crew_member.get("job") == "Director":
                return crew_member.get("name", "Unknown")
    except requests.exceptions.RequestException:
        pass
    except (ValueError, KeyError):
        pass

    return "Unknown"


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_trailer(movie_id):
    try:
        data = tmdb_get(f"movie/{movie_id}/videos")
        for video in data.get("results", []):
            if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                return f"https://www.youtube.com/watch?v={video.get('key')}"
    except requests.exceptions.RequestException:
        pass
    except (ValueError, KeyError):
        pass

    return None


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_imdb_id(movie_id):
    try:
        data = tmdb_get(f"movie/{movie_id}")
        return data.get("imdb_id")
    except requests.exceptions.RequestException:
        return None
    except (ValueError, KeyError):
        return None


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_movie_details(movie_title):
    try:
        data = tmdb_get("search/movie", {"query": movie_title})
        results = data.get("results", [])

        if not results:
            return None, "N/A", "N/A", "No overview available.", "Unknown", None, None

        movie_data = results[0]
        movie_id = movie_data["id"]

        poster_path = movie_data.get("poster_path")
        poster_url = f"{POSTER_BASE_URL}{poster_path}" if poster_path else None

        release_date = movie_data.get("release_date") or "N/A"
        rating = movie_data.get("vote_average", "N/A")
        overview = movie_data.get("overview") or "No overview available."

        director = fetch_director(movie_id)
        trailer_url = fetch_trailer(movie_id)
        imdb_id = fetch_imdb_id(movie_id)
        imdb_link = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None

        return (
            poster_url,
            release_date,
            rating,
            overview,
            director,
            trailer_url,
            imdb_link,
        )

    except requests.exceptions.RequestException:
        return None, "N/A", "N/A", "Movie information is currently unavailable.", "Unknown", None, None
    except (ValueError, KeyError, TypeError):
        return None, "N/A", "N/A", "Movie information is currently unavailable.", "Unknown", None, None


@st.cache_data(show_spinner=False, ttl=900)
def fetch_trending_movies():
    try:
        data = tmdb_get("trending/movie/day")
        return [movie.get("title") for movie in data.get("results", [])[:5] if movie.get("title")]
    except requests.exceptions.RequestException:
        return []
    except (ValueError, KeyError, TypeError):
        return []


# ---------------------------------------------------------------------
# Recommendation logic
# ---------------------------------------------------------------------
def recommend(movie_title):
    matching_movies = movies.index[movies["title"] == movie_title]

    if len(matching_movies) == 0:
        return []

    movie_index = matching_movies[0]
    distances = similarity[movie_index]

    similar_indices = sorted(
        enumerate(distances),
        key=lambda item: item[1],
        reverse=True,
    )[1:6]

    recommended_titles = [
        movies.iloc[index].title for index, _score in similar_indices
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        details = list(executor.map(fetch_movie_details, recommended_titles))

    return [
        (title, *movie_details)
        for title, movie_details in zip(recommended_titles, details)
    ]


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------
with st.sidebar:
    st.title("MovieVerse")
    st.caption("Discover your next favourite movie")

    st.divider()

    dark_mode = st.toggle("Dark appearance", value=True)
    mood = st.selectbox(
        "Choose your mood",
        ["Adventure", "Happy", "Thrilling", "Romantic", "Random"],
    )

    st.divider()
    st.subheader("Trending today")

    trending_movies = fetch_trending_movies()
    if trending_movies:
        for number, title in enumerate(trending_movies, start=1):
            st.write(f"{number}. {title}")
    else:
        st.caption("Trending movies are temporarily unavailable.")

    st.divider()
    st.caption("Movie information provided by TMDB.")


# Preserve the dark/light toggle as a simple page-level styling choice.
if not dark_mode:
    st.markdown(
        """
        <style>
            .stApp {
                background: #f6f7fb;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>Find your next favourite movie.</h1>
        <p>Choose a movie you enjoy and discover five recommendations based on similarity.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if API_KEY == "add_your_api_key_here":
    st.warning(
        "Add your TMDB API key to the TMDB_API_KEY environment variable "
        "to enable posters, movie details, trailers, IMDb links, and trending movies."
    )

left, right = st.columns([3, 1])

with left:
    selected_movie_name = st.selectbox(
        "Select a movie",
        movies["title"].dropna().values,
        index=0,
        key="selected_movie",
    )

with right:
    st.write("")
    st.write("")
    lucky_clicked = st.button("I'm feeling lucky", use_container_width=True)

if lucky_clicked:
    random_movie = random.choice(movies["title"].dropna().values)
    st.session_state.selected_movie = random_movie
    st.rerun()

recommend_clicked = st.button(
    "Get recommendations",
    type="primary",
    use_container_width=True,
)

if recommend_clicked:
    with st.spinner("Finding movies you might like..."):
        movie_details = recommend(st.session_state.selected_movie)

    st.session_state.recommendation_results = movie_details
    st.session_state.recommendation_for = st.session_state.selected_movie


# Keep recommendations visible after Streamlit reruns.
if st.session_state.get("recommendation_results") is not None:
    results = st.session_state.recommendation_results
    recommendation_for = st.session_state.get("recommendation_for", "")

    st.divider()
    st.subheader("Recommended for you")
    st.caption(f"Because you selected: {recommendation_for}")

    if results:
        columns = st.columns(5, gap="medium")

        for index, item in enumerate(results):
            (
                title,
                poster_url,
                release_date,
                rating,
                overview,
                director,
                trailer_url,
                imdb_link,
            ) = item

            with columns[index]:
                with st.container(border=True):
                    if poster_url:
                        st.image(poster_url, use_container_width=True)
                    else:
                        st.markdown(
                            """
                            <div style="
                                height: 250px;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                border-radius: 8px;
                                background: rgba(128,128,128,0.12);
                                text-align: center;
                                padding: 1rem;
                            ">
                                Poster unavailable
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    st.markdown(f'<div class="movie-title">{title}</div>', unsafe_allow_html=True)
                    st.caption(f"Release: {release_date}")
                    st.caption(f"TMDB rating: {rating}/10")
                    st.write(f"**Director:** {director}")

                    with st.expander("Movie overview"):
                        st.write(overview)

                    if trailer_url:
                        st.link_button("Watch trailer", trailer_url, use_container_width=True)

                    if imdb_link:
                        st.link_button("View on IMDb", imdb_link, use_container_width=True)

                    youtube_query = requests.utils.quote(f"full {title} movie")
                    st.link_button(
                        "Search on YouTube",
                        f"https://www.youtube.com/results?search_query={youtube_query}",
                        use_container_width=True,
                    )
    else:
        st.warning("No recommendations were found for this selection.")


# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------
st.divider()
st.markdown(
    """
    <div style="text-align:center; opacity:0.65; padding:0.5rem 0 1rem;">
        MovieVerse · Built with Python and Streamlit · For educational purposes
    </div>
    """,
    unsafe_allow_html=True,
)
