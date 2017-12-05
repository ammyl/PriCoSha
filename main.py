from flask import render_template, flash, redirect, session, url_for, request, g
from appdef import app, conn
import tags, content_edit_delete, friends, group, post_tag
import getfriends, post_tag
from post_tag import makePost
import reply_post

@app.route('/')
def main():
    # if the user is logged in, have all the posts available to the user display
    if (session.get('logged_in') == True):
        # query to get all the posts available to the user
        postQuery = 'SELECT content.id, content.username, content.timest, content.file_path, content.content_name \
                    FROM CONTENT \
                    WHERE content.public = 1 \
                        OR username = %s \
                        OR username in (SELECT username \
                                        FROM member \
                                        WHERE group_name in \
                                        (SELECT group_name \
                                        FROM member \
                                        WHERE member.username = %s)) \
                        OR username in (SELECT username_creator \
                                        FROM member \
                                        WHERE username = %s) \
                        OR username in (SELECT username \
                                        FROM member \
                                        WHERE username_creator=%s) \
                    ORDER BY timest DESC'

        cursor = conn.cursor()
        username = session['username']
        cursor.execute(postQuery, (username, username, username, username))
        postData = cursor.fetchall()
        cursor.close()

        # get all the likes
        likesQuery = 'SELECT * FROM likes'
        likesData = getData(likesQuery)
        # get likes from session username
        cursor = conn.cursor()
        userLikesQuery = 'SELECT * FROM likes WHERE username_liker = %s'
        cursor.execute(userLikesQuery, (username))
        userLikesData = cursor.fetchall()
        cursor.close()

        # get all the tags
        tagsQuery = 'SELECT * FROM tag WHERE status = 1'
        tagsData = getData(tagsQuery)
        orgTagsData = {}
        tagz = organizeData(orgTagsData, tagsData)

        # get comments for posts
        commentsQuery = 'SELECT * FROM comment'
        commentsData = getData(commentsQuery)
        comments = storeComments(commentsData)

        # get all the users
        userQuery = 'SELECT username, first_name, last_name FROM person'
        userData = getData(userQuery)

        storeUsers(userData)

        return render_template("index.html", data=postData, likesData=likesData, userLikesData=userLikesData, tagsData=tagsData, commentsData=commentsData, userData=userData, tagz=tagz)
    return render_template("index.html")

# function to make queries to database to acquire info
def getData(query):
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.commit()
    cursor.close()
    return(data)

def storeUsers(data):
    # store users in a session users dictionary
    # which can be used to access users' first name and last name.
    session['users'] = {}
    for user in data:
        session['users'][user['username']] = {}
        session['users'][user['username']]['first_name'] = user['first_name']
        session['users'][user['username']]['last_name'] = user['last_name']
        # adding friends for users
        session['users'][user['username']]['friends'] = []
        session['users'][user['username']]['friends'] = getfriends.getFriend()

        # including groups you own
        session['users'][user['username']]['groups'] = []
        addGroups(session['users'][user['username']]['groups'])
    return;

def addGroups(groupList):
    friendGroup = "SELECT group_name, description \
                    FROM friendgroup \
                    WHERE username = %s"
    cursor = conn.cursor()
    cursor.execute(friendGroup, (session['username']))
    groupList.extend(cursor.fetchall())
    cursor.close()

def storeComments(data):
    session['comments'] = {}
    for info in data:
        if info['id'] not in session['comments'].keys():
            session['comments'][info['id']] = []
        session['comments'][info['id']].append({'username': info['username'],
                                            'comment_text': info['comment_text'],
                                            'time': info['timest']})
    return;


def organizeData(diction, data):
    for mem in data:
        if mem['id'] not in diction.keys():
            diction[mem['id']] = []
        diction[mem['id']].append({
            'timest': mem['timest'],
            'username_tagee': mem['username_taggee'],
            'status':mem['status'],
            'username_tager': mem['username_tagger']
        })
    return(diction)
