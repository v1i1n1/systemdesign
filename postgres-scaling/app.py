import os
import string
from contextlib import closing

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="PostgreSQL Scaling Demo")

PRIMARY_DSN = os.environ["PRIMARY_DSN"]
REPLICA_DSN = os.environ["REPLICA_DSN"]
SHARDS = {
    "a": os.environ["SHARD_A_DSN"],
    "b": os.environ["SHARD_B_DSN"],
}


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ShardRecord(BaseModel):
    value: str = Field(min_length=1, max_length=500)


def connect(dsn: str):
    return psycopg.connect(dsn)


def initialize_shards():
    for dsn in SHARDS.values():
        with closing(connect(dsn)) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS shard_records (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            conn.commit()


@app.on_event("startup")
def startup():
    initialize_shards()


def get_shard_dsn(key: str) -> str:
    if not key:
        raise HTTPException(400, "Key cannot be empty")

    first = key[0].lower()
    if first in string.ascii_lowercase[:13]:  # a-m
        return SHARDS["a"]
    if first in string.ascii_lowercase[13:]:  # n-z
        return SHARDS["b"]
    raise HTTPException(400, "Key must start with a letter a-z")


@app.get("/health")
def health():
    return {"status": "ok"}


# Exercise 3: writes go to primary
@app.post("/items")
def create_item(item: ItemCreate):
    try:
        with closing(connect(PRIMARY_DSN)) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO items (name)
                    VALUES (%s)
                    RETURNING id, name, created_at
                    """,
                    (item.name,),
                )
                row = cur.fetchone()
            conn.commit()
        return {
            "id": row[0],
            "name": row[1],
            "created_at": row[2],
            "written_to": "primary",
        }
    except psycopg.Error:
        raise HTTPException(503, "Primary database error")


# Exercise 3: reads go to replica; replication can lag
@app.get("/items")
def list_items():
    try:
        with closing(connect(REPLICA_DSN)) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, name, created_at FROM items ORDER BY id"
                )
                rows = cur.fetchall()
        return {
            "read_from": "replica",
            "items": [
                {"id": r[0], "name": r[1], "created_at": r[2]}
                for r in rows
            ],
        }
    except psycopg.Error:
        raise HTTPException(503, "Replica database error")


# Exercise 5: write a record to its assigned shard
@app.post("/shards/{key}")
def write_shard(key: str, record: ShardRecord):
    dsn = get_shard_dsn(key)
    shard_name = "A" if dsn == SHARDS["a"] else "B"
    try:
        with closing(connect(dsn)) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO shard_records (key, value)
                    VALUES (%s, %s)
                    ON CONFLICT (key)
                    DO UPDATE SET value = EXCLUDED.value
                    RETURNING key, value, created_at
                    """,
                    (key.lower(), record.value),
                )
                row = cur.fetchone()
            conn.commit()
        return {"key": row[0], "value": row[1], "shard": shard_name}
    except psycopg.Error:
        raise HTTPException(503, f"Shard {shard_name} database error")


@app.get("/shards/{key}")
def read_shard(key: str):
    dsn = get_shard_dsn(key)
    shard_name = "A" if dsn == SHARDS["a"] else "B"
    try:
        with closing(connect(dsn)) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT key, value, created_at
                    FROM shard_records WHERE key = %s
                    """,
                    (key.lower(),),
                )
                row = cur.fetchone()
        if row is None:
            raise HTTPException(404, "Record not found")
        return {
            "key": row[0],
            "value": row[1],
            "created_at": row[2],
            "shard": shard_name,
        }
    except psycopg.Error:
        raise HTTPException(503, f"Shard {shard_name} database error")
