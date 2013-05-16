from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from campfin.db import *
from campfin.trainer import *

CONFIDENCE_KEEP = 0.65
CONFIDENCE_CHECK = 0.51
MAX_CONTRIBUTOR_CACHE_SIZE = 1000000 # Each item about 1kB

class Linker(object):

    def __init__(self):
        self.db = DB()
        self.trainer = Trainer()
        self.clf = self.trainer.train()
        self.contribution_names = {}

    def link(self, dbname=None, table=None):
        self.link_all() if table == None else self.link_one(dbname, table)

    def link_all(self):
        for dbname, table in self.db.all_linkable_tables():
            self.link_one(dbname, table)

    def link_one(self, dbname, table):
        self.db.set_table(dbname, table)
        self.table = table
        print "Linking contributions in " + self.db.db['database'] + ":" + self.table
        max_contributor_id = self.db.next_contributor_id()
        contributor_cache = {}
        contributor_cache_size = 0
        while True:
            ts_start = datetime.now()

            # Get the next batch of contributions to process
            unlinked_contributions = self.db.next_unlinked_contributions()
            if len(unlinked_contributions) == 0:
                break

            self.contribution_names = {}
            new_contributors = []
            new_contributors_by_namekey = {}
            used_name_keys = {}
            new_partial_matches = []
            for uc in unlinked_contributions:
                uc_features = self._contribution_features(uc)
                name_key = self._name_key(uc_features)

                # Get potential contributors for this contribution
                while contributor_cache_size > MAX_CONTRIBUTOR_CACHE_SIZE:
                    k, v = contributor_cache.popitem()
                    contributor_cache_size -= len(v)
                if name_key in contributor_cache:
                    contributors = contributor_cache[name_key]
                else:
                    contributors = list(self.db.potential_contributors(uc_features))
                    contributor_cache[name_key] = contributors
                    contributor_cache_size += len(contributors)

                # Find match in contributors
                new_contributors_for_key = new_contributors_by_namekey[name_key] if name_key in new_contributors_by_namekey else []
                contributor_id = self._first_matching_contributor_id(uc_features, contributors + new_contributors_for_key, new_partial_matches)

                # If no contributor was found, create a new one
                if contributor_id == None:
                    contributor = uc_features
                    contributor['id'] = max_contributor_id
                    max_contributor_id += 1
                    new_contributors.append(contributor)
                    if not name_key in new_contributors_by_namekey:
                        new_contributors_by_namekey[name_key] = []
                    new_contributors_by_namekey[name_key].append(contributor)
                    contributor_cache[name_key].append(contributor)
                    contributor_cache_size += 1
                    contributor_id = contributor['id']

                # Link the contribution
                uc['individual_id'] = contributor_id

            self.db.create_contributors(new_contributors)
            self.db.save_contributions(unlinked_contributions)
            self.db.create_new_partial_matches(new_partial_matches)
            print "Processed " + str(len(unlinked_contributions)) + " contributions in " + str(datetime.now() - ts_start)

    # Find the first matching contributor in a list
    def _first_matching_contributor_id(self, contribution_features, contributors, new_partial_matches):
        partial_matches_to_add = []
        for c in contributors:
            c1f, c2f = contribution_features, c
            compstring1 = '%s %s' % (c1f['first_name'], c1f['city'])
            compstring2 = '%s %s' % (c2f['first_name'], c2f['city'])
            if self.trainer.jaccard_sim(self.trainer.shingle(compstring1.lower(), 2), self.trainer.shingle(compstring2.lower(), 2)) < self.trainer.initial_sim:
                continue
            featurevector = str(self.trainer.create_featurevector(c1f, c2f))
            edge = self.clf.predict_proba(eval(featurevector))
            if edge[0][1] > CONFIDENCE_KEEP:
                return c['id']
            elif edge[0][1] > CONFIDENCE_CHECK:
                partial_matches_to_add.append({'object_id': contribution_features['id'], 'individual_id': c['id'], 'confidence': edge[0][1]})
        new_partial_matches.extend(partial_matches_to_add)
        return None

    def _contribution_features(self, contribution):
        if contribution['id'] in self.contribution_names:
            parsed_name = self.contribution_names[contribution['id']]
        else:
            human_name = HumanName(unicode(contribution['full_name'].upper(), errors='ignore'))
            parsed_name = {'first': human_name.first, 'middle': human_name.middle, 'last': human_name.last}
            self.contribution_names[contribution['id']] = parsed_name
        return {
            'id': contribution['id'],
            'full_name': contribution['full_name'].upper(),
            'first_name' : parsed_name['first'],
            'middle_name' : parsed_name['middle'],
            'last_name' : parsed_name['last'],
            'city': contribution['city'].upper(),
            'state': contribution['state'].upper(),
            'zipcode': contribution['zipcode'].zfill(5),
            'employer': contribution['employer'].upper(),
            'occupation': contribution['occupation'].upper()
        }

    def _name_key(self, contribution_features):
        return contribution_features['last_name'].upper() + '|' + contribution_features['state'].upper()
