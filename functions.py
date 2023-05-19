import sqlite3

# Check if the data already exists in the database cache
def is_duplicate(cursor, title):
    cursor.execute("SELECT title FROM trade WHERE title = ?", (title,))
    return cursor.fetchone() is not None

# Load existing data from the database cache
def load_database_cache(database):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM trade")    
    cache = set(title[0] for title in cursor.fetchall())
    #cursor.fetchall() retrieves all the rows returned by the SELECT query as a list of tuples. Each tuple contains the values of the columns in the selected rows.
    #The expression title[0] for title in cursor.fetchall() is a list comprehension that extracts the first element (index 0) from each tuple in the result. In this case, it extracts the title value from each tuple.
    conn.close()
    return cache