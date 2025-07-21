import os
from dotenv import load_dotenv
import psycopg2


load_dotenv()

class KnowledgeRepository:
    def __init__(self):
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        print("Repo Initiated!")

    async def getKnowledgesRepo(self):
        print("Fetching knowledge base documents from database...")

        conn = psycopg2.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host="localhost",
            port=self.port
        )
        cur = conn.cursor()

        sql = f"""
            SELECT *
            FROM knowledge_base
            ORDER BY id DESC
        """

        cur.execute(sql)

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        data = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        print("Documents fetched successfully")
        return data
    
    async def getDocumentPathRepo(self, id: int):
        print("Fetching document path...")

        conn = psycopg2.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host="localhost",
            port=self.port
        )
        cur = conn.cursor()

        sql = f"""
            SELECT report_title, file_path
            FROM knowledge_base
            WHERE id = {id}
        """

        cur.execute(sql)

        rows = cur.fetchone()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()

        if rows:
            print("Path fetched successfully")
            return dict(zip(colnames, rows))
        
        return None
    