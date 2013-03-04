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
import general_tools as gent
import os

# ----------------------------------------
# Important input variables
# ----------------------------------------
# for the MySQL database
db_name = 'hiphopper'

# this file
loc = 'cluster_artists'

# take the MySQL password from the
# local variables.
mdb_pass = os.getenv('MDBPW')


def get_artist_recs(root_artist, drop_names=None, upvote_names=None):
    '''
    function: get_artist_recs

    Input Arguments:
    1. root_artist :: string :: this is the name of the root artist
                                that is expected by the MySQL
                                database
    2. drop_names :: list (of strings) :: this is the list of
                                          artist names the user of
                                          our app has "down-voted".
                                          All twitter users who "voted"
                                          for this artist will be
                                          down-weighted in the directed
                                          graph algorithm.
    3. upvote_names :: list (of strings) ** currently inactive

       TODO - once we have more data, could implement upvoting on app.
              Currently this feature is inactive.

    '''
    # Handle the case when drop_names or
    # upvote_names are empty arrays
    if (drop_names is not None):
        if len(drop_names) == 0:
            drop_names = None
        else:
            drop_names = np.unique(drop_names)
        if len(upvote_names) == 0:
            upvote_names = None
        else:
            upvote_names = np.unique(upvote_names)

    # -------------------------------------------
    # Open MySQL to access the artist vote data
    # -------------------------------------------
    db = mdb.connect('localhost', 'root', mdb_pass, db_name)

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
    frnd_data = DataFrame(list_data,
                          columns=['user_id', 'user_tw_name',
                          'artist_id', 'artist_name',
                          'artist_sn', 'genre', 'en_hot',
                          'en_familiar']
                          )

    # ---------------------------------------------------
    # Generate the affinity array for artists clustering
    # ---------------------------------------------------

    # filter out the pop artists and other buggy ones
    frnd_data = frnd_data[frnd_data['genre'] != 'pop']
    frnd_data = frnd_data[frnd_data['genre'] != 'latin']
    frnd_data = frnd_data[frnd_data['genre'] != 'cabaret']
    frnd_data = frnd_data[frnd_data['genre'] != 'symphony']
    frnd_data = frnd_data[frnd_data['genre'] != 'soundtrack']
    frnd_data = frnd_data[frnd_data['genre'] != 'r&b']
    frnd_data = frnd_data[frnd_data['genre'] != 'latin pop']
    frnd_data = frnd_data[frnd_data['genre'] != 'hardcore']
    frnd_data = frnd_data[frnd_data['genre'] != 'pop rock']
    # TODO: Find more general ways to filter EchoNest errors in
    #       reporting the genres of celebrities/artists on record.
    # ---------------------------------------------------------
    # hardwired some names that really aren't musicians, but
    # for some reason are listed as "rock" or "blues" in
    # echonest.
    # -----------------------------------------------------
    frnd_data = frnd_data[frnd_data['artist_name'] != 'Wired']
    frnd_data = frnd_data[frnd_data['artist_name'] != 'Samuel L. Jackson']
    frnd_data = frnd_data[frnd_data['artist_name'] != 'Taylor Swift']
    frnd_data = frnd_data[frnd_data['artist_name'] != 'Ozzy Osbourne']
    frnd_data = frnd_data[frnd_data['artist_name'] != 'The Guardian']
    frnd_data = frnd_data[frnd_data['artist_name'] != 'Coachella']

    # Find the number of unique artists
    anames = frnd_data['artist_name']
    unique_anames = np.unique(anames)
    count_names = anames.value_counts()
    n_artists = len(unique_anames)
    aname_list = count_names.keys()

    # familiarity and 'hotttnesss' scores from echonest
    fam = frnd_data['en_familiar']

    # thin out the results
    msk = [(el > 1) for el in count_names]
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
    icol = range(ncols)  # use this list to index across affin_matrix columns

    # -------------------------------------------
    # Make a bipartite graph
    # TODO:
    #  - this graph is currently only used as
    #    a filter for nodes we want to include
    #    in the directed graph
    #  - Note that it's inefficient, and will
    #    fix this later.
    # -------------------------------------------
    import networkx as nx
    from networkx.algorithms import bipartite
    G = nx.Graph()

    # now add the root artist, whom all fans follow
    G.add_node(root_artist, type='artist')

    #G.add_node(unique_anames[0], type='artist')
    for tup in list_data:

        name_of_artist = tup[3]
        # using the ID of the fan instead of name
        # Avoid John Smith problem (multiple people, same name)
        name_of_fan = tup[0]
        familiarity = float(tup[7])
        hot = float(tup[6])

        # removing pop artists and other
        # artists who were removed from the
        # count_names variable in first lines of
        # this function.
        try:
            count = count_names[name_of_artist]
        except:
            continue  # filtered out that artist

        # make sure there are at least 5 people
        # who follow this artist. Quick filter
        # against some echonest errors of non-artists.
        if (count < 5):
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
        wgt = 1.0
        G.add_edge(name_of_artist, name_of_fan, weight=wgt)

    # -------------------------------------------
    # Make the Directed Graph:
    # ````````````````````````
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
    aname_list = np.array(aname_list)
    aname_list = np.concatenate((np.array([root_artist]), aname_list))
    n_artists = n_artists + 1  # Added one to include root artist in matrix
    index_array = np.arange(n_artists)
    weight_matrix = np.zeros((n_artists, n_artists))

    # Do we apply a downweight to twitter followers
    # who like a particular artist
    if (drop_names is None):
        down_weight = 1.0
        down_voted_artists = ' - No artist here! - '
        weight_adjust_down = 1.0
    else:
        down_weight = 1.0/100.0
        down_voted_artists = drop_names

    # TODO: Note that upvote_artists is currently inactive.
    #       Later, explore user-friendly ways to add this
    #       functionality.
    if (upvote_names is None):
        up_weight = 1.0
        up_voted_artists = ' - No artist here! - '
        weight_adjust_up = 1.0
    else:
        up_weight = 100.0
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

            # TODO: differentiate between different levels of
            #       user missmatches with the twitter "voters".
            #       For now, I only downweight once for
            #       each user, even if they have multiple artists
            #       that our app's web-user doesn't like.
            # -----------------------------------------------
            # check to see if any of the down-voted
            # artists are in the user's list. If so, then
            # down-weight.
            # -----------------------------------------------
            for k, dva in enumerate(down_voted_artists):
                if any(str(dva).strip() in s for s in user_follows):
                    # down weight this fan's preferences by making the
                    # distance to the root node longer
                    # print 'downweighting ', uid
                    weight_adjust_down = down_weight
                    break
                    n_down_votes_per_user += 1
                else:
                    weight_adjust_down = 1.0

            # store the weighting specific to this user
            weight_adjust = weight_adjust_down

        else:
            continue

        j = 0
        for uf in user_follows:
            # Find the appropriate column index for uf.
            # i.e. where the name matches up with the aname_list array
            msk = np.array([(t == uf) for t in aname_list])
            ir = index_array[msk][0]

            j += 1

            for i in range(j, len(user_follows)-1, 1):
                # locate the pair's name
                pair_name = user_follows[i]
                msk = np.array([(t == pair_name) for t in aname_list])
                ic = index_array[msk][0]
                # the matrix is symetric... artists on rows and columns
                weight_matrix[ir, ic] += 1 * weight_adjust
                weight_matrix[ic, ir] += 1 * weight_adjust

    # ------------------------------------------------------------
    # 1. normalize the weights to the log number of
    #    followers artist has. This reigns in the power law
    #    of artist follower numbers. (e.g. millions of followers
    #    for Justin Bieber, but only 5 thousand for J Dilla).
    #
    # 2. Begin filling our directed graph.
    # ------------------------------------------------------------
    # Transform the 0's to really small values. Avoid div-by-0's
    trans = np.where(weight_matrix, weight_matrix, 0.00001)
    # now compute the log safely
    log_wgt = np.log(trans)
    log_wgt = np.where(log_wgt < 0, 0, log_wgt)  # scale small back to zero

    # add artists' names to the directed graph
    for i in range(1, nrows+1, 1):
        name_of_artist = aname_list[i]
        DG.add_node(name_of_artist)

    # Now fill the Directed graph with weighted edges.
    # edges are weighted by the number of shared followers
    # in common between two artists (not symetric).
    for i in range(n_artists):
        artist_name_row = aname_list[i]

        for j in range(n_artists):

            # the weight - note, can also multiply in
            # 'hotttnesss' factors from EchoNest, or
            # their familiarity score. Apply to the row
            if (wgt > 0.0001):
                wgt = 1.0 / log_wgt[i, j]
            else:
                wgt = 0
                continue  # don't draw a graph if nothing's there

            # the artist in the column space
            artist_name_col = aname_list[j]

            # only make edges between different artists...
            if (artist_name_col == artist_name_row):
                continue

            # TODO: played with a threshold for making an edge.
            #       did not significantly affect results. May
            #       be important at larger scale of data.
            # if ( weight_matrix[i, j] < 0.0001 ): continue
            DG.add_weighted_edges_from([(artist_name_row,
                                       artist_name_col, wgt)]
                                       )

    # -----------------------------------------------------
    # Now calculate the path lengths from each artist
    # to the root artist.
    # -----------------------------------------------------
    path_lengths = nx.single_source_dijkstra_path_length(DG,
                       root_artist, weight='weight')

    # -----------------------------------------------------
    # Output, path_lengths, is a a list of tuples.
    # Sort the tuples (artist, path_length) by
    # the distance from the root artist.
    # -----------------------------------------------------
    import operator
    sorted_dist = sorted(path_lengths.iteritems(), key=operator.itemgetter(1))

    # select the top 4 recommended artists and
    # return them as a list to calling program
    j = 0
    rec_list = []
    twitter_handles = []
    yn_next = False
    for art in sorted_dist:

        # break if we have 4 artists.
        # counting of j started at 0.
        if j > 3:
            break

        # unpack the tuple
        name, dist = art

        # skip the root artist
        if (name == root_artist):
            continue

        # A control statement to remove artists
        # that have been down-weighted from the
        # output.
        if drop_names is not None:
            for dn in drop_names:
                if dn.strip() == name:
                    yn_next = True
                    break

        if yn_next:
            yn_next = False
            continue

        # Get the proper twitter screen name
        # jpp, flag refactor
        for tup in list_data:
            sn = tup[4]
            n = tup[3]
            if (n == name):
                twitter_handles.append(sn)
                break

        j += 1
        print name

        rec_list.append(name)

    # if no artists left to fill, then pack with
    # the following:
    # name = "Sorry, no artists left!"
    # sn = twitter
    n_recs_out = len(rec_list)
    if n_recs_out < 4:
        for i in range(4 - n_recs_out):
            rec_list.append("Sorry, no artists left!")
            twitter_handles.append("twitter")

    # convert to dictionary to be jsonify-able
    rec_dict = {'name': rec_list, 'sn': twitter_handles}

    # print statement for debugging...
    # print 'the rejected artists are ', drop_names

    return rec_dict
