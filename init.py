import random, sys, time, re
from flask import Flask, render_template, request, jsonify, Response, url_for
from flask import redirect, make_response, session
from model import Recommender
from utils import Database
from utils import Indexer

reload(sys)
sys.setdefaultencoding('utf-8')

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Qas5nb113@&B#(V!*#8z\n\xec]/'

db = Database()

recommender = Recommender()

if not db.checkConnectivity():
	print 'Unable to connect to database'
	sys.exit(-1)

indexer = Indexer()

@app.before_request
def authenticateUser():
	if request.endpoint != 'search' and request.endpoint != 'signIn' and 'userid' not in session:
		return redirect(url_for('signIn'))

@app.route('/signout')
def signOut():
	session.clear()
	return redirect(url_for('signIn'))

@app.route('/signin', methods=['GET', 'POST'])
def signIn():
	if request.method == 'POST':
		if int(request.form['userid']) > 34394:
			session['userid'] = request.form['userid']
			return redirect(url_for('home'))
	return render_template('sign_in.html')

@app.route('/json')
def raw_resp():
	user_id = int(session['userid'])
	movie_ids = recommender.recommendMoviesTo(user_id, limit=30)

	watched_ids = recommender.getWatchedMovies(user_id)
	movies = {'recommended': movie_ids, 'watched': watched_ids}
	return jsonify(movies)


@app.route('/')
def home():
	user_id = int(session['userid'])
	movie_ids = recommender.recommendMoviesTo(user_id, limit=30)
	movies_info = recommender.displayMovies(movie_ids)

	popular_ids = recommender.getPopularMovies()
	popular_info = recommender.displayMovies(popular_ids)

	watched_ids = recommender.getWatchedMovies(user_id)
	watched_info = recommender.displayMovies(watched_ids)

	recent_ids = recommender.getRecentMovies()
	recent_info = recommender.displayMovies(recent_ids)

	recommended = prepareMovies(movies_info)
	popular = prepareMovies(popular_info)
	watched = prepareMovies(watched_info)
	recent = prepareMovies(recent_info)

	similar = recommended[:]

	random.shuffle(watched)
	random.shuffle(similar)

	similar_to = {}
	similar_to['name'] = 'Iron Man'
	similar_to['recommendations'] = similar
	return render_template('movies.html', recommended=recommended, recent=recent, popular=popular, watched=watched, similar_to=similar_to)

@app.route('/search/json')
def searchJson():
	keyword = request.args.get('keyword', default = '', type = str)
	movies = indexer.search(keyword)
	for movie in movies:
		movie['url'] = db.getMovieUrl(movie['id'])
	return jsonify(movies)


@app.route('/search')
def search():
	keyword = request.args.get('keyword', default = '', type = str)
	movies = indexer.search(keyword)
	for movie in movies:
		movie['url'] = db.getMovieUrl(movie['id'])
	return render_template('search_results.html', keyword=keyword, search_results=movies)

@app.route('/movie/<int:movie_id>')
def showMovie(movie_id):
	movie = db.getMovieInfo(movie_id)
	ratings = db.getRatings(movie_id)
	return render_template('movie.html', movie=movie, y_data = ratings['ratings'])


@app.route('/create_index')
def create_index():
	indexer.buildIndex()
	return 'Success'


def prepareMovies(movies_info):
	movies = []
	for movie_info in movies_info:
		movie = {}
		movie['id'] = movie_info[0]
		movie['title'] = movie_info[1] if len(movie_info[1]) <= 46 else movie_info[1][:43] + '...'
		movie['title'] = re.sub(r'[^\x00-\x7F]+','', movie['title'])
		url = db.getMovieUrl(movie_info[0])
		if url == '':
			url = url_for('static', filename='image-not-available.jpg')
		movie['url'] = url
		movies.append(movie)
	return movies

if __name__ == "__main__":
	app.run('', threaded=True, port=5000, debug=True)

