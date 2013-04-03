from fec.trainer import *
import cPickle as pickle
from sklearn.ensemble import RandomForestClassifier

class Tester(object):

    def __init__(self):
        self.test_training_file = 'data/training_matches_test.p'

    # Used to adjust learning parameters/thresholds
    def run_training_test(self):
        trainer = Trainer(self.test_training_file)
        trainer.generate_training_set(10000)

        match_file = open(self.test_training_file, 'rb')
        training_matches = pickle.load(match_file)
        match_file.close()

        clf = RandomForestClassifier(n_estimators=10, random_state=0)
        clf = clf.fit([eval(t.features) for t in training_matches], [int(t.matchpct) for t in training_matches])

        trainer = Trainer(self.test_training_file)
        trainer.group_by_last_name_and_state()

        CONFIDENCE_KEEP = 0.65
        CONFIDENCE_CHECK = 0.51

        num_pairs = 0
        num_true_matches = 0
        num_found_matches = 0
        num_correct = 0
        num_to_check = 0
        num_false_positives = 0
        num_missed = 0

        print 'Running test with KEEP=' + str(CONFIDENCE_KEEP) + ', initial_sim=' + str(trainer.initial_sim)
        for last_name_and_state, matches in trainer.groups.iteritems():
            last_name, state = last_name_and_state.split('|')
            if len(matches) < 2:
                continue
            #print last_name
            for c in itertools.combinations(matches, 2):
                is_true_match = c[0]['contributor_ext_id'] == c[1]['contributor_ext_id']
                if is_true_match:
                    num_true_matches += 1
                compstring1 = '%s %s' % (c[0]['first_name'], c[0]['city'])
                compstring2 = '%s %s' % (c[1]['first_name'], c[1]['city'])
                if trainer.jaccard_sim(trainer.shingle(compstring1.lower(), 2), trainer.shingle(compstring2.lower(), 2)) >= trainer.initial_sim:
                    num_pairs += 1
                    c1, c2 = c[0], c[1]
                    featurevector = str(trainer.create_featurevector(c1, c2))
                    edge = clf.predict_proba(eval(featurevector))
                    if edge[0][1] > CONFIDENCE_KEEP and is_true_match == True:
                        num_correct += 1
                        num_found_matches += 1
                    elif edge[0][1] > CONFIDENCE_KEEP:
                        #print '*'
                        #print c1
                        #print c2
                        num_false_positives += 1
                    elif edge[0][1] > CONFIDENCE_CHECK:
                        num_to_check += 1
                    elif is_true_match == True:
                        num_missed += 1
                    else:
                        num_correct += 1

        print '**'
        print 'true matches: ' + str(num_true_matches)
        print 'found matches: ' + str(num_found_matches)
        print 'matches to check: ' + str(num_to_check)
        print 'missed matches: ' + str(num_missed)
        print 'false positives: ' + str(num_false_positives)
        print 'pairs: ' + str(num_pairs)
        print 'correct pairs: ' + str(num_correct)
        print '*'
        print str(float(num_found_matches)/float(num_true_matches)*100.0)

    # Illustrates difference between bucketing by last_name and bucketing by last_name/state (1%)
    def run_bucket_test(self):
        trainer = Trainer(self.test_training_file)
        trainer.generate_training_set(10000)

        match_file = open(self.test_training_file, 'rb')
        training_matches = pickle.load(match_file)
        match_file.close()

        clf = RandomForestClassifier(n_estimators=10, random_state=0)
        clf = clf.fit([eval(t.features) for t in training_matches], [int(t.matchpct) for t in training_matches])

        trainer = Trainer(self.test_training_file)

        num_matches = 0
        num_lastname_matches = 0
        num_lastname_and_state_matches = 0
        num_neither_matches = 0

        rows = []
        human_names = {}

        for row in csv.reader(open(trainer.input_file), delimiter=',', quotechar='"'):
            row = dict(zip(trainer.input_file_fields, row))
            if row['contributor_gender'] == '':
                continue;
            row['last_name'] = HumanName(row['full_name']).last.upper()
            rows.append(row)

        cnt = 0
        for i in range(0, len(rows) - 1):
            print i
            for j in range(0, len(rows) - 1):
                if i == j:
                    continue
                if rows[i]['contributor_ext_id'] == rows[j]['contributor_ext_id']:
                    num_matches += 1
                    if rows[i]['last_name'] == rows[j]['last_name']:
                          num_lastname_matches += 1
                          if rows[i]['state'] == rows[j]['state']:
                                num_lastname_and_state_matches += 1
                    else:
                        num_neither_matches += 1
                        print '*'
                        print rows[i]
                        print rows[j]

        print num_matches
        print num_lastname_matches
        print num_lastname_and_state_matches
        print num_neither_matches

        print float(num_lastname_matches) / float(num_matches)
        print float(num_lastname_and_state_matches) / float(num_matches)