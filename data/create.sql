CREATE TABLE `individual_contributions` (
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
  `sub_id` int(11) DEFAULT NULL,
  `contributor_last_name` varchar(255) DEFAULT NULL,
  `contributor_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `index_individual_contributions_on_contributor_id` (`contributor_id`),
  KEY `index_individual_contributions_on_contributor_last_name` (`contributor_last_name`)
)

CREATE TABLE `contributors` (
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
  KEY `index_contributors_on_last_name` (`last_name`)
)

CREATE TABLE `contributor_matches` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `individual_contribution_id` int(11) DEFAULT NULL,
  `contributor_id` varchar(255) DEFAULT NULL,
  `confidence` float DEFAULT NULL,
  `resolved` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `index_contributor_matches_on_individual_contribution_id` (`individual_contribution_id`),
  KEY `index_contributor_matches_on_contributor_id` (`contributor_id`),
  KEY `index_contributor_matches_on_resolved` (`resolved`)
)
