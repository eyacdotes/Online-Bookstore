import sqlite3
from sqlite3 import IntegrityError

database: str = "bookstoredb.db"

def connect():
    return sqlite3.connect(database)

def db_connect()->object:
    return connect(
        host="127.0.0.1",
        user="root",
        password="",
        database="buayadb"
    )

def getProcess(sql:str)->list:
    db = connect()
    cursor = db.cursor()
    cursor.execute(sql)
    return cursor.fetchall()
    
def countall(table:str)->int:
    db = connect()
    cursor = db.cursor()
    if table == 'orders':
        cursor.execute(f"SELECT COUNT(DISTINCT o_id) AS count FROM Orders;")
    else:
        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE status = 1")
    count = cursor.fetchone()[0]
    db.close()
    return count

def getall(table:str, page:int)->list:
    if table == 'orders':
        sql = f"SELECT o.o_id, c.c_name, o.o_date, o.ship_address, ROUND(SUM(io.qty * i.price), 2) AS total_price, o.status FROM Orders o JOIN Customer c ON o.c_id = c.c_id JOIN ItemsOrdered io ON o.io_id = io.io_id JOIN Items i ON io.i_id = i.i_id GROUP BY o.o_id, c.c_name;"
    elif table == 'items':
        if page == 1:
            sql = f"SELECT * FROM {table} WHERE stock >= 1 and status=1"
        else:
            sql = f"SELECT * FROM {table} WHERE status=1"
    else:
        sql = f"SELECT * FROM {table} WHERE status=1"
    return getProcess(sql)

def getstock(item_id)->list:
    sql = f"SELECT stock FROM items WHERE i_id = {item_id}"
    return getProcess(sql)

def getcartitems(c_id)->list:
    sql = f"SELECT items.title, items.price, itemsordered.qty, itemsordered.io_id, items.author, items.genre, items.i_type, itemsordered.c_id, items.i_id, items.stock FROM items JOIN itemsordered ON itemsordered.i_id = items.i_id WHERE itemsordered.c_id = '{c_id}' and itemsordered.status = '1' and items.status = '1' and items.stock != 0;"
    #print(f"sql={sql}")
    return getProcess(sql)
    
def get_recent_orders()->list:
    sql = f"SELECT o.o_id, c.c_name, o.ship_address, ROUND(SUM(io.qty * i.price), 2) AS total_price FROM Orders o JOIN Customer c ON o.c_id = c.c_id JOIN ItemsOrdered io ON o.io_id = io.io_id JOIN Items i ON io.i_id = i.i_id GROUP BY o.o_id, c.c_name ORDER BY o.o_id DESC LIMIT 10;"
    #print(f"sql={sql}")
    return getProcess(sql)
    
def get_recent(table:str, orderby)->list:
    sql = f"SELECT * FROM {table} WHERE status = 1 ORDER BY {orderby} DESC LIMIT 10;"
    #print(f"sql={sql}")
    return getProcess(sql)
    
def get_all_orders()->list:
    sql = "SELECT orders.o_id, customer.c_name, items.title, items.isbn, itemsordered.qty, items.price FROM orders JOIN itemsordered ON orders.io_id = itemsordered.io_id JOIN customer ON orders.c_id = customer.c_id JOIN items ON itemsordered.i_id = items.i_id;"
    return getProcess(sql)

def getorders(c_id)->list:
    sql = f"SELECT orders.o_id, orders.o_date, items.title AS i_name, items.price, itemsordered.qty, orders.status FROM orders JOIN itemsordered ON orders.io_id = itemsordered.io_id JOIN items ON itemsordered.i_id = items.i_id WHERE orders.c_id = {c_id} ORDER BY orders.o_id DESC;"
    return getProcess(sql)
    
def getmax() -> int:
    sql = f"SELECT MAX(o_id) AS max_order_id FROM orders;"
    result = getProcess(sql)

    # Check if result is not None and if the first element is not None
    if result and result[0][0] is not None:
        return result[0][0]
    else:
        # Handle the case where the query didn't return any rows
        return 0  # You can set a default value or handle it based on your requirements
    
def getaddress(u_id):
    sql = f"SELECT customer.c_address FROM customer JOIN users  ON customer.c_id = users.u_id WHERE users.u_id = '{u_id}' AND customer .status = 1;"
    result = getProcess(sql)
    return result[0][0]
    
def updatecartitem(qty, io_id)->bool:
    sql = f"UPDATE itemsordered SET qty = {qty} WHERE io_id = {io_id}"
    success = doProcess(sql)
    return success
    
def updatestockitem(value, i_id)->bool:
    sql = f"UPDATE items SET stock = stock - {value} WHERE i_id = {i_id};"
    success = doProcess(sql)
    return success
    
def gettotalprice(c_id)->list:
    sql = f"SELECT ROUND(SUM(items.price * itemsordered.qty), 2) AS total_price FROM items JOIN itemsordered ON itemsordered.i_id = items.i_id WHERE itemsordered.c_id = '{c_id}' AND itemsordered.status = '1';"
    #print(f"sql={sql}")
    return getProcess(sql)
	
def getrecord(table:str,**kwargs)->list:
    params = list(kwargs.items())
    fields = []
    for index, flds in enumerate(params):
        flds = list(params[index])
        if table == 'items':
            fields.append(f"{flds[0]} LIKE '{flds[1]}%'") if flds[0] != 'i_type' else fields.append(f"{flds[0]} LIKE '{flds[1]}%'")
        elif table == 'users':
            fields.append(f"{flds[0]} = '{flds[1]}'")
        else:
            fields.append(f"{flds[0]} LIKE '%{flds[1]}%'")
    if table == 'users':
        condition = " and ".join(fields)
        sql = f"SELECT * FROM {table} WHERE {condition}"
    else:
        condition = " or ".join(fields)
        sql = f"SELECT * FROM {table} WHERE ({condition}) and status=1"
    print(f"sql={sql}")
    return getProcess(sql)
    
def getitems(table:str,**kwargs)->list:
    params = list(kwargs.items())
    fields = []
    for index, flds in enumerate(params):
        flds = list(params[index])
        fields.append(f"{flds[0]} LIKE '{flds[1]}%'") if flds[0] != 'i_type' else fields.append(f"{flds[0]} LIKE '{flds[1]}%'")
    condition = " or ".join(fields)
    sql = f"SELECT * FROM {table} WHERE ({condition}) and status=1 and stock != 0"
    print(f"sql={sql}")
    return getProcess(sql)
	
def doProcess(sql)->bool:
    db = connect()
    cursor = db.cursor()
    try:
        cursor.execute(sql)
        print(f"SQL: {sql}")
        db.commit()
    except IntegrityError as e:
        if "Duplicate entry" in str(e) and "for key 'idno'" in str(e):
            print("ERROR: IDNO already exists!")
        else:
            print(f"ERROR: {e}")
        return False
    return True if cursor.rowcount>0 else False
	
def addrecord(table: str, **kwargs) -> bool:
    flds = list(kwargs.keys())
    vals = [str(val) for val in kwargs.values()]
    fld = ",".join(flds)
    val = "','".join(vals)
    sql = f"INSERT INTO {table}({fld}) values('{val}')"
    print(sql)
    success = doProcess(sql)
    return success
        
def updaterecord(table, **kwargs) -> bool:
    flds = list(kwargs.keys())
    vals = list(kwargs.values())
    fld = []
    
    for i in range(1, len(flds)):
        if vals[i] != '':
            # Escape single quotes in field values
            field_value = vals[i].replace("'", "''")
            fld.append(f"{flds[i]}='{field_value}'")
    print(fld)
    if len(fld) == 0:
        print("No changes have been made!")
        return False
    else:
        params = ",".join(fld)
        sql = f"UPDATE {table} SET {params} WHERE {flds[0]}='{vals[0]}'"
        print(sql)
        return doProcess(sql)

	
def deleterecord(table,**kwargs)->bool:
    params = list(kwargs.items())
    flds = list(params[0])
    sql = f"UPDATE {table} SET status=0 WHERE {flds[0]}='{flds[1]}'"
    #sql = f"DELETE FROM {table} WHERE {flds[0]}='{flds[1]}'"
    success = doProcess(sql)
    return success
    
    
def deletecartitem(io_id)->bool:
    #sql = f"UPDATE {table} SET status=0 WHERE {flds[0]}='{flds[1]}'"
    sql = f"DELETE FROM itemsordered WHERE io_id = {io_id}"
    success = doProcess(sql)
    return success
