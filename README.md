     _   _,              |\ o          |\ o       |)   _  ,_
    /   / |  /|/|/|  |/\_|/ | /|/|     |/ | /|/|  |/) |/ /  |
    \__/\/|_/ | | |_/|_/ |_/|/ | |_/   |_/|/ | |_/| \/|_/   |/
                    (|   |)
# Campaign Finance Linker

Campaign finance disclosure laws help us understand how money influences our political system, but inconsistencies in
the data make it hard to get a full picture of where the money comes from. This library uses machine learning -- specifically, a [random forest classifier](http://en.wikipedia.org/wiki/Random_forest) -- to group records by the individual who made the contribution.

## How it works

Campaign finance records generally include a contributor's name, address, occupation and employer,
but not a unique identifier for the individual. Inconsistencies like misspelled names or changing job titles make it difficult to connect records by donor.

This library can link contributions within a single dataset or across multiple datasets. It could, for example,
match individual contribution records from the 2012 presidential election, connect records across multiple years of federal election data,
or find connections between contributions to candidates in a local election and contributions to candidates who ran for president.

To train the classifier, we use an already-linked dataset (`data/crp_slice.zip`) from the [Center for Responsive Politics](http://www.opensecrets.org).

This project was inspired by Chase Davis' [fec-standardizer](https://github.com/cjdd3b/fec-standardizer).
See his [wiki](https://github.com/cjdd3b/fec-standardizer/wiki) for background.

## Installation

	pip install -r requirements.txt

## Getting started

Follow these steps to create the necessary MySQL schema and to download, import, and link individual contribution data for the 2014 election cycle from the Federal Election Commision.

1) Create a `database.yml` and edit the connection properties to match your system:

    cp config/database.sample.yml config/database.yml

2) Create three tables (`individuals`, `individual_partial_matches`, `individual_contributions_2014`) for your linkage:

    python create.py

3) Download and import the first 20,000 individual contributions from the 2014 cycle:

    python seed.py

4) Generate a training set from the linked CRP data:

    python generate.py

5) Train the classifier and link the 2014 individual contribution data:

    python link.py

The 20,000 contributions (`individual_contributions_2014`) are now linked to about 18,000 canonical individuals (`individuals`). The 2,000 record difference is the result of multiple contributions being linked to a single individual. Each contribution record is linked to a canonical individual by the `individual_id` field.

The `individual_partial_matches` table contains roughly 30 records, which represent the pairs that didn't satisfy the threshold to be considered a match by the learning algorithm, but possibly are. You can resolve these potential matches with the `resolve.py` script, or you could use another method to determine whether they're actually matches. They can also be ignored, which results in
a slightly less precise linkage.

## Linking a second dataset

Linking a second dataset is easier than linking the first. (The training set only needs to be generated once, so you don't have to run `generate.py` again.) The steps are:

1) Create a table with the new data (make sure it contains an empty `individual_id` field to link to `individuals`)

2) Add your new table to `linkable_tables` in `database.yml`. (You can override field names for the new table if needed.)

3) Link the new dataset by specifying the new table name:

    python link.py --table=new_table

Since this second linkage shares the `individuals` table with the first linkage, some individuals from the 2014 cycle may now be linked to
the dataset you just imported.

Instead of creating a new table, you could also just append new records to the same `individual_contributions_2014` table you used for the example linkage and rerun the linkage, as long as you don't delete the existing data in the `individual_id` field.

## Notes

For performance reasons, the linker only compares records that have the same values for last name and state.

Linking larger datasets can take a long time; the full set of 3.5 million 2012 contributions took about 5 hours to link on a 2 GHz MacBook Pro. You can kill and restart the `link.py` script at any time. (It would be fairly easy to parallelize the process so the script can be run on multiple machines, each of which pulls out &mdash; and locks &mdash; some records to link until there are no records
left).

As the `individuals` table grows, future linkages will take longer. If you don't need records linked across projects, you can use a different `individuals` tables for each one by creating a new table and modifying database.yml to point to the
correct table.

Records from the `individuals` table are cached in memory to reduce MySQL queries. Depending on how much RAM you have available, you can tweak the size of the cache by changing `MAX_CONTRIBUTOR_CACHE_SIZE` in `campfin/linker.py`. (Default is about 1 GB).

Use `test.py` to evaluate the machine learning performance and tweak some parameters

## Authors

- Jay Boice, jay.boice@huffingtonpost.com
- Aaron Bycoffe, bycoffe@huffingtonpost.com

## Copyright

Copyright &copy; 2013 The Huffington Post. See LICENSE for details.
