import sqlite3

database = "Posts.db"

table = "Posts"

connection = sqlite3.connect(database)
queries = []
queries.append("DROP TABLE IF EXISTS _{table}_Old;")
queries.append("ALTER TABLE {table} RENAME TO _{table}_Old;")
queries.append("""
CREATE TABLE {table} ( 
    ID TEXT,
    TIME INTEGER DEFAULT 1733976175,
    OWNER INTEGER,
    BODY TEXT, 
    TITLE TEXT
);""")
queries.append("INSERT INTO {table} (ID, OWNER, BODY, TITLE) SELECT ID, OWNER, BODY, TITLE FROM _{table}_Old;")
queries.append("DROP TABLE _{table}_Old;")
for query in queries:
    query = query.format(table=table)
    print(query)
    connection.execute(query) 
connection.close()