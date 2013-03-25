import simplejson as json
import MySQLdb
import MySQLdb.cursors

CHUNK_SIZE = 5000

class DB(object):

    def __init__(self, dbname=None, table=None):
        self.dbname = dbname
        self.table = table
        self.db_config = json.load(open('config/database.json'))
        self.canonical_config = self.db_config['canonical']
        self.possible_config = self.db_config['possibles']
        if self.dbname:
            self.table_config = self.db_config['databases'][self.dbname]['linkable_tables'][self.table]
        self.dbs = {"canonical": MySQLdb.connect(**self.db_config['databases'][self.db_config['canonical']['database']]['connection']),
                    "possibles": MySQLdb.connect(**self.db_config['databases'][self.db_config['possibles']['database']]['connection'])}
        self.dbcs = {"canonical": self.dbs["canonical"].cursor(MySQLdb.cursors.DictCursor),
                    "possibles": self.dbs["possibles"].cursor(MySQLdb.cursors.DictCursor)}
        if self.dbname:
            self.dbs['linker'] = MySQLdb.connect(**self.db_config['databases'][self.dbname]['connection'])
            self.dbcs['linker'] = self.dbs["linker"].cursor(MySQLdb.cursors.DictCursor)

    def fill_empty_last_names(self):
        print "Setting empty last names in individual_contributions"
        while self.num_unfilled_last_names() > 0:
            print '  ' + str(self.num_unfilled_last_names()) + ' remaining...'
            self.dbcs['linker'].execute("""
              update %s set %s = substring_index(%s, ',', 1) where %s is null limit 100000
              """ %
              (self.table, self.table_config['last_name'], self.table_config['full_name'], self.table_config['last_name']))
            self.dbs['linker'].commit()

    def num_unfilled_last_names(self):
        self.dbcs['linker'].execute("""
          select count(*) as cnt from %s where %s is null
          """ %
          (self.table, self.table_config['last_name']))
        return self.dbcs['linker'].fetchone()['cnt']

    def next_contributor_id(self):
        self.dbcs['canonical'].execute("""
          select max(%s) as maxid from %s
          """ %
          (self.canonical_config['id'], self.canonical_config['table_name']))
        maxid = self.dbcs['canonical'].fetchone()['maxid']
        if maxid == None:
            maxid = 0
        return maxid + 1

    def next_unlinked_contributions(self):
        self.dbcs['linker'].execute("""
          select %s as id, %s as full_name, %s as city, %s as state, %s as zipcode, %s as employer, %s as occupation, %s as last_name, %s as canonical_id from %s where %s is null limit %s
          """ %
          (self.table_config['id'], self.table_config['full_name'], self.table_config['city'], self.table_config['state'], self.table_config['zipcode'], self.table_config['employer'], self.table_config['occupation'], self.table_config['last_name'], self.table_config['canonical_id'], self.table, self.table_config['canonical_id'], CHUNK_SIZE))
        return self.dbcs['linker'].fetchall()

    def potential_contributors(self, contribution):
        self.dbcs['canonical'].execute("""
          select * from %s where %s = '%s' and %s = '%s' order by %s
          """ %
          (self.canonical_config['table_name'], self.canonical_config['last_name'], MySQLdb.escape_string(contribution['last_name']), self.canonical_config['state'], MySQLdb.escape_string(contribution['state']), self.canonical_config['id']))
        return self.dbcs['canonical'].fetchall()

    def create_contributors(self, contributors):
        if len(contributors) > 0:
            str_insert = "insert into %s (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % (self.canonical_config['table_name'], self.canonical_config['id'], self.canonical_config['full_name'], self.canonical_config['first_name'], self.canonical_config['middle_name'], self.canonical_config['last_name'], self.canonical_config['city'], self.canonical_config['state'], self.canonical_config['zipcode'], self.canonical_config['employer'], self.canonical_config['occupation'])
            self.dbcs['canonical'].executemany(str_insert + """
              values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              """,
              ((c['id'], c['full_name'], c['first_name'], c['middle_name'], c['last_name'], c['city'], c['state'], c['zipcode'], c['employer'], c['occupation']) for c in contributors))
            self.dbs['canonical'].commit()

    def save_contributions(self, contributions):
        for c in contributions:
            if c['canonical_id'] == None:
                continue
            self.dbcs['linker'].execute("""
              update %s set %s = %s where id = %s
              """ %
              (self.table, self.table_config['canonical_id'], c['canonical_id'], c['id']))
        self.dbs['linker'].commit()

    def create_new_possible_matches(self, new_possible_matches):
        if len(new_possible_matches) > 0:
            str_insert = "insert into %s (%s, object_table, object_id, confidence)" % (self.possible_config['table_name'], self.possible_config['canonical_id'])
            self.dbcs['possibles'].executemany(str_insert + """
              values (%s, %s, %s, %s)
              """,
              ((m['canonical_id'], self.table, m['object_id'], m['confidence']) for m in new_possible_matches))
            self.dbs['possibles'].commit()

    def r_get_next_possible_match(self):
        self.dbcs['possibles'].execute("""
          select *
          from %s, %s, %s
          where resolved = false and
            %s.%s = %s.%s and
            %s.object_table = '%s' and
            %s.object_id = %s.%s
          order by %s.%s
          limit 1
        """ %
        (self.possible_config['table_name'], self.table, self.canonical_config['table_name'], self.possible_config['table_name'], self.possible_config['canonical_id'], self.canonical_config['table_name'], self.canonical_config['id'], self.possible_config['table_name'], self.table, self.possible_config['table_name'], self.table, self.table_config['id'], self.possible_config['table_name'], self.possible_config['canonical_id']))
        return self.dbcs['possibles'].fetchone()

    def r_ignore_match(self, match):
        self.dbcs['possibles'].execute("update %s set resolved = true where object_table = '%s' and object_id = %s" % (self.possible_config['table_name'], self.table, match['object_id']))
        self.dbs['possibles'].commit()

    def r_resolve_match(self, match):
        self.dbcs['possibles'].execute("update individual_contributions set contributor_id = %s where id = %s", (match['contributor_id'], match['individual_contribution_id']))
        self.dbcs['possibles'].execute("update contributor_matches set resolved = true where individual_contribution_id = %s", match['individual_contribution_id'])
        self.dbs['possibles'].commit()