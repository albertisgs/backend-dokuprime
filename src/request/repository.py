import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class RequestRepository:
    def __init__(self):
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.db_name = os.getenv("DB_NAME")
        self.port = os.getenv("DB_PORT")
        print("Repo Initiated!")

    async def addPromptRepo(
            self,
            usecase_name: str,
            priority: str,
            user_request: str,
            team: str,
            reason: str,
            prompt: str
        ):
        print("Adding new prompt into database...")

        with psycopg2.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host="localhost",
            port=self.port,
            options='-c timezone=Asia/Jakarta'
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    INSERT into user_requests (
                        usecase_name, priority, user_request, team, reason, prompt
                    )
                    VALUES
                    ('{usecase_name}', '{priority}', '{user_request}', '{team}', '{reason}', '{prompt}');
                """)
                conn.commit()

        print("New prompt successfully added")

    async def getRequestRepo(self):
        print("Fetching requests from database...")

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
            FROM user_requests
            ORDER BY request_date DESC
        """

        cur.execute(sql)

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

        data = [dict(zip(columns, row)) for row in rows]

        cur.close()
        conn.close()

        print("Requests fetched successfully")
        return data

    async def getRequestByIdRepo(self, id: int):
        print("Fetching requests from database...")

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
            FROM user_requests
            WHERE id = {id}
        """

        cur.execute(sql)

        rows = cur.fetchone()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()

        print("Requests fetched successfully")
        return dict(zip(colnames, rows))
    