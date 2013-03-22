import json
import MySQLdb
import MySQLdb.cursors

CHUNK_SIZE = 5000

class DB(object):

    def __init__(self):
        db_config = dict([(k.encode('utf-8'), v.encode('utf-8')) for k, v in json.load(open('config/database.json')).iteritems()])
        self.db = MySQLdb.connect(**db_config)
        self.dbc = self.db.cursor(MySQLdb.cursors.DictCursor)

    def fill_empty_last_names(self):
        print "Setting empty last names in individual_contributions"
        while self.num_unfilled_last_names() > 0:
            print '  ' + str(self.num_unfilled_last_names()) + ' remaining...'
            self.dbc.execute("update individual_contributions set contributor_last_name = substring_index(contributor_name,',',1) where contributor_last_name is null limit 100000")
            self.db.commit()

    def num_unfilled_last_names(self):
        self.dbc.execute("select count(*) as cnt from individual_contributions where contributor_last_name is null")
        return self.dbc.fetchone()['cnt']

    def next_contributor_id(self):
        self.dbc.execute("select max(id) as maxid from contributors")
        maxid = self.dbc.fetchone()['maxid']
        if maxid == None:
            maxid = 0
        return maxid + 1

    def create_contributors(self, contributors):
        if len(contributors) > 0:
            self.dbc.executemany(
            """insert into contributors (id, full_name, first_name, middle_name, last_name, city, state, zipcode, employer, occupation)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            ((c['id'], c['full_name'], c['first_name'], c['middle_name'], c['last_name'], c['city'], c['state'], c['zipcode'], c['employer'], c['occupation']) for c in contributors)
            )
            self.db.commit()

    def save_contributions(self, contributions):
        for c in contributions:
            self.dbc.execute("update individual_contributions set contributor_id = %s where id = %s", (c['contributor_id'], c['id']))
        self.db.commit()

    def create_new_possible_matches(self, new_possible_matches):
        if len(new_possible_matches) > 0:
            self.dbc.executemany(
            """insert into contributor_matches (individual_contribution_id, contributor_id, confidence)
            values (%s, %s, %s)""",
            ((m['individual_contribution_id'], m['contributor_id'], m['confidence']) for m in new_possible_matches)
            )
            self.db.commit()

    def next_unlinked_contributions(self):
        self.dbc.execute("select id, contributor_name, city, state, zipcode, employer, occupation, contributor_last_name, contributor_id from individual_contributions where contributor_id is null limit %s", CHUNK_SIZE)
        return self.dbc.fetchall()

    def potential_contributors(self, contribution):
        self.dbc.execute("select * from contributors where last_name = %s and state = %s order by id", (contribution['contributor_last_name'], contribution['state']))
        return self.dbc.fetchall()


    def r_get_next_possible_match(self):
        self.dbc.execute("""
          select *
          from contributor_matches, individual_contributions, contributors
          where resolved = false and
            contributor_matches.contributor_id = contributors.id and
            contributor_matches.individual_contribution_id = individual_contributions.id
          order by contributor_matches.contributor_id
          limit 1
        """)
        return self.dbc.fetchone()

    def r_ignore_match(self, match):
        self.dbc.execute("update contributor_matches set resolved = true where id = %s", match['id'])
        self.db.commit()

    def r_resolve_match(self, match):
        self.dbc.execute("update individual_contributions set contributor_id = %s where id = %s", (match['contributor_id'], match['individual_contribution_id']))
        self.dbc.execute("update contributor_matches set resolved = true where individual_contribution_id = %s", match['individual_contribution_id'])
        self.db.commit()