'''
Created on Feb 1, 2013

@author: jparrella
'''


# Local variable for the functions below
proj_name  = 'hiphopper' 
art_tbl_name = 'artists'
frnds_tbl_name = 'friends'

# First execute the unix command to export DYLIB
#import os
#os.system("DYLD_LIBRARY_PATH=\"${DYLD_LIBRARY_PATH}:/user/local/mysql/lib/\"")
import MySQLdb as mdb
import general_tools as gt

def create_db(p_name=proj_name):
    '''
    Use to create a new MySQL Schema
    '''
    db = mdb.connect('localhost', 'root','',
        charset='utf8', use_unicode=True)
    cursor = db.cursor()
    # Create the database
    # Could tag "IF NOT EXISTS", but will let it raise an
    # exception for now. I don't want to add values to
    # populated tables inadvertantly.
    cursor.execute("CREATE database {0}".format(p_name))

    db.commit()

def create_user_table(db_select, root_artist):
    '''
    Make a new table in the hiphopper database 
    '''
    db = mdb.connect('localhost','root','')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(db_select.strip()))
    
    # Table name
    tbl_name = 'users'+"_"+root_artist.strip()
    
    cursor.execute("CREATE TABLE {0} (\
        pkid int NOT NULL auto_increment, \
        user_tw_id int(20) NOT NULL, \
        user_tw_name char(150) CHARACTER SET utf8 NULL, \
        user_tw_sn char(150) CHARACTER SET utf8 NOT NULL, \
        user_followees_count int(20) NULL, \
        PRIMARY KEY (pkid)) ENGINE=InnoDB;".format(tbl_name))

def populate_user_table(root_followers, in_db, root_artist):

    db = mdb.connect('localhost','root','',
        charset='utf8', use_unicode=True)

    cursor = db.cursor()
    cursor.execute('USE {0}'.format(in_db))

    # Table name
    tbl_name = 'users'+"_"+root_artist.strip()

    # If it's not a list, then convert it to one
    if not (type(root_followers) is list):
        if root_followers:
            root_followers = [root_followers]
        else:
            # if it doesn't exist, then raise an exception
            raise Exception('populate_user_table: input value, \
                root_followers, is empty')

    # loop over the users to store them
    for user_obj in root_followers:

        uid     = user_obj.id
        ufc     = user_obj.friends_count

        # just in case there's nothing there
        if (uid == None) or (user_obj.screen_name == None):
            continue
        # print 'in user mysql call: ', user_obj.id

        # make sure to escape the strings in case of quotations, etc.
        try:
            tw_name = mdb.escape_string(user_obj.name)
        except:
            # occasionally you get characters that can't be
            # encoded in ascii (128)
            tw_name = user_obj.name
        try:
            tw_sn   = mdb.escape_string(user_obj.screen_name)
        except:
            tw_sn   = user_obj.screen_name

        cinsert = "INSERT INTO {0}(user_tw_id, user_tw_name, user_tw_sn, \
            user_followees_count)".format(tbl_name)
        inp_row = "VALUES('%s','%s','%s','%s')"%(uid, tw_name, tw_sn, ufc)
        execute_mdb = cinsert + inp_row + ';'
        try:
            cursor.execute( execute_mdb.encode("utf8") )
        except:
            # jpp, flag: throwing away users with extraordinarily 
            #            crazy names... copyright symbols, TMs, etc...
            #            try something more sophistocated later
            continue

    db.commit()


def create_artist_table(db_select, root_artist):
    '''
    Make a new table in the hiphopper database
    '''

    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(db_select.strip()))
    
    # the artist table, specific for chosen root artist 
    table_name = art_tbl_name.strip() + "_" + root_artist.strip()

    #++++++++++++++++++++++++++++++++++++++++++++
    # CONSIDER adding is_user_artist to columns
    #   facilitate weighting of rec's later (jpp, flag)
    #++++++++++++++++++++++++++++++++++++++++++++

    # create the table in MySQL
    cursor.execute("CREATE TABLE {0} (\
        pkid int NOT NULL auto_increment, \
        user_id int(20) NOT NULL, \
        artist_name char(150) CHARACTER SET utf8 NOT NULL, \
        artist_tw_sn char(150) CHARACTER SET utf8 NOT NULL, \
        twitter_counts int(20) NOT NULL, \
        genre char(150) CHARACTER SET utf8 NULL, \
        ecnest_hot decimal(5,2) NULL, \
        ecnest_familiar decimal(5,2) NULL, \
        PRIMARY KEY (pkid)) ENGINE=InnoDB;".format(table_name))

    db.commit()


def populate_artist_table(user_id, artist_name, artist_id,
    genre, ecnest_hot, ecnest_familiar, in_db, root_artist):

    db = mdb.connect('localhost', 'root', '',
        charset='utf8', use_unicode=True)

    cursor = db.cursor()
    cursor.execute('USE {0}'.format(in_db))
    
    # the table we're going to add rows to
    table_name = art_tbl_name.strip() + "_" + root_artist.strip()

    n_users = len(user_id)
    for i in range(n_users):
        cinsert = "INSERT INTO {0}(user_id, artist_name, \
            artist_tw_sn, twitter_counts, genre, ecnest_hot, \
            ecnest_familiar)".format(table_name)
        inp_row = "VALUES('%s','%s','%s','%s','%s','%s','%s')"%(
            user_id[i], artist_name[i], artist_id[i], twt_counts[i],
            genre[i], ecnest_hot[i], ecnest_familiar[i])
        execute_mdb = cinsert + inp_row + ';'
        cursor.execute(execute_mdb.encode("utf8"))

    db.commit()

def create_friends_table(db_select, root_artist):
    '''
    Make a new table in the hiphopper database 
    '''
    db = mdb.connect('localhost','root','')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(db_select.strip()))

    # the artist table, specific for chosen root artist 
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

    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(in_db))

    # the table we're going to add rows to
    table_name = frnds_tbl_name.strip() + "_" + root_artist.strip()

    # Loop over all friends of the current user
    for frnd in frnd_list:

        # load input into dummy variables
        # escape the strings
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


        print 'in friends into mysql: ', user_id, uname, usn, frnd.id, fname, fsn, frnd.followers_count, frnd.friends_count, frnd.profile_image_url

        try:

            # Load my MySQL commands into strings before executing
            cinsert = "INSERT INTO {0}(user_id, user_tw_name, user_tw_sn, friend_id, \
                friend_tw_name, friend_tw_sn, friend_follow_count, friend_friend_count)".format(table_name)

            inp_row = "VALUES('%s','%s','%s','%s','%s','%s','%s','%s')"%(user_id, uname, usn,
                frnd.id, fname, fsn, frnd.followers_count, frnd.friends_count)

            # Now execute MySQL command for adding a new row
            execute_mdb = cinsert + inp_row + ';'
            cursor.execute(execute_mdb.encode("utf8"))

        except:
            try:# try again without the url
                # make sure it's not the url we're storing for twitter
                # profile pictures
                cinsert = "INSERT INTO {0}(user_id, user_tw_name, user_tw_sn, \
                    friend_id, friend_tw_name, friend_tw_sn, \
                    friend_follow_count, \
                    friend_friend_count)".format(table_name)

                inp_row = "VALUES('%s','%s','%s','%s','%s',\
                    '%s','%s','%s')"%(user_id, uname, usn,
                    frnd.id, fname, fsn, frnd.followers_count, frnd.friends_count)

                execute_mdb = cinsert + inp_row + ';'
                cursor.execute(execute_mdb.encode("utf8"))
            except:
                # jpp, flag: throwing away users with extraordinarily
                #            crazy names... copyright symbols, TMs, etc...
                #            try something more sophistocated later
                continue

    # save the changes
    db.commit()


def create_test_table(db_select, root_artist):
    '''
    Make a new table in the hiphopper database 
    '''
    db = mdb.connect('localhost','root','')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(db_select.strip()))

    # the artist table, specific for chosen root artist 
    table_name = "test_" + root_artist.strip()

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


def populate_test_table(user_id, user_tw_name, user_tw_sn,
    frnd_list, in_db, root_artist):

    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(in_db))

    # the table we're going to add rows to
    table_name = "test_" + root_artist.strip()

    # Loop over all friends of the current user
    for frnd in frnd_list:

        # load input into dummy variables
        # escape the strings
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


        print 'in friends into mysql: ', user_id, uname, usn, frnd.id, fname, fsn, frnd.followers_count, frnd.friends_count, frnd.profile_image_url

        try:

            # Load my MySQL commands into strings before executing
            cinsert = "INSERT INTO {0}(user_id, user_tw_name, user_tw_sn, friend_id, \
                friend_tw_name, friend_tw_sn, friend_follow_count, friend_friend_count)".format(table_name)

            inp_row = "VALUES('%s','%s','%s','%s','%s','%s','%s','%s')"%(user_id, uname, usn,
                frnd.id, fname, fsn, frnd.followers_count, frnd.friends_count)

            # Now execute MySQL command for adding a new row
            execute_mdb = cinsert + inp_row + ';'
            cursor.execute(execute_mdb.encode("utf8"))

        except:
            try:# try again without the url
                # make sure it's not the url we're storing for twitter
                # profile pictures
                cinsert = "INSERT INTO {0}(user_id, user_tw_name, user_tw_sn, \
                    friend_id, friend_tw_name, friend_tw_sn, \
                    friend_follow_count, \
                    friend_friend_count)".format(table_name)

                inp_row = "VALUES('%s','%s','%s','%s','%s',\
                    '%s','%s','%s')"%(user_id, uname, usn,
                    frnd.id, fname, fsn, frnd.followers_count, frnd.friends_count)

                execute_mdb = cinsert + inp_row + ';'
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
    Make a new table in the hiphopper database 
    '''
    db = mdb.connect('localhost','root','')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(db_select.strip()))

    # the artist table, specific for chosen root artist 
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
    artist_id, artist_name, artist_sn, artist_genre,
    artist_familiarity, artist_hotness, in_db, root_artist):

    db = mdb.connect('localhost', 'root', '')
    cursor = db.cursor()
    cursor.execute('USE {0}'.format(in_db))

    # the table we're going to add rows to
    table_name = "artist_votes_" + root_artist.strip()

    # load input into dummy variables
    # escape the strings
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

    print ( 'in friends into mysql: ', user_id, uname, artist_id,
        art_name, art_sn, art_genre,
        artist_hotness, artist_familiarity )

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
