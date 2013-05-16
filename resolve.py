from optparse import OptionParser
from campfin.db import *

parser = OptionParser()
parser.add_option("-d", "--db", dest="dbname",
                  default=None,
                  help="Database name with data to resolve")
parser.add_option("-t", "--table",
                  default=None,
                  help="Name of table to resolve")
(options, args) = parser.parse_args()

db = DB()
if options.table == None:
    tables_to_resolve = db.all_linkable_tables()
else:
    tables_to_resolve = [[db.db['database'], options.table]]

for dbname, table in tables_to_resolve:
    db.set_table(dbname, table)
    while True:
        match = db.r_get_next_partial_match()
        if match == None:
            break

        print "%s, %s %s %s (%s - %s)" % (match['name1'], match['city1'], match['state1'], match['zip1'], match['occupation1'], match['employer1'])
        print "%s, %s %s %s (%s - %s)" % (match['name2'], match['city2'], match['state2'], match['zip2'], match['occupation2'], match['employer2'])

        key = ''
        while key != 'Y' and key != 'N':
            key = raw_input('Is this a match? (y/n)').upper()

        if key == 'N':
            db.r_ignore_match(match)
        else:
            db.r_resolve_match(match)

