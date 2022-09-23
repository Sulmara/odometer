# odometer
build 2022-09-24
support: duncan.mcrae@sulmara.com

## input:
- takes in a tuple "(E,N)" on a udp port.

## output:
- write to database (stored locacally)
```
MariaDB [ras]> select * from odom order by id desc limit 5;
+-----+-----------+-----------+----------+----------+---------------------+
| id  | e         | n         | distance | odometer | timestamp           |
+-----+-----------+-----------+----------+----------+---------------------+
| 538 | 136776.97 | 136790.49 |     5.31 |  3330.24 | 2022-09-23 06:21:38 |
| 537 | 136773.10 | 136786.85 |     5.15 |  3324.93 | 2022-09-23 06:21:37 |
| 536 | 136769.76 | 136782.93 |     5.21 |  3319.78 | 2022-09-23 06:21:36 |
| 535 | 136765.95 | 136779.37 |     5.00 |  3314.57 | 2022-09-23 06:21:35 |
| 534 | 136762.34 | 136775.91 |     4.65 |  3309.57 | 2022-09-23 06:21:34 |
+-----+-----------+-----------+----------+----------+---------------------+
5 rows in set (0.001 sec)
```
- send output via udp to ROC at user set intervals

## future:
- use sql commands to recall from db

## notes:
- database build:
MariaDB [ras]> desc odom;
+-----------+------------------+------+-----+---------------------+----------------+
| Field     | Type             | Null | Key | Default             | Extra          |
+-----------+------------------+------+-----+---------------------+----------------+
| id        | int(10) unsigned | NO   | PRI | NULL                | auto_increment |
| e         | decimal(9,2)     | NO   |     | NULL                |                |
| n         | decimal(9,2)     | NO   |     | NULL                |                |
| distance  | decimal(10,2)    | YES  |     | NULL                |                |
| odometer  | decimal(10,2)    | YES  |     | NULL                |                |
| timestamp | timestamp        | NO   |     | current_timestamp() |                |
+-----------+------------------+------+-----+---------------------+----------------+
6 rows in set (0.002 sec)
