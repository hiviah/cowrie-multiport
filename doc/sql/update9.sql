ALTER TABLE `sessions` ADD `port` INT(5) NULL DEFAULT NULL;
ALTER TABLE `sessions` ADD `ord_id` INT(11) NOT NULL auto_increment, ADD KEY `ord_id` (`ord_id`);
ALTER TABLE `auth` ADD KEY(session);
