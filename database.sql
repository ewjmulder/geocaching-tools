create table caches (
  id int,
  name varchar(1024),
  code varchar(7),
  premiumOnly bool,
  favoritePoints int,
  geocacheType ENUM('lala', 'lolo')
);




insert into caches values (1, "name", "1234567", true, 5, 'lala');

