import json
import MySQLdb
import MySQLdb.cursors

db_config = dict([(k.encode('utf-8'), v.encode('utf-8')) for k, v in json.load(open('config/database.json')).iteritems()])
db = MySQLdb.connect(**db_config)
dbc = db.cursor(MySQLdb.cursors.DictCursor)