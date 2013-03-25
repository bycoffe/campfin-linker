# FEC Linker

A series of scripts that can be used to link donors within campaign finance data.

This project was originally modeled on Chase Davis' [fec-standardizer](https://github.com/cjdd3b/fec-standardizer).
Many of the ideas from that code are contained here; his [wiki](https://github.com/cjdd3b/fec-standardizer/wiki)
provides a great deal of background on the methods used within.

## Installation

    pip install MySQL-python==1.2.4 nameparser==0.2.7 numpy==1.7.0 scipy==0.11.0 scikit-learn==0.13.1 simplejson==3.1.2

## Getting started

We suggest you follow these steps the first time you link a dataset. This guide will create the necessary mysql schema
for running a linkage, then download, import, and link FEC some individual contribution data for the 2014 election cycle.
After you've gone through the process once, it will be easier to link a different set of contributions.

Create a database and three tables (individuals, individual_contributions, individual_possible_matches) for your linkage:

    mysqladmin -u root create fec
    mysql -u root fec < data/create.sql

Create a local database.json and edit the fec connection properties to match your system:

    cp config/database.sample.json config/database.json

Download and import the first 30,000 individual contributions from the 2014 cycle:

    curl -s ftp://ftp.fec.gov/FEC/2014/indiv14.zip > data/indiv14.zip
    unzip data/indiv14.zip -d data
    head -30000 data/itcont.txt > data/itcont2.txt
    mysql -u root fec -e "LOAD DATA LOCAL INFILE 'data/itcont2.txt' INTO TABLE individual_contributions FIELDS TERMINATED BY '|' (committee_id,amendment,report_type,pgi,image_num,transaction_type,entity_type,contributor_name,ccc,state,zipcode,employer,occupation,transaction_date,amount,other_id,transaction_id,filing_number,memo_code,memo_text,sub_id,contributor_last_name,contributor_id)"

Create the training set needed to run a linkage:

    python train.py

Link the 2014 individual contribution data:

    python link.py

After the script finishes, the 30,000 contributions you imported are linked to canonical individuals. You'll see that the
*individual_contributions* table has 30,000 records, while the *individuals* table has roughly 26,000. The difference in the
sizes of those tables represent multiple contributions by a person. Each contribution record is linked to a canonical
individual by the *canonical_id* field.

The *individual_possible_matches* table contains roughly 170 records, which represent the pairs that didn't satisfy the threshold
to be considered a match by the learning algorithm, but possibly are. These possible matches can be resolved with the resolve.py
script, or you could use another method to determine whether they're actually matches. They can also be ignored, which would result in
a slightly less precise linkage.

## Linking a second dataset

Linking a second dataset is easier than linking the first. The steps are:

1. Create a table with the new data
2. Add your new table to *linkable_tables* in *database.json*. You can override field names for the new table if it's convenient
3. Link the new dataset by specifying the new table name:

    python link.py --table=new_table

This second linkage shares the *individuals* table with the first linkage, so some records from the 2014 cycle may be linked to
the dataset you just imported.

Note that rather than creating a new table, you could also just append new records to the same *individual_contributions* table you used
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