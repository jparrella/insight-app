'''
This is the python module that serves up
the backend, directed graph algorithm to the
frontend web-browser.

Calls cluster_artists.py to calculate the rankings
for recommended artists, and posts on the web.
'''
# import the following
import os
from flask import Flask, url_for
from flask import render_template
from flask import jsonify
from flask import request
import sys
from cluster_artists import get_artist_recs

# instantiate the flask object
app = Flask(__name__)

@app.route('/')
def home():
    '''
    Return the homepage.

    Notes:
    render_template() looks for the
    passed html file in the
    local ./templates folder.
    '''
    return render_template('home.html')

@app.route('/about_me')
def about_me():
	'''
	Return the about_me.html page.
	'''
    return render_template('about_me.html')

@app.route('/slides')
def slides():
	'''
	Return the slides.html page.
	Slides that share info about my Insight project.
	'''
    return render_template('slides.html')

@app.route('/hiphopper')
def api():
	'''
	The initial hiphopper application webpage.
	Where user will select the root artist.
	'''
    return render_template('hiphopper.html')

@app.route('/hiphopper/output_', methods=['GET'])
def api_output():
	'''
	This is the function that interfaces with
	Ajax/JavaScript inside output.html.

	Here, we take the following steps:
	```````````````````````````````````
	1. Call the python algorithm for ranking
	   best musicians for the user given root artist.
	'''
	# get the root artist
	artist = request.args['artist']
	
	# Call the backend algorithm to get best
	# initial recommendations from stored twitter data.
	rec = get_artist_recs( artist.strip() )
	rec_name = rec['name']
	rec_sn   = rec['sn']

	# now render the HTML for output
	return render_template('output.html', recommendation=rec_name,
		rec_sn = rec_sn, root_artist = artist)


@app.route('/hiphopper/output', methods=['POST', 'GET'])
def refresh_list():
	'''
	This is the function that interfaces with
	Ajax/JavaScript inside output.html.

	Here, we take the following steps:
	```````````````````````````````````
	1. Wait for information from the user on
	   what he/she did not like. 
	2. Call the python algorithm for re-ranking
	   best musicians for the user.
	'''
	# store the jsonified data from the app's user
	out_dict = request.json
	# get the rejected artists
	rejected_artists = request.json['rejected_artists']
	# currently upvoted_artists are not used
	upvoted_artists = request.json['upvoted_artists']
	# store the root artist
	root_artist = request.json['root_artist']

	# make sure we don't have any unicode characters
	# that will disrupt our string comparisons in 
	# get_artist_recs()
	if type(rejected_artists) is list:
		for i in range( len(rejected_artists) ):
			rejected_artists[i] = rejected_artists[i].replace(
				'&amp;', '&')

	# pass to recommendation algorithm
	rec = get_artist_recs(root_artist, drop_names = rejected_artists,
		                  upvote_names = upvoted_artists
		                  )

	# store the names and screen names of rec'd artists
	rec_name = rec['name']
	rec_sn   = rec['sn']

	# concatenate these recommendations
	rec = rec_name + rec_sn
	print rec[:]
	
	# store in a dict to the json file
	# for passing back to the web-browser.
	data = {}
	for i, v in enumerate( rec ):
		data[i] = v

	return jsonify(data)


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    app.debug = False
    app.run(host='0.0.0.0', port=8080)

