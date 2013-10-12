import yaml
import MySQLdb
import MySQLdb.cursors

CHUNK_SIZE = 5000

class DB(object):

    def __init__(self):
        self.db_config = yaml.load(open('config/database.yml'))
        self.individuals_config = self.db_config['individuals']
        self.individuals_db_config = self.get_db_config(self.individuals_config['database']) or self.db_config['databases'][0]
        self.partial_matches_config = self.db_config['partial_matches']
        self.partial_matches_db_config = self.get_db_config(self.partial_matches_config['database']) or self.db_config['databases'][0]
        self.dbs = {
            "individuals": MySQLdb.connect(**self.db_config_for(self.individuals_db_config)),
            "partial_matches": MySQLdb.connect(**self.db_config_for(self.partial_matches_db_config))
        }
        self.dbcs = {"individuals": self.dbs["individuals"].cursor(MySQLdb.cursors.DictCursor),
                     "partial_matches": self.dbs["partial_matches"].cursor(MySQLdb.cursors.DictCursor),
        }
        self.set_table()

    def set_table(self, dbname=None, table=None):
        self.db = self.db_config['databases'][0] if dbname == None else self.get_db_config(dbname)
        self.tablename = self.db['linkable_tables'][0]['table'] if table == None else table
        self.table_config = [x for x in self.db['linkable_tables'] if x['table'] == self.tablename]
        if len(self.table_config) == 0:
            print "Table %s not found in database.yml" % self.tablename
            exit()
        else:
            self.table_config = self.table_config[0]
        for k in self.table_config.keys():
            if self.table_config[k] == None:
                self.table_config[k] = "''"
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
        self.dbcs['individuals'].execute("""
          select max(%s) as maxid from %s
          """ %
          (self.individuals_config['id'], self.individuals_config['table_name']))
        maxid = self.dbcs['individuals'].fetchone()['maxid']
        if maxid == None:
            maxid = 0
        return maxid + 1

    def unlinked_contributions_count(self):
        self.dbcs['linker'].execute("select COUNT(*) from %s where %s is null" % (self.tablename, self.table_config['individual_id']))
        return int(self.dbcs['linker'].fetchone()['COUNT(*)'])

    def next_unlinked_contributions(self):
        self.dbcs['linker'].execute("""
          select %s as id, %s as full_name, %s as city, %s as state, %s as zipcode, %s as employer, %s as occupation, %s as individual_id from %s where %s is null limit %s
          """ %
          (self.table_config['id'], self.table_config['full_name'], self.table_config['city'], self.table_config['state'], self.table_config['zipcode'], self.table_config['employer'], self.table_config['occupation'], self.table_config['individual_id'], self.tablename, self.table_config['individual_id'], CHUNK_SIZE))
        return self.dbcs['linker'].fetchall()

    def potential_contributors(self, contribution):
        self.dbcs['individuals'].execute("""
          select * from %s where %s = '%s' and %s = '%s' order by %s
          """ %
          (self.individuals_config['table_name'], self.individuals_config['last_name'], MySQLdb.escape_string(contribution['last_name']), self.individuals_config['state'], MySQLdb.escape_string(contribution['state']), self.individuals_config['id']))
        return self.dbcs['individuals'].fetchall()

    def create_contributors(self, contributors):
        if len(contributors) > 0:
            str_insert = "insert into %s (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)" % (self.individuals_config['table_name'], self.individuals_config['id'], self.individuals_config['full_name'], self.individuals_config['first_name'], self.individuals_config['middle_name'], self.individuals_config['last_name'], self.individuals_config['city'], self.individuals_config['state'], self.individuals_config['zipcode'], self.individuals_config['employer'], self.individuals_config['occupation'])
            self.dbcs['individuals'].executemany(str_insert + """
              values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
              """,
              ((c['id'], c['full_name'], c['first_name'], c['middle_name'], c['last_name'], c['city'], c['state'], c['zipcode'], c['employer'], c['occupation']) for c in contributors))
            self.dbs['individuals'].commit()

    def save_contributions(self, contributions):
        for c in contributions:
            if c['individual_id'] == None:
                continue
            self.dbcs['linker'].execute("""
              update %s set %s = %s where %s = %s
              """ %
              (self.tablename, self.table_config['individual_id'], c['individual_id'], self.table_config['id'], c['id']))
        self.dbs['linker'].commit()

    def create_new_partial_matches(self, new_partial_matches):
        if len(new_partial_matches) > 0:
            str_insert = "insert into %s (individual_id, object_table, object_id, confidence)" % (self.partial_matches_config['table_name'])
            self.dbcs['partial_matches'].executemany(str_insert + """
              values (%s, %s, %s, %s)
              """,
              ((m['individual_id'], self.tablename, m['object_id'], m['confidence']) for m in new_partial_matches))
            self.dbs['partial_matches'].commit()

    def r_get_next_partial_match(self):
        self.dbcs['partial_matches'].execute("""
          select %s.id as id, %s.object_id as object_id, %s.individual_id as individual_id, %s.%s as name1, %s.%s as name2, %s.%s as city1, %s.%s as city2, %s.%s as state1, %s.%s as state2, %s.%s as zip1, %s.%s as zip2, %s.%s as occupation1, %s.%s as occupation2, %s.%s as employer1, %s.%s as employer2
          from %s, %s, %s
          where resolved = false and
            %s.individual_id = %s.%s and
            %s.object_table = '%s' and
            %s.object_id = %s.%s
          order by %s.individual_id
          limit 1
        """ %
        (self.partial_matches_config['table_name'], self.partial_matches_config['table_name'], self.partial_matches_config['table_name'], self.tablename, self.table_config['full_name'], self.individuals_config['table_name'], self.individuals_config['full_name'], self.tablename, self.table_config['city'], self.individuals_config['table_name'], self.individuals_config['city'], self.tablename, self.table_config['state'], self.individuals_config['table_name'], self.individuals_config['state'], self.tablename, self.table_config['zipcode'], self.individuals_config['table_name'], self.individuals_config['zipcode'], self.tablename, self.table_config['occupation'], self.individuals_config['table_name'], self.individuals_config['occupation'], self.tablename, self.table_config['employer'], self.individuals_config['table_name'], self.individuals_config['employer'],
        self.partial_matches_config['table_name'], self.tablename, self.individuals_config['table_name'], self.partial_matches_config['table_name'], self.individuals_config['table_name'], self.individuals_config['id'], self.partial_matches_config['table_name'], self.tablename, self.partial_matches_config['table_name'], self.tablename, self.table_config['id'], self.partial_matches_config['table_name']))
        return self.dbcs['partial_matches'].fetchone()

    def r_ignore_match(self, match):
        self.dbcs['partial_matches'].execute("update %s set resolved = true where object_table = '%s' and object_id = %s" % (self.partial_matches_config['table_name'], self.tablename, match['object_id']))
        self.dbs['partial_matches'].commit()

    def r_resolve_match(self, match):
        self.dbcs['partial_matches'].execute("update %s set %s = %s where id = %s" % (self.tablename, self.table_config['individual_id'], match['individual_id'], match['object_id']))
        self.dbcs['partial_matches'].execute("update %s set resolved = true where object_table = '%s' and object_id = %s" % (self.partial_matches_config['table_name'], self.tablename, match['object_id']))
        self.dbs['partial_matches'].commit()
