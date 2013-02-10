import os
from flask import Flask, url_for
from flask import render_template
from flask import jsonify
from flask import request

# get path and import the clustering routine
# import sys
# sys.path.append( '../src/' )
from cluster_artists import get_artist_recs

app = Flask(__name__)

@app.route('/')
def home():
    # render_template() looks for the following html file in the
    # local ./templates folder.
#    return render_template('bootstrap_eg1.html')
#    return render_template('bootstrap_eg2.html')
    return render_template('home.html')

@app.route('/hiphopper')
def api():
#    recommendation = {'band': 'radiohead', 'album': 'Ok comp'}
#    return jsonify(recommendation) # to send to web-compatable...
    return render_template('hiphopper.html')

@app.route('/hiphopper/output', methods=['GET'])
def api_output():
	#    return jsonify(recommendation) # to send to web-compatable...
	rec = get_artist_recs()
	rec_name = rec['name']
	rec_sn   = rec['sn']
	return render_template('output.html', recommendation=rec_name,
		rec_sn = rec_sn)

@app.route('/hiphopper/output', methods=['POST', 'GET'])
def refresh_list():
	# get the name from $.post JavaScript...
	name = str(request.json['id']).strip()
	out_dict = request.json
	rejected_artists = request.json['rejected_artists']
	upvoted_artists = request.json['upvoted_artists']
	print 'removing votes for ', rejected_artists
	print 'upvoting votes for ', upvoted_artists

	# pass to recommendation algorithm
	rec = get_artist_recs(
		drop_names = rejected_artists,
		upvote_names = upvoted_artists
		)

	rec_name = rec['name']
	rec_sn   = rec['sn']

	rec = rec_name + rec_sn # concatenate
	print rec[:]
	
	data = {}
	for i, v in enumerate( rec ):
		data[i] = v

	return jsonify(data)


@app.route('/hiphopper/revised_output') #, methods=['GET','POST'])
def api_revise():
#    recommendation = {'band': 'radiohead', 'album': 'Ok comp'}
#    return jsonify(recommendation) # to send to web-compatable...
    return render_template('revised_output.html')

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.debug = True
    app.run(host='0.0.0.0', port=port)

