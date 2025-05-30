from flask import Flask, render_template, request, redirect, url_for
import pickle
import requests

app = Flask(__name__)

# Load movie data and similarity matrix
movies = pickle.load(open('movies.pkl', 'rb'))
similarity = pickle.load(open('similarity.pkl', 'rb'))

# TMDb API Key
TMDB_API_KEY = 'ad48252852be067c600f32953db9767d'  # Replace with your actual key

# Function to get recommended movies
def recommend(movie):
    movie = movie.lower()
    if movie not in movies['title'].str.lower().values:
        return []
    index = movies[movies['title'].str.lower() == movie].index[0]
    distances = list(enumerate(similarity[index]))
    sorted_movies = sorted(distances, key=lambda x: x[1], reverse=True)[1:6]
    return [movies.iloc[i[0]].title for i in sorted_movies]

# Home page
@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = []
    movie_name = ""
    movie_titles = movies['title'].tolist()

    if request.method == 'POST':
        movie_name = request.form.get('movie')
        recommendations = recommend(movie_name)

    return render_template('index.html', recommendations=recommendations, movie_name=movie_name, movies_list=movie_titles)

# Movie detail page with TMDb integration
@app.route('/movie/<movie_name>')
def movie_detail(movie_name):
    try:
        # Search for the movie
        search_url = "https://api.themoviedb.org/3/search/movie"
        search_params = {"api_key": TMDB_API_KEY, "query": movie_name}
        search_response = requests.get(search_url, params=search_params, timeout=10)
        search_response.raise_for_status()
        results = search_response.json().get("results", [])

        if not results:
            raise ValueError("No results found.")

        movie_info = results[0]
        movie_id = movie_info["id"]

        # Fetch detailed info
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        detail_response = requests.get(detail_url, params={"api_key": TMDB_API_KEY}, timeout=10)
        detail_response.raise_for_status()
        detail_data = detail_response.json()

        # Get trailer
        video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos"
        video_response = requests.get(video_url, params={"api_key": TMDB_API_KEY}, timeout=10)
        video_response.raise_for_status()
        trailer_key = next(
            (video["key"] for video in video_response.json().get("results", []) if video["type"] == "Trailer" and video["site"] == "YouTube"),
            None
        )

        # Movie data to send to template
        movie_data = {
            "title": movie_info["title"],
            "description": detail_data.get("overview", "No description available."),
            "poster_url": f"https://image.tmdb.org/t/p/w500{movie_info.get('poster_path')}" if movie_info.get("poster_path") else "/static/default.jpg",
            "rating": detail_data.get("vote_average", "N/A"),
            "genres": [genre["name"] for genre in detail_data.get("genres", [])],
            "trailer_url": f"https://www.youtube.com/watch?v={trailer_key}" if trailer_key else None
        }

    except Exception as e:
        print("Error fetching movie details:", e)
        movie_data = {
            "title": movie_name,
            "description": "No details found due to connection or API issue.",
            "poster_url": "/static/default.jpg",
            "rating": "N/A",
            "genres": [],
            "trailer_url": None
        }

    return render_template("movie_detail.html", movie=movie_data)

# Subscription page
@app.route('/subscribe/<movie_name>')
def subscribe(movie_name):
    return render_template('subscribe.html', movie_name=movie_name)

# Payment page
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if request.method == 'POST':
        return render_template('thankyou.html')
    return render_template('payment.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
