# Campaign Finance Linker

Campaign finance disclosure laws help us understand how money influences our political system, but inconsistencies in
the data make it hard to track individuals across contributions and through different elections. Campaign finance data
generally includes information about each contribution such as the contributor's name, address, occupation and employer,
but these individual contributors aren't uniquely identified. Misspelled names or changing job titles -- among other
inconsistencies -- make identifying individual donors a challenge.

This project contains a series of scripts that can be used to uniquely identify individual donors within campaign
finance data. It uses machine learning to link individuals within a single dataset or across multiple datasets. A linked
dataset from the [Center for Responsive Politics](http://www.opensecrets.org) is used as training data for a random
forest classifier. The classifier correctly identifies individuals about 96% of the time.

Your campaign finance data must be loaded into mysql to use these scripts. Since most data is released as delimited flat
files, it's fairly easy to load them into mysql for processing even if you aren't using it as your primary data store. Two
tables are maintained; an *individuals* table, which contains a record for each individual who has ever made a contribution,
and an *individual_partial_matches* table, which contains potential matches that fell below the threshold to be considered a certain
match. Any table containing campaign finance data that you feed into the system must contain an empty column that will be linked
to the *individuals* table.

This project was originally modeled on Chase Davis' [fec-standardizer](https://github.com/cjdd3b/fec-standardizer).
Many of the ideas from that code are contained here; his [wiki](https://github.com/cjdd3b/fec-standardizer/wiki)
provides a great background on the methods used within.

## Installation

    pip install -r requirements.txt

## Getting started

We suggest you follow these steps the first time you link a dataset. This guide will create the necessary mysql schema
for running a linkage, then download, import, and link some FEC individual contribution data for the 2014 election cycle.
After you've gone through the process once, it will be easier to link a different set of contributions.

Create a local database.yml and edit the connection properties to match your system:

    cp config/database.sample.yml config/database.yml

Create three tables (individuals, individual_partial_matches, individual_contributions_2014) for your linkage:

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
individual by the *individual_id* field.

The *individual_partial_matches* table contains roughly 170 records, which represent the pairs that didn't satisfy the threshold
to be considered a match by the learning algorithm, but possibly are. These potential matches can be resolved with the resolve.py
script, or you could use another method to determine whether they're actually matches. They can also be ignored, which would result in
a slightly less precise linkage.

## Linking a second dataset

Linking a second dataset is easier than linking the first. Note that you don't have to run train.py again -- this only has to be
done once. The steps are:

1. Create a table with the new data (make sureit contains an individual_id field to link to *individuals*)
2. Add your new table to *linkable_tables* in *database.yml*. You can override field names for the new table if convenient
3. Link the new dataset by specifying the new table name:

    python link.py --table=new_table

Since this second linkage shares the *individuals* table with the first linkage, some individuals from the 2014 cycle may now be linked to
the dataset you just imported.

Note that rather than creating a new table, you could also just append new records to the same *individual_contributions_2014* table you used
for the example linkage and rerun the linkage, as long as you don't delete the existing data in the *individual_id* field.

## Methodology

The process to link a single table is:

* Pull out 5,000 unlinked records from the table to be linked
* For each record, get all possible matches from the *individuals* table (people with the same last name, from the same state)
* Find the first matching individual record for the current contribution; if one doesn't exist, create it
* Link the contribution to the found (or newly created) individual

## Notes

Linked individuals must have the same values for last name and state. This reduces the number of records that must be compared
by a huge amount (making it possible to run this on millions of records), but according to our tests, sacrifices about 1% of accuracy.

Linking larger datasets can take a long time; the full set of 3.5 million 2012 contributions takes about 5 hours to link on a decent
computer. You can kill and restart the link.py script at any point without hurting anything. If necessary, it would be fairly easy to parallelize the
process so the script can be run on multiple machines, each of which pulls out (and locks) some records to link until there are no records
left.

As the *individuals* table grows, future linkages will take longer. You may wish to maintain multiple *individuals* tables for different projects
if you don't need records linked across projects. This can be accomplished by creating a new table and modifying database.yml to point to the
correct table.

The default chunk size (number of contribution records to process at one time) is 5,000, but can be tweaked by changing CHUNK_SIZE in db.py
if you'd like to do mysql I/O more or less often.

Records from the *individuals* table are cached in memory to reduce mysql queries. You can tweak the size of the cache by changing
MAX_CONTRIBUTOR_CACHE_SIZE in campfin/linker.py. It defaults to about 1Gb.

You can use test.py to evaluate the machine learning performance and tweak parameters if desired.

## Authors

- Jay Boice, jay.boice@huffingtonpost.com
- Aaron Bycoffe, bycoffe@huffingtonpost.com
- Chase Davis, chase.davis@gmail.com

## Copyright

Copyright © 2013 The Huffington Post. See LICENSE for details.
