DROP TABLE IF EXISTS `downloads`;
DROP TABLE IF EXISTS `ttylog`;
DROP TABLE IF EXISTS `sessions`;
DROP TABLE IF EXISTS `sensors`;
DROP TABLE IF EXISTS `input`;
DROP TABLE IF EXISTS `clients`;
DROP TABLE IF EXISTS `auth`;

CREATE TABLE `auth` (
  `id` int(11) NOT NULL auto_increment,
  `session` char(32) NOT NULL,
  `success` tinyint(1) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(100) NOT NULL,
  `timestamp` datetime NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `session` (`session`)
) ;

CREATE TABLE `clients` (
  `id` int(4) NOT NULL auto_increment,
  `version` varchar(50) NOT NULL,
  PRIMARY KEY  (`id`)
) ;

CREATE TABLE `input` (
  `id` int(11) NOT NULL auto_increment,
  `session` char(32) NOT NULL REFERENCES sessions(id),
  `timestamp` datetime NOT NULL,
  `realm` varchar(50) default NULL,
  `success` tinyint(1) default NULL,
  `input` text NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `session` (`session`,`timestamp`,`realm`)
) ;

CREATE TABLE `sensors` (
  `id` int(11) NOT NULL auto_increment,
  `ip` varchar(15) NOT NULL,
  PRIMARY KEY  (`id`)
) ;

CREATE TABLE `sessions` (
  `ord_id` int(11) NOT NULL auto_increment,
  `id` char(32) NOT NULL,
  `starttime` datetime NOT NULL,
  `endtime` datetime default NULL,
  `sensor` int(4) NOT NULL,
  `ip` varchar(15) NOT NULL default '',
  `termsize` varchar(7) default NULL,
  `client` int(4) default NULL,
  `port` INT(5) NULL DEFAULT NULL,
  PRIMARY KEY  (`id`),
  KEY `starttime` (`starttime`,`sensor`),
  KEY `ord_id` (`ord_id`)
) ;

CREATE TABLE `ttylog` (
  `id` int(11) NOT NULL auto_increment,
  `session` char(32) NOT NULL REFERENCES sessions(id),
  `ttylog` mediumblob NOT NULL,
  PRIMARY KEY  (`id`)
) ;

CREATE TABLE `downloads` (
  `id` int(11) NOT NULL auto_increment,
  `session` CHAR( 32 ) NOT NULL REFERENCES sessions(id),
  `timestamp` datetime NOT NULL,
  `url` text NOT NULL,
  `outfile` text NOT NULL,
  `shasum` varchar(64) default NULL,
  PRIMARY KEY  (`id`),
  KEY `session` (`session`,`timestamp`)
) ;
