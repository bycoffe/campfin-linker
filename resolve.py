from fec.db import *

def get_next_possible_match():
    dbc.execute("""
      select *
      from contributor_matches, individual_contributions, contributors
      where resolved = false and
        contributor_matches.contributor_id = contributors.id and
        contributor_matches.individual_contribution_id = individual_contributions.id
      order by contributor_matches.contributor_id
      limit 1
    """)
    return dbc.fetchone()

def ignore_match(match):
    dbc.execute("update contributor_matches set resolved = true where id = %s", match['id'])
    db.commit()

def resolve_match(match):
    dbc.execute("update individual_contributions set contributor_id = %s where id = %s", (match['contributor_id'], match['individual_contribution_id']))
    dbc.execute("update contributor_matches set resolved = true where individual_contribution_id = %s", match['individual_contribution_id'])
    db.commit()

while True:

    match = get_next_possible_match()
    if match == None:
        break

    print "%s, %s %s %s (%s - %s)" % (match['contributor_name'], match['city'], match['state'], match['zipcode'], match['occupation'], match['employer'])
    print "%s, %s %s %s (%s - %s)" % (match['full_name'], match['contributors.city'], match['contributors.state'], match['contributors.zipcode'], match['contributors.occupation'], match['contributors.employer'])

    key = ''
    while key != 'Y' and key != 'N':
        key = raw_input('Is this a match? (y/n)').upper()

    if key == 'N':
        ignore_match(match)
    else:
        resolve_match(match)

