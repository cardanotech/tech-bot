import psycopg2
import psycopg2.extras
import queue
from threading import Thread
from api import queries as q
import select

class DBConnector:
    def __init__(self, uname, pswd, dbname, host, port = 5432):
        self.uname = uname
        self.pswd = pswd
        self.dbname = dbname
        self.host = host
        self.port = port

        self.conn = psycopg2.connect(database=dbname, host=host, port=port, user=uname, password=pswd)
        self.conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

    def execute(self, query):
        result = None
        try:
            cur = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(query)
            result = cur.fetchall()

        except (psycopg2.DatabaseError) as error:
            print(error)
        return result

    def start_block_listener(self):
        block_q = queue.Queue(10)
        Thread(target=self._block_listener, args=(block_q,), daemon=True).start()
        return block_q

    def _block_listener(self, block_q):
        self.execute(q.create_notify)
        self.execute(q.create_trigger)

        conn = psycopg2.connect(database=self.dbname, host=self.host, port=self.port, user=self.uname, password=self.pswd)
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("LISTEN NEW_BLOCK;")

        while True:
            if select.select([conn], [], [], 1800) == ([], [], []):
                print("timeout")
                pass
            conn.poll()

            while conn.notifies:
                notify = conn.notifies.pop(0)
                slot_no = notify.payload

                try:
                    block_q.put(slot_no)
                except queue.Full:
                    pass
