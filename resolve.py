from fec.db import *

db = DB()

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

