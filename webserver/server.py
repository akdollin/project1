#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, session

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following uses the sqlite3 database test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
#DATABASEURI = "sqlite:///test.db"
DATABASEURI = "postgresql://acd2164:KAFBXH@w4111db.eastus.cloudapp.azure.com/acd2164"



#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
#engine.execute("""DROP TABLE IF EXISTS users;""")
#engine.execute("""CREATE TABLE IF NOT EXISTS users (
#  uid text,
#  password text
#);""")
#engine.execute("""INSERT INTO users(uid, password) VALUES ('aa1234', 'password'), ('xyz987', 'thisismypw'), ('ck2609', 'somethingrandom');""")
#
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT * FROM users")
  names = []
  for result in cursor:
    names.append(result)  # can also be accessed using result[0]
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  return render_template("anotherfile.html")


#
# KAT
#
# Login page checks if uid and password exist in database.
# If yes, go to home page. If no, return to log in page
# with error messages wrong uid or wrong password.
#
#
### info of the session kept in app's memory, hashmap mapping cookie to session object
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = 'super secret key'
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['uid']
        password = request.form['password']
        try:
            cursor = g.conn.execute(text('SELECT * FROM users WHERE userid = :name'), name = userid)
        #cursor = g.conn.execute('SELECT * FROM users WHERE uid = ?', userid)
        except:
            import traceback; traceback.print_exc()
        row = cursor.fetchone()
        if row:
            if password == row[1]:
                session['username'] = userid
                return redirect('/home')
            #else indicate wrong password, in the form of context for login (?)
        #else: indicate wrong username
        cursor.close()
    return render_template("login.html")
"""
    except:
        print "Actual exception"
        import traceback; traceback.print_exc()
"""


#
# KAT
#
# Sign up page checks if uid exists in database.
# If no, add uid and password to database. If yes,
# return to sign up page with error message used uid.
#
#
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    try:
        if request.method == 'POST':
            userid = request.form['uid']
            password = request.form['password']
            cursor = g.conn.execute(text('SELECT * FROM users WHERE userid = :name'), name = userid)
        #cursor = g.conn.execute('SELECT * FROM users WHERE uid = ?', userid)
            row = cursor.fetchone()
            if not row:
                g.conn.execute(text('INSERT INTO users VALUES (:name, :pw)'), name = userid, pw = password)
                return redirect('/login')
        #else indicate username used
            cursor.close()
    except:
        import traceback; traceback.print_exc()
    return render_template("signup.html")


#
# KAT
#
# Home page contains user's queue, option to edit/add
# service accounts, view search history, search for movie/
# artist, and log out (?)
#
#
@app.route('/home', methods=['GET', 'POST'])
def home():
    try:
        userid = session['username']
        print 'hi'
        cursor = g.conn.execute(text('SELECT q.position, m.title FROM queue q, movies m WHERE q.userid = :name AND q.movid = m.movid ORDER BY q.position'), name = userid)
        queue = []
        for result in cursor:
            queue.append(result)  # can also be accessed using result[0]
        cursor.close()
        context = dict(queue = queue, blabla = 'blabla', username = userid)
    #context = dict(blabla = 'blabla')
    except:
        import traceback; 
    return render_template("home.html", **context)


#
# KAT
#
#
#
#
#
#
@app.route('/managestreamacc', methods=['GET', 'POST'])
def managestreamacc():
    userid = session['username']
    cursor = g.conn.execute(text('SELECT x.extservname, e.extaccun, e.extaccid FROM belongto b, servedby s, externalaccounts e, externalservices x where b.userid = :name AND e.extaccid = b.extaccid AND e.extaccid=s.extaccid AND x.extservid=s.extservid'), name = userid)
    list = []
    for row in cursor:
        list.append(row)
    cursor.close()
    context = dict(username = userid, accounts = list)
    return render_template("managestreamacc.html", **context)

#
# KAT
#
#
#
#
#
#
@app.route('/addstreamacc', methods=['GET', 'POST'])
def addstreamacc():
    userid = session['username']
    cursor = g.conn.execute(text('SELECT extservname FROM externalservices'))
    menu = []
    for row in cursor:
        menu.append(row)
    cursor.close()
    getcontext = dict(menu = menu)
    if request.method == 'POST':
        
        service = request.form['service']
        exaccun = request.form['exaccun']
        exaccpw = request.form['exaccpw']
    
        currmaxid = g.conn.execute(text('SELECT max(extaccid) from externalaccounts'))
        cursor = g.conn.execute(text('SELECT extaccun FROM externalaccounts WHERE extaccun = :un AND extservid = '), un = exaccun)

    return render_template("/addstreamacc.html", **getcontext)


#
# KAT
#
#
#
#
#
#
@app.route('/search', methods=['GET', 'POST'])
def search():
    input = request.form['search']
    input = '%' + input + '%'
        
    
    cursor = g.conn.execute(text('SELECT title FROM movies WHERE title LIKE :inpt'), inpt = input)
    list = []
    for row in cursor:
      list.append(row)
    cursor.close()

    context = dict(input = input, movies = list)
    try:
        originput = request.form['search']
        input = '%' + originput + '%'
        
        cursor = g.conn.execute(text('SELECT title, movid FROM movies WHERE title LIKE :inpt'), inpt = input)
        movlist = []
        for row in cursor:
            movlist.append(row)
        cursor.close()

        cursor = g.conn.execute(text('SELECT artistfirstname, artistlastname, artistid FROM artists WHERE artistfirstname LIKE :inpt OR artistlastname LIKE :inpt'), inpt = input)
        artlist = []
        for row in cursor:
            artlist.append(row)
        cursor.close()

        cursor = g.conn.execute(text('SELECT genrename, genreid FROM genres WHERE genrename LIKE :inpt'), inpt = input)
        genlist = []
        for row in cursor:
            genlist.append(row)
        cursor.close()

        cursor = g.conn.execute(text('SELECT DISTINCT awardname, year FROM awards WHERE awardname LIKE :inpt OR category LIKE :inpt OR role LIKE :inpt OR artist LIKE :inpt'), inpt = input)
        awlist = []
        for row in cursor:
            awlist.append(row)
        cursor.close()

        context = dict(originput = originput, movies = movlist, artists = artlist, genres = genlist, awards = awlist)

    except:
        import traceback; traceback.print_exc()
    print request.args
    return render_template("/search.html", **context)


@app.route('/searchhistory', methods=['GET', 'POST'])
def searchhistory():
  userid = session['username']
  cursor = g.conn.execute(text('Select m.title, s.movTimeSearch FROM Movies m, searchHistory_Movies s WHERE s.userid= :name AND s.movid=m.movid ORDER BY s.movTimeSearch DESC'), name = userid)
  searchmovList = []
  for result in cursor:
    searchmovList.append((result.title, result[1]))
  cursor.close()

  cursor2 = g.conn.execute(text('Select a.artistfirstName, a.artistlastname, s.artTimeSearch FROM Artists a, searchHistory_Artists s WHERE s.userid = :name AND  s.artistid=a.artistid ORDER BY s.artTimeSearch DESC'), name = userid)
  searchartList = []
  for result2 in cursor2:
    searchartList.append((result2[0]+' '+result2[1], result2[2]))
  cursor2.close()

  context = dict(searchmovList=searchmovList, searchartList = searchartList, username = userid)
  return render_template("searchhistory.html", **context)


@app.route('/rate', methods=['GET', 'POST'])
def rate():
  userid = session['username']
  cursor = g.conn.execute(text('Select m.title, r.value FROM movies m, rate r WHERE r.userid = :name AND  r.movid=m.movid ORDER BY r.value DESC'), name = userid)
  rateList = []
  for result in cursor:
    rateList.append((result.title, result.value))
  cursor.close()
  #userid = 'kivi' test 
  context = dict(rateList=rateList, username = userid)
  return render_template("rate.html", **context) 

@app.route('/browse', methods=['GET', 'POST'])
def browse():
  userid = session['username']
  cursor = g.conn.execute(text('Select m.title, m.year, g.genreName, m.movid FROM Movies m, CategorizedBy c, Genres g WHERE m.movid = c.movid AND c.genreid = g.genreid ORDER BY m.title ASC'))

  movieList = []
  for result in cursor:
    movieList.append((result.title, result.year, result[2], result[3])) 
  cursor.close()
  context = dict(movieList=movieList, username = userid)


  if request.method == 'POST':
    sort = request.form['sort']
    if sort == 'Sort By Title':
      cursor = g.conn.execute(text('Select m.title, m.year, g.genreName, m.movid FROM Movies m, CategorizedBy c, Genres g WHERE m.movid = c.movid AND c.genreid = g.genreid ORDER BY m.title ASC'))
      movieList1 = []
      for result in cursor:
        movieList1.append((result.title, result.year, result[2], result[3]))
      cursor.close()
      context = dict(movieList1=movieList1, username = userid)

    if sort == 'Sort By Year':
      cursor = g.conn.execute(text('Select m.year, m.title, g.genreName, m.movid FROM Movies m, CategorizedBy c, Genres g WHERE m.movid = c.movid AND c.genreid = g.genreid ORDER BY m.year'))
      movieList2 = []
      for result in cursor:
        movieList2.append((result.year, result.title, result[2], result[3]))
      cursor.close()
      context = dict(movieList2=movieList2, username = userid)

    if sort == 'Sort By Genre':
      cursor = g.conn.execute(text('Select g.genreName, m.title, m.year, m.movid FROM Movies m, CategorizedBy c, Genres g WHERE m.movid = c.movid AND c.genreid = g.genreid ORDER BY g.genreName'))
      movieList3 = []
      for result in cursor:
        movieList3.append((result[0], result.title, result.year, result[3]))
      cursor.close()
      context = dict(movieList3=movieList3, username = userid)

  #userid = 'kivi'
  return render_template("browse.html", **context)


@app.route('/movieinfo', methods=['GET', 'POST'])
def movieinfo():
  userid = session['username']

  movieinfoList = []

  movid = request.args.get('movid')


  #movid = request.form['movid']

  
  cursor = g.conn.execute(text('Select m.title, m.year, m.length, m.imdbrating from movies m WHERE movid= :movid'), movid = movid)

  for result in cursor:
    movieinfoList.append((result.title, result.year, result.length, result.imdbrating)) 
  cursor.close()

  context = dict(movieinfoList=movieinfoList, username = userid)
  return render_template("movieinfo.html", **context)


@app.route('/hooray')
def hooray():
    """
    if not session.get(uid):
        abort(401)
    """
    return render_template("hooray.html")





# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  g.conn.execute('INSERT INTO users VALUES (NULL, ?)', name)
  return redirect('/')

"""
@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()
"""

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
