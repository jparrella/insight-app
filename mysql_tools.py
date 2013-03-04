'''
file: mysql_tools.py

----------
 Notes:
----------
This file contains functions to create tables in the
HipHopper MySQL database. Tables correspond to twitter
data scraped for each of the root artists considered
in the web application.

Created on Feb 1, 2013
@author: justin.parrella@gmail.com
'''

# Local variable for the functions below
proj_name = 'hiphopper'
art_tbl_name = 'artists'
frnds_tbl_name = 'friends'

# imported modules
import MySQLdb as mdb
import general_tools as gt


def create_db(p_name=proj_name):
    '''
    If the hiphopper database has not yet been created, we can
    do so with this function.
    '''
    db = mdb.connect('localhost', 'root', '',
                     charset='utf8', use_unicode=True)
    cursor = db.cursor()
    # Create the database
    # TODO: tag with "IF NOT EXISTS", but will let it raise an
    # exception for now. I don't want to add values to
    # populated tables inadvertantly.
    cursor.execute("CREATE database {0}".format(p_name))

    # commit the changes to MySQL
    db.commit()


def create_user_table(db_select, root_artist):
    '''
    If a "user" table for the given root_artist does not
    yet exist in the hiphopper database, then create it.
    '''
    # open connection to the local MySQL database
    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    # use the schema corresponding to root_artist
    cursor.execute('USE {0}'.format(db_select.strip()))

    # The users table name, specific to the root_artist
    tbl_name = 'users'+"_"+root_artist.strip()

    # TODO: tag with "IF NOT EXISTS", but will let it raise an
    # exception for now.
    cursor.execute("CREATE TABLE {0} (\
        pkid int NOT NULL auto_increment, \
        user_tw_id int(20) NOT NULL, \
        user_tw_name char(150) CHARACTER SET utf8 NULL, \
        user_tw_sn char(150) CHARACTER SET utf8 NOT NULL, \
        user_followees_count int(20) NULL, \
        PRIMARY KEY (pkid)) ENGINE=InnoDB;".format(tbl_name))


def populate_user_table(root_followers, in_db, root_artist):
    '''
    Populate the "user" table for the given root_artist

    What we're storing:
    ```````````````````
    - Information for each twitter follower of the root_artist.
    - in next step (not in this table), we'll store information
      on what twitter users each of the 1st degree users follow.
    '''
    # Open connection to the local MySQL database
    db = mdb.connect('localhost', 'root', '',
                     charset='utf8', use_unicode=True)

    cursor = db.cursor()
    # use the specified database - HipHopper.
    cursor.execute('USE {0}'.format(in_db))

    # Table name
    tbl_name = 'users'+"_"+root_artist.strip()

    # If the twitter user information in root_followers,
    # is not contained in a list, then convert it to one
    # to stream-line the processing.
    if not (type(root_followers) is list):
        if root_followers:
            root_followers = [root_followers]
        else:
            # if it doesn't exist, then raise an exception
            raise Exception('populate_user_table: input value, \
                root_followers, is empty')

    # loop over the twitter users stored in root_followers
    # and store them in our MySQL table.
    for user_obj in root_followers:
        # twitter user ids and the no. of friends (ppl they follow)
        # will be stored in the database. Store them in local vars.
        uid = user_obj.id
        ufc = user_obj.friends_count

        # just in case there's nothing there
        if (uid is None) or (user_obj.screen_name is None):
            continue

        # Make sure to escape the strings in
        # case of quotations, bad characters, etc.
        # Use "try" command to avoid failures
        try:
            tw_name = mdb.escape_string(user_obj.name)
        except:
            # occasionally you get characters that can't be
            # encoded in ascii-128
            tw_name = user_obj.name

        # follow the same procedure for twitter screen names
        try:
            tw_sn = mdb.escape_string(user_obj.screen_name)
        except:
            tw_sn = user_obj.screen_name

        cinsert = "INSERT INTO {0}(user_tw_id, user_tw_name, \
            user_tw_sn, user_followees_count)".format(tbl_name)
        inp_row = "VALUES('%s','%s','%s','%s')" % (uid, tw_name,
                                                   tw_sn, ufc)
        execute_mdb = cinsert + inp_row + ';'

        # TODO: make text handling more general.
        # Found that occasionally the database would not accept
        # a very small number of the twitter profiles I tried to
        # store. Not a problem at current scale, but could be
        # as we scale up to more users.
        # Temporary: using try/except clause to avoid error.
        try:
            cursor.execute(execute_mdb.encode("utf8"))
        except:
            # TODO: currently throwing away users with extraordinarily
            #       crazy names... copyright symbols, TMs, etc...
            #       try something more sophistocated later
            continue

    db.commit()


def create_friends_table(db_select, root_artist):
    '''
    If a "friends" table for the given root_artist does not
    yet exist in the hiphopper database, then create it.

    What we're storing:
    ```````````````````
    - for each twitter follower of the root_artist, store all of
      the twitter users these individuals follow.
    - in next step (not in this table), we'll ID the musicians
      out of all the twitter users this set of people follow.
    '''
    # open the connection to the local database
    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(db_select.strip()))

    # the friends table name, specific for chosen root artist
    table_name = frnds_tbl_name.strip() + "_" + root_artist.strip()

    # create the table in MySQL
    cursor.execute("CREATE TABLE {0} (\
        pkid int NOT NULL auto_increment, \
        user_id int(20) NOT NULL, \
        user_tw_name char(150) CHARACTER SET utf8 NULL, \
        user_tw_sn char(150) CHARACTER SET utf8 NOT NULL, \
        friend_id int(20) NOT NULL, \
        friend_tw_name char(150) CHARACTER SET utf8 NULL, \
        friend_tw_sn char(150) CHARACTER SET utf8 NOT NULL, \
        friend_follow_count int(20) NULL, \
        friend_friend_count int(20) NULL, \
        friend_image_url char(255) CHARACTER SET utf8 NULL, \
        PRIMARY KEY (pkid)) ENGINE=InnoDB;".format(table_name))

    db.commit()


def populate_friends_table(user_id, user_tw_name, user_tw_sn,
                           frnd_list, in_db, root_artist):
    '''
    Populate the "friends" table for the given root_artist

    What we're storing:
    ```````````````````
    - for each twitter follower of the root_artist, store all of
      the twitter users these individuals follow.
    - in next step (not in this table), we'll ID the musicians
      out of all the twitter users this set of people follow.
    '''
    # open a connection to the local MySQL database
    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    # use the hiphopper schema
    cursor.execute('USE {0}'.format(in_db))

    # Name of the table we want to populate
    table_name = frnds_tbl_name.strip() + "_" + root_artist.strip()

    # Loop over all friends of the current user (i.e.
    # twitter users that this person follows)
    for frnd in frnd_list:

        # load input into dummy variables
        # escape the strings if possible to
        # avoid feeding bad characters to MySQL
        try:
            uname = mdb.escape_string(user_tw_name)
        except:
            uname = user_tw_name
        try:
            usn = mdb.escape_string(user_tw_sn)
        except:
            usn = user_tw_sn
        try:
            fname = mdb.escape_string(frnd.name)
        except:
            fname = frnd.name
        try:
            fsn = mdb.escape_string(frnd.screen_name)
        except:
            fsn = frnd.screen_name

        # TODO: make text handling more general.
        # Found that occasionally the database would not accept
        # a very small number of the twitter profiles I tried to
        # store. Not a problem at current scale, but could be
        # as we scale up to more users.
        # Temporary: using try/except clause to avoid error.
        try:

            # Load my MySQL commands into strings before executing
            cinsert = "INSERT INTO {0}(user_id, user_tw_name, \
                user_tw_sn, friend_id, friend_tw_name, \
                friend_tw_sn, friend_follow_count, \
                friend_friend_count)".format(table_name)

            inp_row = "VALUES('%s','%s','%s','%s','%s','%s','%s','%s')" % (user_id,
                uname, usn,frnd.id, fname, fsn,
                frnd.followers_count, frnd.friends_count)

            # Now execute MySQL command for adding a new row
            execute_mdb = cinsert + inp_row + ';'
            cursor.execute(execute_mdb.encode("utf8"))

        except:
            try:  # try again without the url
                  # make sure it's not the url we're storing for twitter
                  # profile pictures
                cinsert = "INSERT INTO {0}(user_id, user_tw_name, \
                    user_tw_sn, friend_id, friend_tw_name, \
                    friend_tw_sn, friend_follow_count, \
                    friend_friend_count)".format(table_name)

                inp_row = "VALUES('%s','%s','%s','%s','%s',\
                    '%s','%s','%s')" % (user_id, uname, usn,
                                        frnd.id, fname, fsn,
                                        frnd.followers_count,
                                        frnd.friends_count
                                        )

                # Make the full MySQL command one string
                execute_mdb = cinsert + inp_row + ';'

                # now execute the command in MySQL
                cursor.execute(execute_mdb.encode("utf8"))
            except:
                # jpp, flag: throwing away users with extraordinarily
                #            crazy names... copyright symbols, TMs, etc...
                #            try something more sophistocated later
                continue

    # save the changes
    db.commit()


def create_artist_votes_table(db_select, root_artist):
    '''
    If a "artist_votes" table for the given root_artist does not
    yet exist in the hiphopper database, then create it.

    What we're storing:
    ```````````````````
    - for each twitter follower of the root_artist, store all of
      the twitter users these individuals follow that have been
      identified as musicians.
    - This database is what is used by the HipHopper application
      to generate recommendations.
    '''
    # open connection to the local MySQL database
    db = mdb.connect('localhost','root','')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(db_select.strip()))

    # the artist table name, specific for chosen root artist
    table_name = "artist_votes_" + root_artist.strip()

    # create the table in MySQL
    cursor.execute("CREATE TABLE {0} (\
        pkid int NOT NULL auto_increment, \
        user_id int(20) NOT NULL, \
        user_tw_name char(150) CHARACTER SET utf8 NULL, \
        artist_id int(20) NOT NULL, \
        artist_name char(150) CHARACTER SET utf8 NULL, \
        artist_sn char(150) CHARACTER SET utf8 NOT NULL, \
        genre char(150) CHARACTER SET utf8 NOT NULL, \
        en_hot decimal(6,3) NULL, \
        en_familiar decimal(6,3) NULL, \
        PRIMARY KEY (pkid)) ENGINE=InnoDB;".format(table_name))

    db.commit()


def populate_artist_votes_table(user_id, user_tw_name,
                                artist_id, artist_name,
                                artist_sn, artist_genre,
                                artist_familiarity,
                                artist_hotness, in_db,
                                root_artist):
    '''
    Populate the "artist_votes" table for the given root_artist.

    What we're storing:
    ```````````````````
    - for each twitter follower of the root_artist, store all of
      the twitter users these individuals follow that have been
      identified as musicians.
    - This database is what is used by the HipHopper application
      to generate recommendations.
    '''
    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(in_db))

    # Name of the table we're going to populate
    table_name = "artist_votes_" + root_artist.strip()

    # load input into dummy variables
    # escape the strings if possible to
    # avoid feeding bad characters to MySQL
    try:
        uname = mdb.escape_string(user_tw_name)
    except:
        uname = user_tw_name
    try:
        art_name = mdb.escape_string(artist_name)
    except:
        art_name = artist_name
    try:
        art_sn = mdb.escape_string(artist_sn)
    except:
        art_sn = mdb.escape_string(artist_sn)
    try:
        art_genre = mdb.escape_string(artist_genre)
    except:
        art_genre = artist_genre

    # TODO: make text handling more general.
    # Found that occasionally the database would not accept
    # a very small number of the twitter profiles I tried to
    # store. Not a problem at current scale, but could be
    # as we scale up to more users.
    # Temporary: using try/except clause to avoid error.
    try:
        # Load my MySQL commands into strings before executing
        cinsert = "INSERT INTO {0}(user_id, user_tw_name, artist_id, \
            artist_name, artist_sn, genre, en_hot, en_familiar)".format(table_name)

        inp_row = "VALUES('%s','%s','%s','%s','%s','%s','%s','%s')" % (user_id, uname,
            artist_id, art_name, art_sn, art_genre,
            artist_hotness, artist_familiarity)

        # Now execute MySQL command for adding a new row
        execute_mdb = cinsert + inp_row + ';'
        cursor.execute(execute_mdb.encode("utf8"))
        # save the changes
        db.commit()
    except:
        pass
        # jpp, flag: throwing away users with extraordinarily
        #            crazy names... copyright symbols, TMs, etc...
        #            try something more sophistocated later
