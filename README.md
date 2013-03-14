1. Description of the files saved for my insight app, HipHopper.
   a. cluster_artists.py:
      This is the main python code for generating artist recommendations for users
      steps are as follows:
      i. User supplies the root artist to begin with (conditions the twitter
         followers we focus on), and any additional artists that the user didn't want.
      ii. Filters out EchoNest genres including "pop", "pop rock", "cabaret", and "soundtrack".
          Reasoning being that pop artists are easily found without a music discovery tool. Also,
          I removed artists with EchoNest genres that have lots of false positives. These include
          "r&b" and "symphony" (which returned Kim Kardashian and George Takai among others).
      iii. Calculates a directed graph using NetworkX DiGraph object twitter "votes" (from followers)
           - Nodes are the artists
           - Edges are weighted by the number of Artist1's followers who also follow Artist2
           - I down-weight votes on the edges from followers who also follow any of the
             musicians a given user removed from the recommended list.
                - Currently this is a constant weighting, only applied once. Can add more
                  detail with more data.
           - Calculate the distance between the root artist and each individual artist in the graph.
           - Serve up the top 4 closest artists.
   b. jpp_insight_app.py:
      This is the module that serves up results from cluster_artists to the web browser with Flask.
      See the comments for details on each method.
   c. mysql_tools.py:
      The set of mysql routines that I used to create and save tables of data from calls to
      the EchoNest and Twitter APIs. Twitter for the main data, EchoNest to evaluate musicians.

