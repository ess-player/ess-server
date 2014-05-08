/* Drop existing database and remove all data */
drop database if exists ess;

/* Create new database */
create database ess;

/* Create a new user calles “ess” with the password “secret” and grant all
 * necessary rights to the database */
grant select,insert,update,delete,create,drop,index on ess.*
	to 'ess'@'localhost' identified by 'secret';
