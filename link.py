import os
from datetime import datetime
import itertools
import cPickle as pickle
from sklearn.ensemble import RandomForestClassifier
from fec.db import *
from fec.match import Match
from fec.preprocessor import *

CHUNK_SIZE = 5000
CONFIDENCE_KEEP = 0.89
CONFIDENCE_CHECK = 0.51

def train_classifier(training_matches):
    print "Training classifier"
    c = RandomForestClassifier(n_estimators=10, random_state=0)
    c = c.fit([eval(t.features) for t in training_matches], [int(t.matchpct) for t in training_matches])
    return c

def load_training_matches():
    print "Loading training matches"
    match_file = open('data/training_matches.p', 'rb')
    tm = pickle.load(match_file)
    match_file.close()
    return tm

def fill_empty_last_names():
    print "Setting empty last names in individual_contributions"
    while num_unfilled_last_names() > 0:
        print '  ' + str(num_unfilled_last_names()) + ' remaining...'
        dbc.execute("update individual_contributions set contributor_last_name = substring_index(contributor_name,',',1) where contributor_last_name is null limit 100000")
        db.commit()

def num_unfilled_last_names():
    dbc.execute("select count(*) as cnt from individual_contributions where contributor_last_name is null")
    return dbc.fetchone()['cnt']

def next_contributor_id():
    dbc.execute("select max(id) as maxid from contributors")
    maxid = dbc.fetchone()['maxid']
    if maxid == None:
        maxid = 0
    return maxid + 1

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

def create_contributors(contributors):
    if len(contributors) > 0:
        dbc.executemany(
        """insert into contributors (id, full_name, first_name, middle_name, last_name, city, state, zipcode, employer, occupation)
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        ((c['id'], c['full_name'], c['first_name'], c['middle_name'], c['last_name'], c['city'], c['state'], c['zipcode'], c['employer'], c['occupation']) for c in contributors)
        )
        db.commit()

def save_contributions(contributions):
    for c in contributions:
        dbc.execute("update individual_contributions set contributor_id = %s where id = %s", (c['contributor_id'], c['id']))
    db.commit()

def create_new_possible_matches(new_possible_matches):
    if len(new_possible_matches) > 0:
        dbc.executemany(
        """insert into contributor_matches (individual_contribution_id, contributor_id, confidence)
        values (%s, %s, %s)""",
        ((m['individual_contribution_id'], m['contributor_id'], m['confidence']) for m in new_possible_matches)
        )
        db.commit()

# Find the first matching contributor in a list
def first_matching_contributor_id(contribution, contributors, new_possible_matches):
    possible_matches_to_add = []
    for c in contributors:
        c1f, c2f = contribution_features(contribution), c
        compstring1 = '%s %s %s' % (c1f['first_name'], c1f['city'], c1f['state'])
        compstring2 = '%s %s %s' % (c2f['first_name'], c2f['city'], c2f['state'])
        if preprocessor._jaccard_sim(preprocessor._shingle(compstring1.lower(), 2), preprocessor._shingle(compstring2.lower(), 2)) < preprocessor.initial_sim:
            continue
        featurevector = str(create_featurevector(c1f, c2f))
        edge = clf.predict_proba(eval(featurevector))
        if edge[0][1] > CONFIDENCE_KEEP:
            return c['id']
        elif edge[0][1] > CONFIDENCE_CHECK:
            possible_matches_to_add.append({'individual_contribution_id': contribution['id'], 'contributor_id': c['id'], 'confidence': edge[0][1]})
    new_possible_matches.extend(possible_matches_to_add)
    return None

def match_contributions():
    max_contributor_id = next_contributor_id()
    ts_start = datetime.now()
    while True:

        # Get the next batch of contributions to process
        dbc.execute("select id, contributor_name, city, state, zipcode, employer, occupation, contributor_last_name, contributor_id from individual_contributions where contributor_id is null limit %s", CHUNK_SIZE)
        unlinked_contributions = dbc.fetchall()
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
            dbc.execute("select * from contributors where last_name = %s and state = %s order by id", (uc['contributor_last_name'], uc['state']))
            contributors = dbc.fetchall()

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

        create_contributors(new_contributors)
        save_contributions(unlinked_contributions)
        create_new_possible_matches(new_possible_matches)

        print "Processed " + str(cnt) + " contributions in " + str(datetime.now() - ts_start)
        ts_start = datetime.now()

fill_empty_last_names()
clf = train_classifier(load_training_matches())
preprocessor = Preprocessor()
contribution_names = {}
match_contributions()

#import cProfile
#import pstats
#cProfile.run('match_contributions()', 'prof')
#p = pstats.Stats('prof')
#p.sort_stats('cumulative').print_stats(50)