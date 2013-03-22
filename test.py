import os
from fec.trainer import *
import cPickle as pickle
from sklearn.ensemble import RandomForestClassifier

if not os.path.isfile("data/crp_slice.csv"):
    os.system("unzip data/crp_slice.zip -d data")

trainer = Trainer()
trainer.generate_training_set(10000)

match_file = open('data/training_matches.p', 'rb')
training_matches = pickle.load(match_file)
match_file.close()

clf = RandomForestClassifier(n_estimators=10, random_state=0)
clf = clf.fit([eval(t.features) for t in training_matches], [int(t.matchpct) for t in training_matches])

trainer = Trainer()
trainer.group_by_last_name()

CONFIDENCE_KEEP = 0.89
CONFIDENCE_CHECK = 0.51

num_pairs = 0
num_correct = 0
num_to_check = 0
num_false_positives = 0
num_missed = 0
num_missed_for_state = 0

for last_name, matches in trainer.last_name_groups.iteritems():
    if len(matches) < 2:
        continue
    print last_name
    for c in itertools.combinations(matches, 2):
        is_true_match = c[0]['contributor_ext_id'] == c[1]['contributor_ext_id']
        if c[0]['state'] == c[1]['state']:
            compstring1 = '%s %s %s' % (c[0]['first_name'], c[0]['city'], c[0]['state'])
            compstring2 = '%s %s %s' % (c[1]['first_name'], c[1]['city'], c[1]['state'])
            if trainer.jaccard_sim(trainer.shingle(compstring1.lower(), 2), trainer.shingle(compstring2.lower(), 2)) >= trainer.initial_sim:
                num_pairs += 1
                c1, c2 = c[0], c[1]
                featurevector = str(trainer.create_featurevector(c1, c2))
                edge = clf.predict_proba(eval(featurevector))
                if edge[0][1] > CONFIDENCE_KEEP and is_true_match == True:
                    num_correct += 1
                elif edge[0][1] > CONFIDENCE_KEEP:
                    num_false_positives += 1
                elif edge[0][1] > CONFIDENCE_CHECK:
                    num_to_check += 1
                elif is_true_match == True:
                    num_missed += 1
                else:
                    num_correct += 1
        elif is_true_match:
            print '***'
            print c[0]
            print c[1]
            num_missed_for_state += 1

print '**'
print 'pairs: ' + str(num_pairs)
print 'correct: ' + str(num_correct)
print 'to check: ' + str(num_to_check)
print 'false positives: ' + str(num_false_positives)
print 'missed: ' + str(num_missed)
print 'missed (state): ' + str(num_missed_for_state)
print '*'
print str(float(num_correct)/float(num_pairs)*100.0)
