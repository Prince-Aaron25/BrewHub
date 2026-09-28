"""Small parameterized query helpers; services own the transaction boundary."""


def one(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchone()


def all_rows(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.fetchall()


def insert(cur, sql, args=()):
    cur.execute(sql, args)
    return cur.lastrowid

