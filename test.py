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
