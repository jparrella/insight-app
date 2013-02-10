'''
Here we're going to perform a clustering algorithm to group the artists
'''

# import the following
import numpy as np
import pandas as pd
import MySQLdb as mdb
from pandas import DataFrame, Series
from time import time, sleep
import mysql_tools as mst
from sklearn.cluster import MeanShift, estimate_bandwidth
import general_tools as gent


# ----------------------------------------
# Important input variables
# ----------------------------------------
# for the MySQL database
db_name = 'hiphopper'
root_artist = 'jdilla'

# this file
loc = 'cluster_artists'


def get_artist_recs(drop_names=None, upvote_names=None):

	# -------------------------------------------
	# Open MySQL to access the artist vote data
	# -------------------------------------------
	db = mdb.connect('localhost', 'root','', db_name)

	with db:
	    cur = db.cursor()
	    cur.execute("SELECT user_id, user_tw_name, \
	        artist_id, artist_name, artist_sn, \
	        genre, en_hot, en_familiar \
	        FROM artist_votes_{0}".format(root_artist))
	    rows = cur.fetchall()

	# convert tuple of tuples to a list of tuples
	list_data = [t for t in rows]

	# Now store the list of tuples received as a DataFrame
	frnd_data = DataFrame( list_data, 
	    columns=['user_id', 'user_tw_name', 'artist_id', 'artist_name', 
	    'artist_sn', 'genre', 'en_hot', 'en_familiar']
	    )

	# ---------------------------------------------------
	# Generate the affinity array for artists clustering
	# ---------------------------------------------------

	# Find the number of unique artists
	anames = frnd_data['artist_name']
	unique_anames = np.unique( anames )
	count_names = anames.value_counts()
	n_artists = len( unique_anames )
	aname_list = count_names.keys()

	# familiarity and 'hotttnesss' scores from echonest
	fam = frnd_data['en_familiar']

	# thin out the results
	msk = [ (el > 1) for el in count_names ]
	count_names_reduced = count_names[msk]

	# Find the number of unique users following the artists
	unique_user_ids = np.unique(frnd_data['user_id'])
	unique_user_names = np.unique(frnd_data['user_tw_name'])
	n_users = len(unique_user_ids)

	# Find the unique twitter handles of the artists
	unique_art_sns = np.unique(frnd_data['artist_sn'])

	# initialize the affinity matrix
	nrows = n_artists
	ncols = n_users
	icol  = range(ncols) # use this list to index across affin_matrix columns

	# -------------------------------------------
	# Make a bipartite graph
	# -------------------------------------------
	import networkx as nx
	from networkx.algorithms import bipartite

	# jpp, flag - refactor this maybe? might need to clear if there's memory of G
	try:
		G.clear()
	except:
		G = nx.Graph()

	# now add the root artist, whom all fans follow
	G.add_node(root_artist, type='artist')

	#G.add_node(unique_anames[0], type='artist')
	for tup in list_data:

		name_of_artist = tup[3]
		name_of_fan = tup[0] # using the ID of the fan instead of name... avoid John Smith problem...
		familiarity = float(tup[7])
		hot = float(tup[6])

		if (count_names[name_of_artist] < 30):
			continue
		
		if not G.has_node(name_of_artist):
			# Add a new artist nodes
			G.add_node(name_of_artist, type='artist')

		if not G.has_node(name_of_fan):
			# Add a new fan
			G.add_node(name_of_fan, type='fan')
			# and connect that person to the root artist
			G.add_edge(root_artist, name_of_fan)

		# Now create a link betwen the current artist
		# and fan grouping
		# wgt = 1.0/familiarity
		wgt = 1.0 # (1.0/familiarity)**2
		G.add_edge(name_of_artist, name_of_fan, weight=wgt)

	# -------------------------------------------
	# Now make the directed graph:
	#   1. Nodes represent artists.
	#   2. Edges are weighted by the number of
	#      fans in common for each pair.
	# -------------------------------------------
	DG = nx.DiGraph()

	# -------------------------------------------------------
	# Calculate the weightings for the directed graph as
	# the number of shared followers between artists.
	# Use neighbors() method of G to count the number of
	# artists that each user follows.
	#  will normalize the edges after this algorithm
	# -------------------------------------------------------
	aname_list = np.array( aname_list )
	aname_list = np.concatenate( (np.array([root_artist]), aname_list) ) #jpp flag
	n_artists = n_artists + 1 # jpp, flag: add one for root artist
	index_array = np.arange( n_artists )

	weight_matrix = np.zeros( (n_artists, n_artists) )

	# Do we apply a downweight to twitter followers
	# who like a particular artist
	if ( drop_names == None ):
		down_weight = 1.0
		down_voted_artists = ' - No artist here! - '
	else:
		down_weight   = 1.0/100.0
		down_voted_artists = drop_names
		# print 'in the downweighting section', down_voted_artist

	if ( upvote_names == None ):
		up_weight = 1.0
		up_voted_artists = ' - No artist here! - '
	else:
		up_weight   = 100.0
		up_voted_artists = drop_names


	for uid in unique_user_ids:
		# keep track of how many up and 
		# down votes we have for one user.
		# that way we can give proper weighting to
		# a user who has a few up and down votes.
		n_down_votes_per_user = 0
		n_up_votes_per_user = 0

		# Some of the user ID's were filtered out because I set
		# a threshold on the number of votes an artist must have
		# to make it to the graphing.
		if G.has_node(uid):

			# add the root_artist to the list
			user_follows = [root_artist] + G.neighbors(uid)

			# check to see if any of the down-voted 
			# artists are in the user's list. If so, then
			# down-weight.
			for k, dva in enumerate(down_voted_artists):
				if any( str(dva).strip() in s for s in user_follows):
					# down weight this fan's preferences by making the
					# distance to the root node longer 
					# print 'downweighting ', uid
					weight_adjust_down = down_weight
					break
					n_down_votes_per_user += 1
				else:
					weight_adjust_down = 1.0

			weight_adjust = weight_adjust_down

			# -------------------------------------
			#    +++  This code needs work +++
			#         upvoting & downvotes
			# -------------------------------------
			# for k, uva in enumerate(up_voted_artists):
			# 	if any( str(uva).strip() in s for s in user_follows):
			# 		# up weight this fan's preferences by making the
			# 		# distance to the root node longer 
			# 		weight_adjust_up = up_weight
			# 		n_up_votes_per_user += 1
			# 	else:
			# 		weight_adjust_up = 1.0

			# if ( n_down_votes_per_user == n_up_votes_per_user ):
			# 	weight_adjust = 1.0

			# if ( n_down_votes_per_user > n_up_votes_per_user ):
			# 	weight_adjust = weight_adjust_down

			# if ( n_up_votes_per_user > n_down_votes_per_user ):
			# 	weight_adjust = weight_adjust_up


			# # Now apply either a weight up or weight down
			# # depending on which profile the current user is
			# # closer too.
			# if ( n_up_votes_per_user > 0 and n_down_votes_per_user > 0):
			# 	if ( n_up_votes_per_user > n_down_votes_per_user ):
			# 		weight_adjust = weight_adjust_up
			# 	else:
			# 		weight_adjust = weight_adjust_down
			# elif n_up_votes_per_user > 0 :
			# 	weight_adjust = weight_adjust_up
			# else:
			# 	weight_adjust = weight_adjust_down

		else:
			continue

		j=0
		for uf in user_follows:
			# Find the appropriate column index for uf.
			# i.e. where the name matches up with the aname_list array
			msk = np.array([ (t == uf) for t in aname_list ])
			ir  = index_array[msk][0]

			j += 1

			for i in range(j, len(user_follows)-1, 1):
				# locate the pair's name
				pair_name = user_follows[i]
				msk = np.array([ (t == pair_name) for t in aname_list ])
				ic = index_array[msk][0]
				# the matrix is symetric... artists on rows and columns
				weight_matrix[ir, ic] += 1 * weight_adjust
				weight_matrix[ic, ir] += 1 * weight_adjust

	# ------------------------------------------------------------
	# normalize the weights to the total number of
	# followers that artist has (so sharing 25% of fan base, etc...)
	# Also, begin filling our directed graph
	# ------------------------------------------------------------
	# for the root artist
	# weight_matrix[0, :] = weight_matrix[0, :] / n_users
	# for the rest of them
	for i in range(1, nrows+1, 1):
		# if (count_names[i-1] > 0):
		# 	# normalize by the number of votes an artist has
		# 	weight_matrix[i, :] = weight_matrix[i, :] / count_names[i-1]
		name_of_artist = aname_list[i]
		DG.add_node(name_of_artist)

	# Now fill the Directed graph with nodes and weights
	for i in range(n_artists):
		artist_name_row = aname_list[i]

		# jpp, flag - not sure if I'll use this or not
		if (i > 0):
			tup = list_data[i]
			familiarity = float(tup[7])
		else:
			familiarity = 1

		for j in range(n_artists):

			# the weight - note, can also multiply in
			# 'hotttnesss' factors from EchoNest, or
			# their familiarity score. Apply to the row
			if ( wgt > 0.0001 ):
				wgt = 1.0 / weight_matrix[i, j]
			else:
				wgt = 0

			# the artist in the column space
			artist_name_col = aname_list[j]
			# only make edges between different artists...
			if (artist_name_col == artist_name_row): continue
			# and set a threshold for making an edge, based on
			# the weight we calculated earlier
			# if ( weight_matrix[i, j] < 0.0001 ): continue
			DG.add_weighted_edges_from( [(artist_name_row, 
				artist_name_col, wgt)] )

	# Now remove the nodes that have no edges
	# for artist in aname_list:
	# 	if (artist == root_artist): continue
	# 	if len(DG.predecessors(artist)) == 0:
	# 		if len(DG.successors(artist)) == 0:
	# 			DG.remove_node( artist )

	# Now calculate the path lengths from each artist
	# to the root artist
	path_lengths = nx.single_source_dijkstra_path_length(
		DG, root_artist, weight='weight'
		)
	# distance = path_lengths.values()
	# name_keys = path_lengths.keys()

	# sorted_dist - a list of tuples
	import operator
	sorted_dist = sorted(path_lengths.iteritems(), key=operator.itemgetter(1))

	# Use the MySQL database to find the artist's
	# twitter screen name -- enable following of the
	# artist on twitter: list_data list of tuples

	# select the top 5 recommended artists and
	# return them as a list to calling program
	j = 0
	rec_list = []
	twitter_handles = []
	for art in sorted_dist:
		if j > 3: break
		# unpack the tuple
		name, dist = art
		# now
		for tup in list_data:
			sn = tup[4]
			n  = tup[3]
			if (n == name):
				twitter_handles.append(sn)
				break

		if (name == root_artist): continue
		j += 1
		print name
		rec_list.append( name )

	# jpp, flag - make more elegant - refactor
	# convert to dictionary to be jsonify-able
	rec_dict = {'name': rec_list, 'sn': twitter_handles}

	return rec_dict #rec_list

