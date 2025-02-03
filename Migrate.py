import sqlite3

database = "./Data/Posts.db"

table = "Posts"

connection = sqlite3.connect(database)
queries = []
queries.append("ALTER TABLE {table} ADD COLUMN HASIMAGE INTEGER DEFAULT 0;")
for query in queries:
    query = query.format(table=table)
    connection.execute(query) 
connection.close()