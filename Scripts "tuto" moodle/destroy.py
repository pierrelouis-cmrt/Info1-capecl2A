import pandas
from sqlalchemy import create_engine
from sqlalchemy import sql
from sqlalchemy.pool import NullPool

# DEFINE THE DATABASE CREDENTIALS
user = 'postgres'
password = ''
host = '127.0.0.1'
port = 5434
database = 'sport' # puis changer à sport une fois la base créée


# PYTHON FUNCTION TO CONNECT TO THE POSTGRESQL DATABASE AND
# RETURN THE SQLACHEMY ENGINE OBJECT
def get_connection():
    return create_engine(url="postgresql://{0}:{1}@{2}:{3}/{4}".format(user, password, host, port, database), poolclass=NullPool)

engine = None
mysql_conn = None
try:
    engine = get_connection()
    print(f"Connecting...")
    with engine.connect() as mysql_conn:
        print(f"Connection to the {host} for user {user} created successfully.")

        #pour modifier le nom d'une base dans table
        query = "DROP DATABASE sport"

        #
        sql_query = sql.text(query)
        mysql_conn.execution_options(isolation_level="AUTOCOMMIT").execute(sql_query)


except Exception as ex:
    print("Connection could not be made due to the following error: \n", ex)

finally:
    if mysql_conn is not None:
        try:
            mysql_conn.close()
        except Exception:
            pass
    if engine is not None:
        engine.dispose()
    print(f"Disconnection to the {host} for user {user} successful.")
