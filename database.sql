DROP TABLE finds;
DROP TABLE dnfs;
DROP TABLE caches;
DROP TABLE users;
DROP TYPE GC_TYPE;
DROP TYPE GC_SIZE;


CREATE TYPE GC_TYPE AS ENUM ('traditional', 'multi', 'mystery', 'letterbox', 'earth', 'virtual', 'event', 'webcam', 'cito-event', 'wherigo', 'reverse', 'mega-event', 'giga-event');
CREATE TYPE GC_SIZE AS ENUM ('micro', 'small', 'regular', 'large', 'other', 'virtual', 'unknown');
CREATE TYPE GC_STATUS AS ENUM ('enabled', 'disabled');

CREATE TABLE caches (
  id INT PRIMARY KEY,
  code VARCHAR(7),
  name VARCHAR(1024),
  type GC_TYPE,
  location GEOGRAPHY(POINT, 4326),
  status GC_STATUS,
  size GC_SIZE,
  difficulty NUMERIC(2, 1) CHECK (difficulty = 1.0 OR difficulty = 1.5 OR difficulty = 2.0 OR difficulty = 2.5 OR difficulty = 3.0 OR difficulty = 3.5 OR difficulty = 4.0 OR difficulty = 4.5 OR difficulty = 5.0),
  terrain NUMERIC(2, 1) CHECK (terrain = 1.0 OR terrain = 1.5 OR terrain = 2.0 OR terrain = 2.5 OR terrain = 3.0 OR terrain = 3.5 OR terrain = 4.0 OR terrain = 4.5 OR terrain = 5.0),
  placed DATE,
  owner VARCHAR(255)
);

CREATE TABLE users (
  id INT PRIMARY KEY,
  username VARCHAR(255)
);

CREATE TABLE finds (
  user_id INT REFERENCES users(id),
  cache_id INT REFERENCES caches(id)
);

CREATE TABLE dnfs (
  user_id INT REFERENCES users(id),
  cache_id INT REFERENCES caches(id)
);

INSERT INTO caches VALUES (1, 'GC81X1W', 'Beukenstein - De Heuvel / The Hill', 'traditional', 'SRID=4326;POINT(5.2763 52.059333)', 'enabled', 'small', 1.5, 2.0, '2018-12-30', 'Team_Spoorloos');
INSERT INTO users VALUES (1, 'Team_Spoorloos');
INSERT INTO finds VALUES (1, 1);
INSERT INTO dnfs VALUES (1, 1);
