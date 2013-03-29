import os
import subprocess

from fec.db import *


class Seeder(object):

    def __init__(self):
        self.path = os.path.join(os.getcwd(), 'data')
        self.db = DB()

    def seed(self):
        filepath = self.download_fec_file()
        self.unzip_fec_file(filepath)
        filepath = self.head_fec_file()
        self.load_fec_data(filepath)

    def download_fec_file(self):
        print "Downloading individual contributions file from the FEC"
        filepath = os.path.join(self.path, 'indiv04.zip')
        fh = open(filepath, 'wb')
        with open(filepath, 'wb') as fh:
            subprocess.call(["curl", "-s", "ftp://ftp.fec.gov/FEC/2004/indiv04.zip"], stdout=fh)
        return filepath

    def unzip_fec_file(self, filepath):
        print "Unzipping FEC file"
        subprocess.call(["unzip", filepath, "-d", self.path])

    def head_fec_file(self, lines=30000):
        print "Extracting first %s rows of FEC file" % lines
        filepath = os.path.join(self.path, 'itcont2.txt')
        os.system("grep '|NY|' data/itcont.txt > data/itcont2.txt")
        #with open(filepath, 'w') as fh:
        #    subprocess.call(["grep", "'|NY|'", os.path.join(self.path, 'itcont.txt')], stdout=fh)
        return filepath

    def load_fec_data(self, filepath):
        print "Loading FEC data"
        self.db.execute("linker", """
            LOAD DATA INFILE %s INTO TABLE individual_contributions_2004_ny FIELDS TERMINATED BY '|' (committee_id,amendment,report_type,pgi,image_num,transaction_type,entity_type,contributor_name,city,state,zipcode,employer,occupation,transaction_date,amount,other_id,transaction_id,filing_number,memo_code,memo_text,sub_id)
        """, args=[filepath,])
