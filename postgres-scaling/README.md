# PostgreSQL Database Scaling Lab

Practice replication, read/write splitting, and application-level sharding with PostgreSQL 16, Docker Compose, FastAPI, and psycopg.

## Requirements
- Docker Desktop running
- Docker Compose v2
- PowerShell (Windows) or a terminal

## Start
```powershell
docker compose up -d --build
docker compose ps
docker compose logs -f api
```

Open Swagger: http://localhost:8000/docs

## Exercise 1 & 2: Primary/replica replication
The primary is exposed on localhost:5432; the replica on localhost:5433.

Create a record:
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/items -ContentType "application/json" -Body '{"name":"Replication test"}'
```

Read records through the replica:
```powershell
Invoke-RestMethod http://localhost:8000/items
```

Verify replica mode:
```powershell
docker exec -it pg-replica psql -U appuser -d appdb -c "SELECT pg_is_in_recovery();"
docker exec -it pg-replica psql -U appuser -d appdb -c "SELECT * FROM items;"
```
`pg_is_in_recovery()` should return true on the replica. Streaming replication is asynchronous, so a newly inserted row can take a moment to appear.

## Exercise 3: API read/write routing
- `POST /items` writes to primary.
- `GET /items` reads from replica.

This demonstrates read/write splitting, not automatic failover. The API returns 503 if the selected database is unavailable.

## Exercise 4 & 5: Two shards
This lab routes keys based on their first letter:
- a–m -> Shard A (localhost port 5434)
- n–z -> Shard B (localhost port 5435)

Write records:
```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/shards/alice -ContentType "application/json" -Body '{"value":"Customer Alice"}'
Invoke-RestMethod -Method Post -Uri http://localhost:8000/shards/rahul -ContentType "application/json" -Body '{"value":"Customer Rahul"}'
```

Read them:
```powershell
Invoke-RestMethod http://localhost:8000/shards/alice
Invoke-RestMethod http://localhost:8000/shards/rahul
```

Inspect each shard:
```powershell
docker exec -it pg-shard-a psql -U appuser -d appdb -c "SELECT * FROM shard_records;"
docker exec -it pg-shard-b psql -U appuser -d appdb -c "SELECT * FROM shard_records;"
```

## Stop
```powershell
docker compose down
```
To remove all database data and start from scratch (destructive):
```powershell
docker compose down -v
```

## Important limitations
This is a local educational demo, not production-ready. It does not implement automatic primary failover, shard replication, connection pooling, TLS, production secrets, or robust retry policies. The replication account is configured for the isolated Docker lab only. Do not expose these ports to an untrusted network.
