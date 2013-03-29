from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from fec.db import *
from fec.trainer import *

CONFIDENCE_KEEP = 0.65
CONFIDENCE_CHECK = 0.51

class Linker(object):

    def __init__(self, dbname, table):
        self.db = DB(dbname, table)
        self.table = self.db.tablename
        self.trainer = Trainer()
        self.contribution_names = {}

    def link(self):
        print "Linking contributions in " + self.db.db['database'] + ":" + self.table
        self.clf = self.trainer.train()
        max_contributor_id = self.db.next_contributor_id()
        all_contributors = {}
        while True:
            ts_start = datetime.now()

            # Get the next batch of contributions to process
            unlinked_contributions = self.db.next_unlinked_contributions()
            if len(unlinked_contributions) == 0:
                break

            self.contribution_names = {}
            new_contributors = []
            used_name_keys = {}
            new_possible_matches = []
            cnt = 0
            for uc in unlinked_contributions:
                uc_features = self._contribution_features(uc)

                # Don't process the same last_name|state twice in this round because the match could be in new_contributors and uncommitted
                if self._name_key(uc_features) in used_name_keys:
                    continue
                used_name_keys[self._name_key(uc_features)] = True
                cnt += 1

                # Get potential contributors for this contribution
                if self._name_key(uc_features) in all_contributors:
                    contributors = all_contributors[self._name_key(uc_features)]
                else:
                    contributors = self.db.potential_contributors(uc_features)
                    all_contributors[self._name_key(uc_features)] = list(contributors)

                # Find match in contributors
                contributor_id = self._first_matching_contributor_id(uc_features, contributors, new_possible_matches)

                # If no contributor was found, create a new one
                if contributor_id == None:
                    contributor = uc_features
                    contributor['id'] = max_contributor_id
                    max_contributor_id += 1
                    new_contributors.append(contributor)
                    all_contributors[self._name_key(uc_features)].append(contributor)
                    contributor_id = contributor['id']

                # Link the contribution
                uc['canonical_id'] = contributor_id

            self.db.create_contributors(new_contributors)
            self.db.save_contributions(unlinked_contributions)
            self.db.create_new_possible_matches(new_possible_matches)

            print "Processed " + str(cnt) + " contributions in " + str(datetime.now() - ts_start)


    # Find the first matching contributor in a list
    def _first_matching_contributor_id(self, contribution_features, contributors, new_possible_matches):
        possible_matches_to_add = []
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
                possible_matches_to_add.append({'object_id': contribution_features['id'], 'canonical_id': c['id'], 'confidence': edge[0][1]})
        new_possible_matches.extend(possible_matches_to_add)
        return None

    def _contribution_features(self, contribution):
        if contribution['id'] in self.contribution_names:
            parsed_name = self.contribution_names[contribution['id']]
        else:
            human_name = HumanName(contribution['full_name'].upper())
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
            'zipcode': contribution['zipcode'],
            'employer': contribution['employer'].upper(),
            'occupation': contribution['occupation'].upper()
        }

    def _name_key(self, contribution_features):
        return contribution_features['last_name'].upper() + '|' + contribution_features['state'].upper()
