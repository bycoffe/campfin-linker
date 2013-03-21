class Match(object):

    def __init__(self, c1, c2, features):
        self.c1 = c1
        self.c2 = c2
        self.features = features
        if 'contributor_ext_id' in c1:
            self.matchpct = 1 if c1['contributor_ext_id'] == c2['contributor_ext_id'] else 0

    def __str__(self):
        return str(self.c1) + str(self.c2) + str(self.features) + str(self.matchpct)