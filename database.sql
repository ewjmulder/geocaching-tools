drop table caches;

create table caches (
  id int,
  code varchar(7),
  name varchar(1024),
  location geography(point, 4326),
  type
  ...
);




insert into caches values (1, '1234567', 'My first cache', 'SRID=4326;POINT(5 52)');
insert into caches values (2, '1234568', 'My second cache', 'SRID=4326;POINT(5 53)');
insert into caches values (3, '1234569', 'My third cache', 'SRID=4326;POINT(150 15)');

