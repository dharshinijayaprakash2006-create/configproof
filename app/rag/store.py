"""The chunks table in Postgres + pgvector: create it, find what is stored, insert new rows."""

import psycopg
from pgvector import Vector
from pgvector.psycopg import register_vector

from app.rag.chunking import Chunk


def schema_sql(dim: int) -> str:
    return f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id           bigserial PRIMARY KEY,
    doc_id       text NOT NULL,
    source_file  text NOT NULL,
    page         int  NOT NULL,
    section      text NOT NULL DEFAULT '',
    chunk_index  int  NOT NULL,
    kind         text NOT NULL DEFAULT 'text',
    text         text NOT NULL,
    content_hash text NOT NULL UNIQUE,
    model        text NOT NULL,
    embedding    vector({int(dim)}) NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw
    ON chunks USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS chunks_doc_page
    ON chunks (doc_id, page);
"""


def connect(url: str, dim: int) -> psycopg.Connection:
    conn = psycopg.connect(url, autocommit=True)
    conn.execute(schema_sql(dim))  # safe to run every time: IF NOT EXISTS
    register_vector(conn)  # after CREATE EXTENSION: lets us pass vectors as parameters
    return conn


def existing_hashes(conn: psycopg.Connection, hashes: list[str]) -> set[str]:
    rows = conn.execute("SELECT content_hash FROM chunks WHERE content_hash = ANY(%s)", (hashes,))
    return {r[0] for r in rows}


INSERT = """
INSERT INTO chunks (doc_id, source_file, page, section, chunk_index, kind, text,
                    content_hash, model, embedding)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (content_hash) DO NOTHING
"""


def insert_chunks(conn, chunks: list[Chunk], vectors: list[list[float]], model: str) -> int:
    rows = [
        (
            c.doc_id,
            c.source_file,
            c.page,
            c.section,
            c.chunk_index,
            c.kind,
            c.text,
            c.content_hash,
            model,
            Vector(v),
        )
        for c, v in zip(chunks, vectors, strict=True)
    ]
    before = count_chunks(conn)
    with conn.cursor() as cur:
        cur.executemany(INSERT, rows)
    return count_chunks(conn) - before


def count_chunks(conn) -> int:
    return conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
