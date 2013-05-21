from campfin.db import *

class Creator(object):

    def __init__(self):
        self.db = DB()

    def create(self):
        print "Creating tables"
        self.db.execute("individuals", """
            CREATE TABLE IF NOT EXISTS `individuals` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `full_name` varchar(255) DEFAULT NULL,
              `first_name` varchar(255) DEFAULT NULL,
              `middle_name` varchar(255) DEFAULT NULL,
              `last_name` varchar(255) DEFAULT NULL,
              `city` varchar(255) DEFAULT NULL,
              `state` varchar(255) DEFAULT NULL,
              `zipcode` varchar(255) DEFAULT NULL,
              `employer` varchar(255) DEFAULT NULL,
              `occupation` varchar(255) DEFAULT NULL,
              PRIMARY KEY (`id`),
              KEY `index_individuals_on_last_name` (`last_name`)
            )
        """)

        self.db.execute("partial_matches", """
            CREATE TABLE IF NOT EXISTS `individual_partial_matches` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `individual_id` int(11) DEFAULT NULL,
              `object_table` varchar(255) DEFAULT NULL,
              `object_id` int(11) DEFAULT NULL,
              `confidence` float DEFAULT NULL,
              `resolved` tinyint(1) DEFAULT '0',
              PRIMARY KEY (`id`),
              KEY `index_individual_partial_matches_on_individual_id` (`individual_id`),
              KEY `index_individual_partial_matches_on_object_table` (`object_table`),
              KEY `index_individual_partial_matches_on_object_id` (`object_id`),
              KEY `index_individual_partial_matches_on_resolved` (`resolved`)
            )
        """)

        self.db.execute("linker", """
            CREATE TABLE IF NOT EXISTS `individual_contributions_2014` (
              `id` int(11) NOT NULL AUTO_INCREMENT,
              `committee_id` varchar(255) DEFAULT NULL,
              `amendment` varchar(255) DEFAULT NULL,
              `report_type` varchar(255) DEFAULT NULL,
              `pgi` varchar(255) DEFAULT NULL,
              `image_num` varchar(255) DEFAULT NULL,
              `transaction_type` varchar(255) DEFAULT NULL,
              `entity_type` varchar(255) DEFAULT NULL,
              `contributor_name` varchar(255) DEFAULT NULL,
              `city` varchar(255) DEFAULT NULL,
              `state` varchar(255) DEFAULT NULL,
              `zipcode` varchar(255) DEFAULT NULL,
              `employer` varchar(255) DEFAULT NULL,
              `occupation` varchar(255) DEFAULT NULL,
              `transaction_date` varchar(255) DEFAULT NULL,
              `amount` float DEFAULT NULL,
              `other_id` varchar(255) DEFAULT NULL,
              `transaction_id` varchar(255) DEFAULT NULL,
              `filing_number` varchar(255) DEFAULT NULL,
              `memo_code` varchar(255) DEFAULT NULL,
              `memo_text` varchar(255) DEFAULT NULL,
              `sub_id` varchar(255) DEFAULT NULL,
              `individual_id` int(11) DEFAULT NULL,
              PRIMARY KEY (`id`),
              KEY `index_individual_contributions_on_individual_id` (`individual_id`)
            )
        """)
