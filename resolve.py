from optparse import OptionParser
from fec.db import *

parser = OptionParser()
parser.add_option("-d", "--db", dest="dbname",
                  default="fec",
                  help="Database name with data to resolve")
parser.add_option("-t", "--table",
                  default="individual_contributions",
                  help="Name of table to resolve")
(options, args) = parser.parse_args()

db = DB(options.dbname, options.table)

while True:

    match = db.r_get_next_possible_match()
    if match == None:
        break

    print "%s, %s %s %s (%s - %s)" % (match['contributor_name'], match['city'], match['state'], match['zipcode'], match['occupation'], match['employer'])
    print "%s, %s %s %s (%s - %s)" % (match['full_name'], match['contributors.city'], match['contributors.state'], match['contributors.zipcode'], match['contributors.occupation'], match['contributors.employer'])

    key = ''
    while key != 'Y' and key != 'N':
        key = raw_input('Is this a match? (y/n)').upper()

    if key == 'N':
        db.r_ignore_match(match)
    else:
        db.r_resolve_match(match)

