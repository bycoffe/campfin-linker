import yaml
import MySQLdb
import MySQLdb.cursors

CHUNK_SIZE = 5000

class DB(object):

    def __init__(self):
        self.db_config = yaml.load(open('config/database.yml'))
        self.canonical_config = self.db_config['canonical']
        self.canonical = [x for x in self.db_config['databases'] if x['database'] == self.canonical_config['database']][0]
        self.possible_config = self.db_config['possibles']
        self.possible = [x for x in self.db_config['databases'] if x['database'] == self.possible_config['database']][0]
        self.dbs = {
            "possibles": MySQLdb.connect(**self.db_config_for(self.possible)),
            "canonical": MySQLdb.connect(**self.db_config_for(self.canonical))
        }
        self.dbcs = {"canonical": self.dbs["canonical"].cursor(MySQLdb.cursors.DictCursor),
                     "possibles": self.dbs["possibles"].cursor(MySQLdb.cursors.DictCursor),
        }
        self.set_table()

    def set_table(self, dbname=None, table=None):
        self.db = self.db_config['databases'][0] if dbname == None else self.get_db_config(dbname)
        self.tablename = self.db['linkable_tables'][0]['table'] if table == None else table
        self.table_config = [x for x in self.db['linkable_tables'] if x['table'] == self.tablename][0]
        self.dbs["linker"] = MySQLdb.connect(**self.db_config_for(self.db))
        self.dbcs["linker"] = self.dbs["linker"].cursor(MySQLdb.cursors.DictCursor)

    def all_linkable_tables(self):
        tables = []
        for db in self.db_config['databases']:
            for table in db['linkable_tables']:
                tables.append([db['database'], table['table']])
        return tables

    def execute(self, db, query, args=[], commit=True):
        self.dbcs[db].execute(query, args);
        if commit:
            self.dbs[db].commit()

    def get_db_config(self, dbname):
        matches = [x for x in self.db_config['databases'] if x['database'] == dbname]
        if matches:
            return matches[0]

    def db_config_for(self, db):
        return {
            'host': db['host'],
            'db': db['database'],
            'user': db['username'],
            'passwd': db['password']
        }

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
          select %s as id, %s as full_name, %s as city, %s as state, %s as zipcode, %s as employer, %s as occupation, %s as canonical_id from %s where %s is null limit %s
          """ %
          (self.table_config['id'], self.table_config['full_name'], self.table_config['city'], self.table_config['state'], self.table_config['zipcode'], self.table_config['employer'], self.table_config['occupation'], self.table_config['canonical_id'], self.tablename, self.table_config['canonical_id'], CHUNK_SIZE))
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
              (self.tablename, self.table_config['canonical_id'], c['canonical_id'], c['id']))
        self.dbs['linker'].commit()

    def create_new_possible_matches(self, new_possible_matches):
        if len(new_possible_matches) > 0:
            str_insert = "insert into %s (canonical_id, object_table, object_id, confidence)" % (self.possible_config['table_name'])
            self.dbcs['possibles'].executemany(str_insert + """
              values (%s, %s, %s, %s)
              """,
              ((m['canonical_id'], self.tablename, m['object_id'], m['confidence']) for m in new_possible_matches))
            self.dbs['possibles'].commit()

    def r_get_next_possible_match(self):
        self.dbcs['possibles'].execute("""
          select %s.id as id, %s.object_id as object_id, %s.canonical_id as canonical_id, %s.%s as name1, %s.%s as name2, %s.%s as city1, %s.%s as city2, %s.%s as state1, %s.%s as state2, %s.%s as zip1, %s.%s as zip2, %s.%s as occupation1, %s.%s as occupation2, %s.%s as employer1, %s.%s as employer2
          from %s, %s, %s
          where resolved = false and
            %s.canonical_id = %s.%s and
            %s.object_table = '%s' and
            %s.object_id = %s.%s
          order by %s.canonical_id
          limit 1
        """ %
        (self.possible_config['table_name'], self.possible_config['table_name'], self.possible_config['table_name'], self.tablename, self.table_config['full_name'], self.canonical_config['table_name'], self.canonical_config['full_name'], self.tablename, self.table_config['city'], self.canonical_config['table_name'], self.canonical_config['city'], self.tablename, self.table_config['state'], self.canonical_config['table_name'], self.canonical_config['state'], self.tablename, self.table_config['zipcode'], self.canonical_config['table_name'], self.canonical_config['zipcode'], self.tablename, self.table_config['occupation'], self.canonical_config['table_name'], self.canonical_config['occupation'], self.tablename, self.table_config['employer'], self.canonical_config['table_name'], self.canonical_config['employer'],
        self.possible_config['table_name'], self.tablename, self.canonical_config['table_name'], self.possible_config['table_name'], self.canonical_config['table_name'], self.canonical_config['id'], self.possible_config['table_name'], self.tablename, self.possible_config['table_name'], self.tablename, self.table_config['id'], self.possible_config['table_name']))
        return self.dbcs['possibles'].fetchone()

    def r_ignore_match(self, match):
        self.dbcs['possibles'].execute("update %s set resolved = true where object_table = '%s' and object_id = %s" % (self.possible_config['table_name'], self.tablename, match['object_id']))
        self.dbs['possibles'].commit()

    def r_resolve_match(self, match):
        self.dbcs['possibles'].execute("update %s set %s = %s where id = %s" % (self.tablename, self.table_config['canonical_id'], match['canonical_id'], match['object_id']))
        self.dbcs['possibles'].execute("update %s set resolved = true where object_table = '%s' and object_id = %s" % (self.possible_config['table_name'], self.tablename, match['object_id']))
        self.dbs['possibles'].commit()
