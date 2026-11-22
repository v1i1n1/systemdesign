# MySQL Master–Replica Replication Using Docker

## 1. Project Overview

This project demonstrates how to configure **MySQL Master–Replica Replication** using Docker Compose.

The objective is to understand how data is synchronized between two independent MySQL servers and how replication works internally using Binary Logs, Relay Logs, and replication threads.

### Technologies Used

- MySQL 8.4
- Docker
- Docker Compose
- GTID-based replication
- MySQL Binary Logging

## 2. Architecture

```text
                  APPLICATION
                       |
                       |
                       v
              +------------------+
              |   MYSQL MASTER   |
              |   Server ID: 1   |
              |   Port: 3306     |
              +------------------+
                       |
                       |
                 Binary Log
                       |
                       v
              +------------------+
              |   MYSQL REPLICA  |
              |   Server ID: 2   |
              |   Port: 3307     |
              +------------------+
                       |
                  Relay Log
                       |
                       v
                 SQL Applier
                       |
                       v
                REPLICA DATABASE
```

### How Replication Works

1. Application sends INSERT, UPDATE, or DELETE queries to Master.
2. Master executes the transaction and records changes in its Binary Log.
3. Replica I/O thread connects to Master and reads Binary Log events.
4. Replica stores received events in its Relay Log.
5. Replica SQL applier reads events from Relay Log.
6. SQL applier executes the transactions on Replica.
7. Data becomes available on Replica.

## 3. Project Structure

```text
mysql-replication/
│
├── docker-compose.yml
└── README.md
```

## 4. Docker Compose Configuration

Create a file named `docker-compose.yml`.

```yaml
services:
  mysql-primary:
    image: mysql:8.4
    container_name: mysql-primary
    environment:
      MYSQL_ROOT_PASSWORD: root123
    ports:
      - "3306:3306"
    command:
      - --server-id=1
      - --log-bin=mysql-bin
      - --binlog-format=ROW
      - --gtid-mode=ON
      - --enforce-gtid-consistency=ON
    volumes:
      - primary_data:/var/lib/mysql

  mysql-replica:
    image: mysql:8.4
    container_name: mysql-replica
    environment:
      MYSQL_ROOT_PASSWORD: root123
    ports:
      - "3307:3306"
    command:
      - --server-id=2
      - --relay-log=relay-bin
      - --read-only=ON
      - --gtid-mode=ON
      - --enforce-gtid-consistency=ON
      - --log-replica-updates=ON
    volumes:
      - replica_data:/var/lib/mysql

volumes:
  primary_data:
  replica_data:
```

### Important Configuration Parameters

| Parameter | Description |
|---|---|
| server-id | Unique identifier for each MySQL server |
| log-bin | Enables Binary Logging |
| binlog-format | Defines Binary Log format |
| gtid-mode | Enables Global Transaction Identifiers |
| relay-log | Stores events received by Replica |
| read-only | Restricts ordinary writes on Replica |
| log-replica-updates | Logs replicated transactions on Replica |

## 5. Start MySQL Servers

Start both containers:

```bash
docker compose up -d
```

Check running containers:

```bash
docker ps
```

Expected containers:

- mysql-primary
- mysql-replica

## 6. Configure Replication User on Master

Connect to Master:

```bash
docker exec -it mysql-primary mysql -uroot -proot123
```

Create a replication user:

```sql
CREATE USER 'replication_user'@'%'
IDENTIFIED BY 'ReplPass123!';

GRANT REPLICATION SLAVE ON *.*
TO 'replication_user'@'%';
```

Exit MySQL:

```sql
EXIT;
```

## 7. Configure Replica

Connect to Replica:

```bash
docker exec -it mysql-replica mysql -uroot -proot123
```

Configure Master connection:

```sql
CHANGE REPLICATION SOURCE TO
SOURCE_HOST='mysql-primary',
SOURCE_PORT=3306,
SOURCE_USER='replication_user',
SOURCE_PASSWORD='ReplPass123!',
SOURCE_AUTO_POSITION=1;
```

For this local Docker lab, enable public-key retrieval for MySQL 8.4 authentication:

```sql
CHANGE REPLICATION SOURCE TO
GET_SOURCE_PUBLIC_KEY = 1;
```

Start replication:

```sql
START REPLICA;
```

## 8. Verify Replication Status

Execute:

```sql
SHOW REPLICA STATUS\G
```

Check these fields:

```text
Replica_IO_Running: Yes
Replica_SQL_Running: Yes
```

Other important fields:

| Field | Description |
|---|---|
| Replica_IO_Running | I/O thread connection status |
| Replica_SQL_Running | SQL applier status |
| Retrieved_Gtid_Set | GTIDs retrieved by Replica |
| Executed_Gtid_Set | GTIDs executed by Replica |
| Seconds_Behind_Source | Estimated replication lag |
| Last_IO_Error | I/O thread error |
| Last_SQL_Error | SQL applier error |

Both replication threads should show `Yes`.

## 9. Practical Experiment 1: INSERT Replication

Connect to Master:

```bash
docker exec -it mysql-primary mysql -uroot -proot123
```

Create a database:

```sql
CREATE DATABASE company;

USE company;
```

Create an employees table:

```sql
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    salary INT
);
```

Insert records:

```sql
INSERT INTO employees VALUES
(1, 'Vinay', 50000),
(2, 'Rahul', 60000),
(3, 'Priya', 70000);
```

Connect to Replica:

```bash
docker exec -it mysql-replica mysql -uroot -proot123
```

Verify:

```sql
USE company;

SELECT * FROM employees;
```

Expected output:

| ID | Name | Salary |
|---|---|---|
| 1 | Vinay | 50000 |
| 2 | Rahul | 60000 |
| 3 | Priya | 70000 |

The records inserted on Master should automatically appear on Replica.

## 10. Practical Experiment 2: UPDATE Replication

On Master:

```sql
UPDATE company.employees
SET salary = 90000
WHERE id = 1;
```

On Replica:

```sql
SELECT * FROM company.employees;
```

Expected result: Vinay's salary changes from 50000 to 90000.

## 11. Practical Experiment 3: DELETE Replication

On Master:

```sql
DELETE FROM company.employees
WHERE id = 2;
```

On Replica:

```sql
SELECT * FROM company.employees;
```

Expected result: Rahul's record disappears from Replica.

## 12. Practical Experiment 4: Replica Downtime and Recovery

This experiment demonstrates how MySQL catches up after temporary Replica downtime.

### Step 1: Stop Replica

```bash
docker stop mysql-replica
```

### Step 2: Insert records on Master

```sql
INSERT INTO company.employees VALUES
(4, 'Arun', 80000),
(5, 'Kiran', 85000);
```

### Step 3: Restart Replica

```bash
docker start mysql-replica
```

### Step 4: Verify recovered records

```bash
docker exec -it mysql-replica mysql -uroot -proot123
```

Execute:

```sql
SELECT * FROM company.employees;
```

Expected result: Replica catches up and receives the missing transactions, provided the required Binary Logs are still available.

## 13. Understanding GTID Replication

GTID stands for Global Transaction Identifier.

Each transaction receives a unique identifier.

Example:

```text
Transaction 1 -> UUID:1
Transaction 2 -> UUID:2
Transaction 3 -> UUID:3
Transaction 4 -> UUID:4
```

GTID helps MySQL identify which transactions have already been executed and which transactions are missing.

Check GTID status:

```sql
SHOW REPLICA STATUS\G
```

Look at:

```text
Retrieved_Gtid_Set
Executed_Gtid_Set
```

## 14. Inspect Binary Logs

On Master:

```sql
SHOW BINARY LOGS;
```

Check the current Binary Log:

```sql
SHOW MASTER STATUS;
```

Inspect Binary Log events from the command line:

```bash
docker exec mysql-primary mysqlbinlog \
  --base64-output=DECODE-ROWS -vv \
  /var/lib/mysql/mysql-bin.000001
```

Note: The Binary Log filename may differ depending on your MySQL instance.

## 15. Inspect Relay Logs

On Replica:

```sql
SHOW REPLICA STATUS\G
```

Find the Relay Log filename.

You can inspect it using:

```bash
docker exec mysql-replica mysqlbinlog \
  --base64-output=DECODE-ROWS -vv \
  /var/lib/mysql/relay-bin.000001
```

The Relay Log contains events retrieved from Master that are waiting to be applied or have been processed.

## 16. Important Replication Concepts

| Concept | Explanation |
|---|---|
| Master / Source | Server where transactions originate |
| Replica | Server that receives and applies transactions |
| Binary Log | Records database changes |
| I/O Thread | Fetches events from Master |
| Relay Log | Stores received events |
| SQL Applier | Applies events on Replica |
| GTID | Unique transaction identifier |
| Replication Lag | Delay between Master and Replica |

## 17. Troubleshooting

### Issue 1: Authentication requires secure connection

Error:

```text
Authentication plugin 'caching_sha2_password'
reported error: Authentication requires secure connection.
```

Solution for this local lab:

```sql
STOP REPLICA;

CHANGE REPLICATION SOURCE TO
GET_SOURCE_PUBLIC_KEY = 1;

START REPLICA;
```

### Issue 2: Replica cannot connect to Master

Check:

- Both Docker containers are running.
- Master hostname is correct.
- Replication user exists.
- Replication permissions are granted.

### Issue 3: Replication is not running

Execute:

```sql
SHOW REPLICA STATUS\G
```

Inspect:

```text
Last_IO_Error
Last_SQL_Error
```

### Issue 4: Replica data is not updated

Check:

```text
Replica_IO_Running
Replica_SQL_Running
Seconds_Behind_Source
```

Investigate replication errors and lag.

## 18. Clean Up

Stop containers:

```bash
docker compose down
```

To remove containers and persistent database volumes:

```bash
docker compose down -v
```

**Warning:** The `-v` option permanently deletes the MySQL data stored in the Docker volumes.

## 19. Production Considerations

This project demonstrates asynchronous replication in a local development environment.

For production deployments, consider:

- TLS encryption for replication connections.
- Secure credential management.
- Binary Log retention and backups.
- Monitoring replication lag.
- Replication consistency checks.
- Automated failover and leader election.
- High availability and disaster recovery.
- Restricting Replica writes using appropriate database permissions.

## 20. Key Takeaway

The complete MySQL replication workflow:

```text
INSERT / UPDATE / DELETE
          |
          v
      MASTER
          |
          v
      BINARY LOG
          |
          v
      I/O THREAD
          |
          v
      RELAY LOG
          |
          v
      SQL APPLIER
          |
          v
       REPLICA
```

**Master → Binary Log → I/O Thread → Relay Log → SQL Applier → Replica Database**

This project demonstrates how database replication works internally and how MySQL maintains copies of data across multiple database servers.
