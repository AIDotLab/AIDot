import os
from dotenv import load_dotenv
import pymysql

load_dotenv()
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWD = os.getenv("MYSQL_PASSWD")
MYSQL_DB = os.getenv("MYSQL_DB")
MYSQL_CHARSET = os.getenv("MYSQL_CHARSET")

if __name__ == '__main__':
    db = pymysql.connect(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, passwd=MYSQL_PASSWD, db=MYSQL_DB, charset=MYSQL_CHARSET)
    cur = db.cursor()

    sql = "SELECT * FROM myTable"
    cur.execute(sql)

    data_list = cur.fetchall()

    print(data_list[0])
    print(data_list[1])
    print(data_list[2])
    print(data_list[3])

    db.close()
