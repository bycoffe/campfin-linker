# FEC Linker

A series of scripts that can be used to link donors within campaign finance data.

This project was originally modeled on Chase Davis' [fec-standardizer](https://github.com/cjdd3b/fec-standardizer).
Many of the ideas from that code are contained here; his [wiki](https://github.com/cjdd3b/fec-standardizer/wiki)
provides a great deal of background on the methods used within.

## Installation

    pip install MySQL-python==1.2.4 nameparser==0.2.7 numpy==1.7.0 scipy==0.11.0 scikit-learn==0.13.1 simplejson==3.1.2

## Getting started

We suggest you follow these steps the first time you link a dataset. This guide will create the necessary mysql schema
for running a linkage, then download, import, and link FEC individual contribution data for the 2014 election cycle.
After you've gone through the process once, it will be easier to link a different set of contributions.

1. Create a database and three tables for your linkage:

    mysql -u root fec < data/create.sql

2. Create a local database.json and edit the fec connection properties to match your system:

    cp config/database.sample.json config/database.json

3. Download and import 2014 individual contributions to be linked:

    curl -s ftp://ftp.fec.gov/FEC/2014/indiv14.zip > data/indiv14.zip
    unzip data/indiv14.zip -d data
    mysql -u root fec -e "LOAD DATA LOCAL INFILE 'data/itcont.txt' INTO TABLE individual_contributions FIELDS TERMINATED BY '|'"

4. Create the training set needed to run all linkages:

    python train.py

5. Link the 2014 individual contribution data:

    python link.py

## Authors

- Jay Boice, jay.boice@huffingtonpost.com
- Aaron Bycoffe, bycoffe@huffingtonpost.com

## Copyright

Copyright © 2013 The Huffington Post. See LICENSE for details.