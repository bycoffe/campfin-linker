import os
from datetime import datetime
import itertools
import cPickle as pickle
from sklearn.ensemble import RandomForestClassifier
from fec.db import *
from fec.match import Match
from fec.trainer import *

CONFIDENCE_KEEP = 0.89
CONFIDENCE_CHECK = 0.51

def contribution_features(contribution):
    if contribution['id'] in contribution_names:
        parsed_name = contribution_names[contribution['id']]
    else:
        human_name = HumanName(contribution['contributor_name'])
        parsed_name = {'first': human_name.first, 'middle': human_name.middle, 'last': human_name.last}
        contribution_names[contribution['id']] = parsed_name
    return {
        'full_name': contribution['contributor_name'],
        'first_name' : parsed_name['first'],
        'middle_name' : parsed_name['middle'],
        'last_name' : parsed_name['last'],
        'city': contribution['city'],
        'state': contribution['state'],
        'zipcode': contribution['zipcode'],
        'employer': contribution['employer'],
        'occupation': contribution['occupation']
    }

def name_key(contribution):
    return contribution['contributor_name'] + '|' + contribution['state']

# Find the first matching contributor in a list
def first_matching_contributor_id(contribution, contributors, new_possible_matches):
    possible_matches_to_add = []
    for c in contributors:
        c1f, c2f = contribution_features(contribution), c
        compstring1 = '%s %s %s' % (c1f['first_name'], c1f['city'], c1f['state'])
        compstring2 = '%s %s %s' % (c2f['first_name'], c2f['city'], c2f['state'])
        if trainer.jaccard_sim(trainer.shingle(compstring1.lower(), 2), trainer.shingle(compstring2.lower(), 2)) < trainer.initial_sim:
            continue
        featurevector = str(trainer.create_featurevector(c1f, c2f))
        edge = clf.predict_proba(eval(featurevector))
        if edge[0][1] > CONFIDENCE_KEEP:
            return c['id']
        elif edge[0][1] > CONFIDENCE_CHECK:
            possible_matches_to_add.append({'individual_contribution_id': contribution['id'], 'contributor_id': c['id'], 'confidence': edge[0][1]})
    new_possible_matches.extend(possible_matches_to_add)
    return None

def match_contributions():
    max_contributor_id = db.next_contributor_id()
    ts_start = datetime.now()
    while True:

        # Get the next batch of contributions to process
        unlinked_contributions = db.next_unlinked_contributions()
        if len(unlinked_contributions) == 0:
            break

        new_contributors = []
        used_name_keys = {}
        contribution_names = {}
        new_possible_matches = []
        cnt = 0
        for uc in unlinked_contributions:

            # Don't process the same last_name|state twice in this round because the match could be in new_contributors and uncommitted
            if name_key(uc) in used_name_keys:
                continue
            used_name_keys[name_key(uc)] = True
            cnt += 1

            # Get potential contributors for this contribution
            contributors = db.potential_contributors(uc)

            # Find match in contributors
            contributor_id = first_matching_contributor_id(uc, contributors, new_possible_matches)

            # If no contributor was found, create a new one
            if contributor_id == None:
                contributor = contribution_features(uc)
                contributor['id'] = max_contributor_id
                max_contributor_id += 1
                new_contributors.append(contributor)
                contributor_id = contributor['id']

            # Link the contribution
            uc['contributor_id'] = contributor_id

        db.create_contributors(new_contributors)
        db.save_contributions(unlinked_contributions)
        db.create_new_possible_matches(new_possible_matches)

        print "Processed " + str(cnt) + " contributions in " + str(datetime.now() - ts_start)
        ts_start = datetime.now()

db = DB()
db.fill_empty_last_names()
trainer = Trainer()
clf = trainer.train()
contribution_names = {}
match_contributions()

#import cProfile
#import pstats
#cProfile.run('match_contributions()', 'prof')
#p = pstats.Stats('prof')
#p.sort_stats('cumulative').print_stats(50)