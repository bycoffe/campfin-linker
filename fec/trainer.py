import csv
import itertools
from collections import defaultdict
import cPickle as pickle
import sys
from match import Match
from nameparser import HumanName
from sklearn.ensemble import RandomForestClassifier

class Trainer(object):

    def __init__(self):
        self.initial_sim = 0.1
        self.fields = ["id", "import_reference_id", "cycle", "transaction_namespace", "transaction_id", "transaction_type", "filing_id", "is_amendment", "amount", "date", "full_name", "contributor_ext_id", "contributor_type", "occupation", "employer", "contributor_gender", "contributor_address", "city", "state", "zipcode", "contributor_category", "organization_name", "organization_ext_id", "parent_organization_name", "parent_organization_ext_id", "recipient_name", "recipient_ext_id", "recipient_party", "recipient_type", "recipient_state", "recipient_state_held", "recipient_category", "committee_name", "committee_ext_id", "committee_party", "candidacy_status", "district", "district_held", "seat", "seat_held", "seat_status", "seat_result"]
        self.last_name_groups = defaultdict(list)
        self.training_set_size = 1000000
        self.input_file = "data/crp_slice.csv"
        self.output_file = 'data/training_matches.p'

    def generate_training_set(self, training_set_size=None):
        if training_set_size != None:
            self.training_set_size = training_set_size
        self.group_by_last_name()
        to_create = []
        for last_name, matches in self.last_name_groups.iteritems():
            if len(matches) < 2 or last_name.count(' ') > 0:
                continue
            print last_name
            for c in itertools.combinations(matches, 2):
                compstring1 = '%s %s %s' % (c[0]['first_name'], c[0]['city'], c[0]['state'])
                compstring2 = '%s %s %s' % (c[1]['first_name'], c[1]['city'], c[1]['state'])
                if self.jaccard_sim(self.shingle(compstring1.lower(), 2), self.shingle(compstring2.lower(), 2)) >= self.initial_sim:
                    c1, c2 = c[0], c[1]
                    featurevector = str(self.create_featurevector(c1, c2))
                    match = Match(c1, c2, featurevector)
                    to_create.append(match)
        pickle.dump(to_create, open(self.output_file, 'w'))

    def train(self):
        print "Training classifier"
        c = RandomForestClassifier(n_estimators=10, random_state=0)
        training_matches = self.load_training_matches()
        c = c.fit([eval(t.features) for t in training_matches], [int(t.matchpct) for t in training_matches])
        return c

    def load_training_matches(self):
        print "Loading training matches"
        match_file = open(self.output_file, 'rb')
        tm = pickle.load(match_file)
        match_file.close()
        return tm

    def jaccard_sim(self, X, Y):
        '''
        Jaccard similarity between two sets.

        Explanation here: http://en.wikipedia.org/wiki/Jaccard_index
        '''
        if not X or not Y: return 0
        x = set(X)
        y = set(Y)
        return float(len(x & y)) / len(x | y)

    def shingle(self, word, n):
        '''
        Not using a generator here, unlike the initial implementation,
        both because it doesn't save a ton of memory in this use case
        and because it was borking the creation of minhashes.

        More on shingling here: http://blog.mafr.de/2011/01/06/near-duplicate-detection/
        '''
        return set([word[i:i + n] for i in range(len(word) - n + 1)])

    def group_by_last_name(self):
        n=0
        for row in csv.reader(open(self.input_file), delimiter=',', quotechar='"'):
            n += 1
            row = dict(zip(self.fields, row))
            row['full_name'] = row['full_name'].upper()
            row['city'] = row['city'].upper()
            row['state'] = row['state'].upper()
            row['occupation'] = row['occupation'].upper()
            row['employer'] = row['employer'].upper()
            parsed_name = HumanName(row['full_name'])
            row['first_name'] = parsed_name.first
            row['last_name'] = parsed_name.last
            if len(row['last_name']) > 0:
                self.last_name_groups[row['last_name']].append(row)
            if n >= self.training_set_size:
                break

    def clean_str(self, val):
        '''
        Helper function to lowercase and strip input string.
        '''
        if not val: return ' '
        return val.lower().strip()

    def same(self, key, c1, c2):
        match = 0
        if self.clean_str(c1[key]) == self.clean_str(c2[key]):
            match = 1
        return match

    def similarity(self, key, c1, c2):
        if key == 'zipcode':
            counter = 0.0
            z1, z2 = [self.clean_str(x) for x in [c1['zipcode'], c2['zipcode']]]
            if len(z1) < 5 or len(z2) < 5:
                return counter
            for i in range(5):
                if z1[i] == z2[i]:
                    counter += 1
                else:
                    break
                i += 1
            return counter / 5.0

        elif key == 'zipcode_region':
            if self.clean_str(c1['zipcode'])[0] == self.clean_str(c2['zipcode'])[0]:
                return 1
            return 0

        elif key == 'zipcode_sectionalcenter':
            if self.clean_str(c1['zipcode'])[:3] == self.clean_str(c2['zipcode'])[:3]:
                return 1
            return 0

        else:
            c1_shingles = self.shingle(self.clean_str(c1[key]), 3)
            c2_shingles = self.shingle(self.clean_str(c2[key]), 3)
            return self.jaccard_sim(c1_shingles, c2_shingles)

    def create_featurevector(self, c1, c2):
        features = []

        # Features to look for exact matches
        same_keys = ['last_name', 'first_name', 'city', 'state', 'zipcode', ]
        for key in same_keys:
            features.append(self.same(key, c1, c2))

        # Features to look for similarities
        sim_keys = ['zipcode', 'first_name', 'occupation', 'employer', 'full_name', 'zipcode_region', 'zipcode_sectionalcenter', ]
        for key in sim_keys:
            features.append(self.similarity(key, c1, c2))
        return features
