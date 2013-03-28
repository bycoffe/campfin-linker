# FEC Linker

A series of scripts that can be used to link donors within campaign finance data.

This project was originally modeled on Chase Davis' [fec-standardizer](https://github.com/cjdd3b/fec-standardizer).
Many of the ideas from that code are contained here; his [wiki](https://github.com/cjdd3b/fec-standardizer/wiki)
provides a great deal of background on the methods used within.

## Installation

    pip install -r requirements.txt

## Getting started

We suggest you follow these steps the first time you link a dataset. This guide will create the necessary mysql schema
for running a linkage, then download, import, and link some FEC individual contribution data for the 2014 election cycle.
After you've gone through the process once, it will be easier to link a different set of contributions.

Create a local database.yml and edit the connection properties to match your system:

    cp config/database.sample.yml config/database.yml

Create three tables (individuals, individual_contributions_2014, individual_possible_matches) for your linkage:

    python create.py

Download and import the first 30,000 individual contributions from the 2014 cycle:

    python seed.py

Create the training set needed to run a linkage:

    python train.py

Link the 2014 individual contribution data:

    python link.py

After the script finishes, the 30,000 contributions you imported are linked to canonical individuals. You'll see that the
*individual_contributions_2014* table has 30,000 records, while the *individuals* table has roughly 26,000. The difference in the
sizes of those tables represent multiple contributions by a person. Each contribution record is linked to a canonical
individual by the *canonical_id* field.

The *individual_possible_matches* table contains roughly 170 records, which represent the pairs that didn't satisfy the threshold
to be considered a match by the learning algorithm, but possibly are. These potential matches can be resolved with the resolve.py
script, or you could use another method to determine whether they're actually matches. They can also be ignored, which would result in
a slightly less precise linkage.

## Linking a second dataset

Linking a second dataset is easier than linking the first. The steps are:

1. Create a table with the new data
2. Add your new table to *linkable_tables* in *database.json*. You can override field names for the new table if it's convenient
3. Link the new dataset by specifying the new table name:

    python link.py --table=new_table

This second linkage shares the *individuals* table with the first linkage, so some individuals from the 2014 cycle may now be linked to
the dataset you just imported.

Note that rather than creating a new table, you could also just append new records to the same *individual_contributions_2014* table you used
for the example linkage and rerun the linkage, as long as you don't delete the existing data in the *canonical_id* field.

## Methodology

## Notes

Linking larger datasets can take a long time -- the set of 3.5 million 2012 contributions takes about 5 hours to link on a decent
computer. You can kill and restart the link.py script at any point without hurting anything. If necessary, it would be fairly easy to parallelize the
process so the script can be run on multiple machines, each of which pulls out (and locks) some records to link until there are no records
left.

## Authors

- Jay Boice, jay.boice@huffingtonpost.com
- Aaron Bycoffe, bycoffe@huffingtonpost.com

## Copyright

Copyright © 2013 The Huffington Post. See LICENSE for details.
