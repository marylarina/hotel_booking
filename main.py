from flask import Flask, render_template, request, redirect
from flask_paginate import Pagination, get_page_parameter
import psycopg2
from psycopg2 import sql
from config import host, user, password, db_name

app = Flask(__name__)


def get_connection():
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        return connection
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)


connection = get_connection()


@app.route('/')
def home_page():
    return render_template('index.html')


@app.route('/main')
def databases_list():
    cursor = connection.cursor()
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    """)

    table_names = [table[0] for table in cursor.fetchall()]
    result = []
    for table_name in table_names:
        result.append(table_name)
    return render_template('main.html', table_names=result)


@app.route('/main/<string:name>', methods=['GET'])
def selected_database(name):
    cursor = connection.cursor()

    cursor.execute(f"""SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public' and table_name = %(name)s
        """, {'name': name})

    column_names = [column_name[0] for column_name in cursor.fetchall()]

    stmt1 = sql.SQL("""
           SELECT * from {table_name} ORDER BY {id}
    """).format(table_name=sql.Identifier(name), id=sql.Identifier(column_names[0]))

    cursor.execute(stmt1)
    database_all = cursor.fetchall()

    limit = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = page*limit - limit
    stmt = sql.SQL("""
               SELECT * from {table_name} ORDER BY {id} LIMIT {limit} OFFSET {offset}
        """).format(table_name=sql.Identifier(name), id=sql.Identifier(column_names[0]), limit=sql.Literal(limit),
                    offset=sql.Literal(offset))
    cursor.execute(stmt)
    database = cursor.fetchall()
    pagination = Pagination(page=page, per_page=limit, total=len(database_all))

    stmt2 = sql.SQL("""SELECT booking.booking_id, SUM(price) FROM booking_list, booking, room
where booking.booking_id = booking_list.booking_id and room.room_id = booking_list.room_id GROUP BY booking.booking_id
 ORDER BY booking.booking_id;""")
    cursor.execute(stmt2)
    booking_price = cursor.fetchall()

    stmt3 = sql.SQL("""SELECT booking_id, departure_date - arrival_date FROM booking;""")
    cursor.execute(stmt3)
    booking_days = cursor.fetchall()

    max_salary = sql.SQL("""SELECT MAX(salary) FROM employee""")
    cursor.execute(max_salary)
    max_salary_output = cursor.fetchone()
    row_count = len(database_all)
    connection.commit()
    return render_template('table_output.html',
                           name=name, database=database, column_names=column_names, row_count=row_count,
                           max_salary_output=max_salary_output[0], pagination=pagination, sort=1,
                           booking_price=booking_price, booking_days=booking_days)


@app.route('/main/booking_arrival', methods=['GET'])
def booking_arrival():
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' and table_name = 'booking'
            """)

    column_names = [column_name[0] for column_name in cursor.fetchall()]
    order_arrival = sql.SQL("""SELECT * FROM booking ORDER BY arrival_date""")
    cursor.execute(order_arrival)
    order_arrival_output = cursor.fetchall()
    row_count = len(order_arrival_output)

    limit = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = page * limit - limit
    stmt = sql.SQL("""
                   SELECT * from booking ORDER BY arrival_date LIMIT {limit} OFFSET {offset}
            """).format(limit=sql.Literal(limit),
                        offset=sql.Literal(offset))
    cursor.execute(stmt)
    database = cursor.fetchall()

    stmt2 = sql.SQL("""SELECT booking.booking_id, SUM(price) FROM booking_list, booking, room
    where booking.booking_id = booking_list.booking_id and room.room_id = booking_list.room_id GROUP BY booking.booking_id
     ORDER BY booking.arrival_date;""")
    cursor.execute(stmt2)
    booking_price = cursor.fetchall()

    stmt3 = sql.SQL("""SELECT booking_id, departure_date - arrival_date FROM booking ORDER BY booking.arrival_date;""")
    cursor.execute(stmt3)
    booking_days = cursor.fetchall()

    pagination = Pagination(page=page, per_page=limit, total=len(order_arrival_output))
    return render_template('table_output.html',
                           name='booking', database=database, column_names=column_names,
                           row_count=row_count, pagination=pagination, sort=2, booking_price=booking_price, booking_days=booking_days)


@app.route('/main/booking_departure', methods=['GET'])
def booking_departure():
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' and table_name = 'booking'
            """)

    column_names = [column_name[0] for column_name in cursor.fetchall()]
    order_departure = sql.SQL("""SELECT * FROM booking ORDER BY departure_date""")
    cursor.execute(order_departure)
    order_departure_output = cursor.fetchall()
    row_count = len(order_departure_output)

    limit = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = page * limit - limit
    stmt = sql.SQL("""
                       SELECT * from booking ORDER BY departure_date LIMIT {limit} OFFSET {offset}
                """).format(limit=sql.Literal(limit),
                            offset=sql.Literal(offset))
    cursor.execute(stmt)
    database = cursor.fetchall()

    stmt2 = sql.SQL("""SELECT booking.booking_id, SUM(price) FROM booking_list, booking, room
    where booking.booking_id = booking_list.booking_id and room.room_id = booking_list.room_id GROUP BY booking.booking_id
     ORDER BY booking.departure_date;""")
    cursor.execute(stmt2)
    booking_price = cursor.fetchall()

    stmt3 = sql.SQL("""SELECT booking_id, departure_date - arrival_date FROM booking ORDER BY booking.departure_date;""")
    cursor.execute(stmt3)
    booking_days = cursor.fetchall()

    pagination = Pagination(page=page, per_page=limit, total=len(order_departure_output))
    return render_template('table_output.html',
                           name='booking', database=database, column_names=column_names,
                           row_count=row_count, pagination=pagination, sort=3, booking_price=booking_price, booking_days=booking_days)


@app.route('/main/employee_type/<string:job_name>', methods=['GET'])
def employee_filter(job_name):
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' and table_name = 'employee'
                """)
    column_names = [column_name[0] for column_name in cursor.fetchall()]
    employee = sql.SQL("""SELECT * FROM employee WHERE job_name = {job_name}""").format(job_name=sql.Literal(job_name))
    cursor.execute(employee)
    employee_type = cursor.fetchall()
    row_count = len(employee_type)

    limit = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = page * limit - limit
    stmt = sql.SQL("""
                       SELECT * from employee WHERE job_name = {job_name} LIMIT {limit} OFFSET {offset}
                """).format(limit=sql.Literal(limit),
                            offset=sql.Literal(offset), job_name=sql.Literal(job_name))
    cursor.execute(stmt)
    database = cursor.fetchall()
    pagination = Pagination(page=page, per_page=limit, total=len(employee_type))
    return render_template('table_output.html',
                           name='employee', database=database, column_names=column_names,
                           row_count=row_count, pagination=pagination, sort=job_name)


@app.route('/main/order_name', methods=['GET'])
def client_order_by_name():
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' and table_name = 'client'
                """)

    column_names = [column_name[0] for column_name in cursor.fetchall()]
    first_name = sql.SQL("""SELECT * FROM client ORDER BY first_name""")
    cursor.execute(first_name)
    first_name_output = cursor.fetchall()
    row_count = len(first_name_output)

    limit = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = page * limit - limit
    stmt = sql.SQL("""
                       SELECT * from client ORDER BY first_name LIMIT {limit} OFFSET {offset}
                """).format(limit=sql.Literal(limit),
                            offset=sql.Literal(offset))
    cursor.execute(stmt)
    database = cursor.fetchall()
    pagination = Pagination(page=page, per_page=limit, total=len(first_name_output))
    return render_template('table_output.html',
                           name='client', database=database, column_names=column_names,
                           row_count=row_count, pagination=pagination, sort=4)


@app.route('/main/order_surname', methods=['GET'])
def client_order_by_surname():
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public' and table_name = 'client'
                """)

    column_names = [column_name[0] for column_name in cursor.fetchall()]
    last_name = sql.SQL("""SELECT * FROM client ORDER BY last_name""")
    cursor.execute(last_name)
    last_name_output = cursor.fetchall()
    row_count = len(last_name_output)

    limit = 10
    page = request.args.get(get_page_parameter(), type=int, default=1)
    offset = page * limit - limit
    stmt = sql.SQL("""
                       SELECT * from client ORDER BY last_name LIMIT {limit} OFFSET {offset}
                """).format(limit=sql.Literal(limit),
                            offset=sql.Literal(offset))
    cursor.execute(stmt)
    database = cursor.fetchall()
    pagination = Pagination(page=page, per_page=limit, total=len(last_name_output))
    return render_template('table_output.html',
                           name='client', database=database, column_names=column_names,
                           row_count=row_count, pagination=pagination, sort=5)


@app.route('/main/<string:name>/delete/<int:id>', methods=['POST', 'GET'])
def delete_record(name, id):
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public' and table_name = %(name)s
            """, {'name': name})

    column_names = [column_name[0] for column_name in cursor.fetchall()]

    stmt = sql.SQL("""DELETE FROM {table_name} WHERE {table_id} = {id}""").format(table_name=sql.Identifier(name),
                                                                                  table_id=sql.Identifier(
                                                                                      column_names[0]),
                                                                                  id=sql.Literal(id))
    cursor.execute(stmt)

    connection.commit()
    return redirect(f'/main/{name}')


@app.route('/main/<string:name>/delete/<int:employee_id>/<int:room_id>', methods=['POST', 'GET'])
def delete_room_service(name, employee_id, room_id):
    cursor = connection.cursor()
    stmt = sql.SQL("""DELETE FROM {table_name} WHERE employee_id = {employee_id} AND room_id = {room_id}""").format(
        table_name=sql.Identifier(name),
        employee_id=sql.Literal(employee_id),
        room_id=sql.Literal(room_id))
    cursor.execute(stmt)
    connection.commit()
    return redirect(f'/main/{name}')


@app.route("/main/<string:name>/edit/<int:id>", methods=['POST', 'GET'])
def edit_record(name, id):
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                            FROM information_schema.columns
                            WHERE table_schema = 'public' and table_name = %(name)s
                        """, {'name': name})

    column_names = [column_name[0] for column_name in cursor.fetchall()]
    column_names_copy = column_names.copy()
    column_names_copy.remove(column_names[0])

    stmt = sql.SQL("""
                       SELECT * FROM {table_name} WHERE {table_id} = {id}
                """).format(table_name=sql.Identifier(name), table_id=sql.Identifier(column_names[0]),
                            id=sql.Literal(id))

    cursor.execute(stmt)
    database = cursor.fetchall()
    stmt1 = sql.SQL("""SELECT employee_type FROM employee_type""")
    cursor.execute(stmt1)
    employee_type = cursor.fetchall()
    cursor.close()
    return render_template("edit.html", id=id, name=name, database=database[0], column_names=column_names, employee_type=employee_type)


@app.route('/main/<string:name>/update/<int:id>', methods=['POST'])
def update_record(name, id):
    if request.method == 'POST':
        cursor = connection.cursor()
        cursor.execute(f"""SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = 'public' and table_name = %(name)s
                            """, {'name': name})

        column_names = [column_name[0] for column_name in cursor.fetchall()]
        column_names_copy = column_names.copy()
        column_names_copy.remove(column_names[0])
        edit_records = [[column] for column in column_names_copy]
        count = 0
        for column in column_names_copy:
            if not request.form[f'{column}']:
                break
            else:
                edit_records[column_names_copy.index(column)].append(request.form[f'{column}'])
                count += 1

        if count == len(column_names_copy):
            stmt = sql.SQL("""UPDATE {name} SET """).format(name=sql.Identifier(name))
            for element in edit_records:
                element1 = sql.Identifier(element[0])
                element2 = sql.Literal(element[1])
                stmt += sql.SQL(""" = """).join([element1, element2])
                if element != edit_records[-1]:
                    stmt += sql.SQL(""", """)
            stmt += sql.SQL("""WHERE {table_id} = {id}""").format(table_id=sql.Identifier(column_names[0]),
                                                                  id=sql.Literal(id))
            cursor.execute(stmt)
            connection.commit()
        return redirect(f'/main/{name}')


@app.route('/main/<string:name>/add_render', methods=['POST', 'GET'])
def add_render(name):
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = 'public' and table_name = %(name)s
                            """, {'name': name})

    column_names = [column_name[0] for column_name in cursor.fetchall()]
    column_names_copy = column_names.copy()
    if name != 'room_service':
        column_names_copy.remove(column_names[0])

    stmt1 = sql.SQL("""SELECT employee_type FROM employee_type""")
    cursor.execute(stmt1)
    employee_type = cursor.fetchall()

    cursor.close()
    return render_template("add.html", name=name, column_names=column_names, employee_type=employee_type)


@app.route('/main/<string:name>/add', methods=['POST'])
def add_record(name):
    if request.method == 'POST':
        cursor = connection.cursor()
        cursor.execute(f"""SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = 'public' and table_name = %(name)s
                            """, {'name': name})

        column_names = [column_name[0] for column_name in cursor.fetchall()]
        column_names_copy = column_names.copy()
        if name != 'room_service':
            column_names_copy.remove(column_names[0])
        add_records = [[column] for column in column_names_copy]
        count = 0
        for column in column_names_copy:
            if not request.form[f'{column}']:
                break
            else:
                add_records[column_names_copy.index(column)].append(request.form[f'{column}'])
                count += 1

        if count == len(column_names_copy):
            stmt = sql.SQL("""INSERT INTO {name}(""").format(name=sql.Identifier(name))
            for element in add_records:
                element1 = sql.Identifier(element[0])
                stmt += sql.SQL(""" {element1} """).format(element1=element1)
                if element != add_records[-1]:
                    stmt += sql.SQL(""" , """)
            stmt += sql.SQL(""") VALUES ( """)
            for element in add_records:
                element2 = sql.Literal(element[1])
                stmt += sql.SQL("""{element2} """).format(element2=element2)
                if element != add_records[-1]:
                    stmt += sql.SQL(""" , """)
            stmt += sql.SQL(""")""")

            cursor.execute(stmt)
            connection.commit()
        return redirect(f'/main/{name}')


@app.route('/main/booking/add_booking_render', methods=['POST', 'GET'])
def add_booking_render():
    cursor = connection.cursor()
    cursor.execute("""SELECT room_type FROM room_type""")
    room_type = cursor.fetchall()
    cursor.execute("""SELECT client_id, first_name, last_name FROM client""")
    client = cursor.fetchall()
    return render_template("add_booking.html", room_type=room_type, client=client)


def find_room():
    cursor = connection.cursor()
    if request.method == 'POST':
        arrival_date = request.form['arrival_date']
        departure_date = request.form['departure_date']
        adult_number = request.form['adult_number']
        children_number = request.form['children_number']
        room_type = request.form['room_type']
        client_id = request.form['client_id']

        if not arrival_date or not departure_date or not adult_number or not children_number or not room_type or not client_id:
            return ['error']

        if arrival_date > departure_date:
            return ['error']

        stmt1 = sql.SQL("""SELECT booking_id FROM booking WHERE (({arrival_date} >= arrival_date AND {arrival_date} <= departure_date) OR 
            ({departure_date} >= arrival_date AND {departure_date} <= departure_date))""").format(
            arrival_date=sql.Literal(arrival_date),
            departure_date=sql.Literal(departure_date))

        cursor.execute(stmt1)
        already_booked_ids = cursor.fetchall()

        if len(already_booked_ids) > 0:
            stmt2 = sql.SQL("""SELECT room_id FROM booking_list WHERE""")
            for element in already_booked_ids:
                stmt2 += sql.SQL(""" booking_id = {element} """).format(element=sql.Literal(element[0]))
                if element != already_booked_ids[-1]:
                    stmt2 += sql.SQL("""OR """)
            cursor.execute(stmt2)
            booked_rooms_list = cursor.fetchall()

            stmt3 = sql.SQL("""SELECT room_id FROM room WHERE""")
            count1 = 0
            for element in booked_rooms_list:
                stmt3 += sql.SQL(""" room_id <> {element} """).format(element=sql.Literal(element[0]))
                count1 += 1
                if count1 != len(booked_rooms_list):
                    stmt3 += sql.SQL("""AND """)
            cursor.execute(stmt3)
            all_type_free = cursor.fetchall()
        else:
            cursor.execute("""SELECT room_id FROM room""")
            all_type_free = cursor.fetchall()

        stmt4 = sql.SQL("""SELECT room_id FROM room WHERE (room_type = {room_type}) AND (""").format(
            room_type=sql.Literal(room_type))
        for element in all_type_free:
            stmt4 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
            if element != all_type_free[-1]:
                stmt4 += sql.SQL("""OR """)
        stmt4 += sql.SQL(""" )""")
        cursor.execute(stmt4)
        req_type_room_list = cursor.fetchall()

        if len(req_type_room_list) != 0:
            stmt5 = sql.SQL("""SELECT * FROM room WHERE (capacity >= {adult_number} + {children_number}) 
                AND (""").format(adult_number=sql.Literal(int(adult_number)),
                                 children_number=sql.Literal(int(children_number)))
            for element in req_type_room_list:
                stmt5 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                if element != req_type_room_list[-1]:
                    stmt5 += sql.SQL("""OR """)
            stmt5 += sql.SQL(""" ) ORDER BY capacity""")
            cursor.execute(stmt5)
            number_clients_room_list = cursor.fetchall()[:1]
        else:
            number_clients_room_list = []

        if len(number_clients_room_list) == 0:
            if len(req_type_room_list) != 0:
                stmt6 = sql.SQL("""SELECT capacity FROM room WHERE""")
                for element in req_type_room_list:
                    stmt6 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                    if element != req_type_room_list[-1]:
                        stmt6 += sql.SQL("""OR """)
                cursor.execute(stmt6)
                rooms_capacity_list = cursor.fetchall()
                count = 0
                result = 0
                for element in rooms_capacity_list:
                    if result < int(adult_number) + int(children_number):
                        result += int(element[0])
                        count += 1
                    else:
                        break
                if result < int(adult_number) + int(children_number):
                    stmt7 = sql.SQL("""SELECT * FROM room WHERE (capacity >= {adult_number} + {children_number}) 
                                AND (""").format(adult_number=sql.Literal(int(adult_number)),
                                                 children_number=sql.Literal(int(children_number)))
                    for element in all_type_free:
                        stmt7 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                        if element != all_type_free[-1]:
                            stmt7 += sql.SQL("""OR """)
                    stmt7 += sql.SQL(""" ) ORDER BY capacity""")
                    cursor.execute(stmt7)
                    number_clients_room_all_type_list = cursor.fetchall()[:1]

                    if len(number_clients_room_all_type_list) == 0:
                        stmt8 = sql.SQL("""SELECT capacity FROM room WHERE""")
                        for element in all_type_free:
                            stmt8 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                            if element != all_type_free[-1]:
                                stmt8 += sql.SQL("""OR """)
                        cursor.execute(stmt8)
                        rooms_capacity_all_type_list = cursor.fetchall()
                        count = 0
                        result = 0
                        for element in rooms_capacity_all_type_list:
                            if result < int(adult_number) + int(children_number):
                                result += int(element[0])
                                count += 1
                            else:
                                break
                        if result < int(adult_number) + int(children_number):
                            return []
                        else:
                            flag = 0
                            stmt9 = sql.SQL(""" SELECT * FROM room WHERE """)
                            for element in all_type_free:
                                if flag < count:
                                    stmt9 += sql.SQL(""" room_id = {element} """).format(
                                        element=sql.Literal(element[0]))
                                    flag += 1
                                    if flag != count:
                                        stmt9 += sql.SQL("""OR """)
                            cursor.execute(stmt9)
                            final_rooms_all_type_list = cursor.fetchall()
                            return final_rooms_all_type_list
                    else:
                        return number_clients_room_all_type_list
                else:
                    flag = 0
                    stmt10 = sql.SQL(""" SELECT * FROM room WHERE """)
                    for element in req_type_room_list:
                        if flag < count:
                            stmt10 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                            flag += 1
                            if flag != count:
                                stmt10 += sql.SQL("""OR """)
                    cursor.execute(stmt10)
                    final_rooms_list = cursor.fetchall()
                    return final_rooms_list
            else:
                stmt7 = sql.SQL("""SELECT * FROM room WHERE (capacity >= {adult_number} + {children_number}) 
                                                AND (""").format(adult_number=sql.Literal(int(adult_number)),
                                                                 children_number=sql.Literal(int(children_number)))
                for element in all_type_free:
                    stmt7 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                    if element != all_type_free[-1]:
                        stmt7 += sql.SQL("""OR """)
                stmt7 += sql.SQL(""" ) ORDER BY capacity""")
                cursor.execute(stmt7)
                number_clients_room_all_type_list = cursor.fetchall()[:1]

                if len(number_clients_room_all_type_list) == 0:
                    stmt8 = sql.SQL("""SELECT capacity FROM room WHERE""")
                    for element in all_type_free:
                        stmt8 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                        if element != all_type_free[-1]:
                            stmt8 += sql.SQL("""OR """)
                    cursor.execute(stmt8)
                    rooms_capacity_all_type_list = cursor.fetchall()
                    count = 0
                    result = 0
                    for element in rooms_capacity_all_type_list:
                        if result < int(adult_number) + int(children_number):
                            result += int(element[0])
                            count += 1
                        else:
                            break
                    if result < int(adult_number) + int(children_number):
                        return []
                    else:
                        flag = 0
                        stmt9 = sql.SQL(""" SELECT * FROM room WHERE """)
                        for element in all_type_free:
                            if flag < count:
                                stmt9 += sql.SQL(""" room_id = {element} """).format(element=sql.Literal(element[0]))
                                flag += 1
                                if flag != count:
                                    stmt9 += sql.SQL("""OR """)
                        cursor.execute(stmt9)
                        final_rooms_all_type_list = cursor.fetchall()
                        return final_rooms_all_type_list
                else:
                    return number_clients_room_all_type_list
        else:
            return number_clients_room_list


@app.route('/main/booking/add_booking', methods=['POST'])
def add_booking():
    cursor = connection.cursor()
    database = find_room()
    if request.method == 'POST':
        booking_date = request.form['booking_date']
        arrival_date = request.form['arrival_date']
        departure_date = request.form['departure_date']
        adult_number = request.form['adult_number']
        children_number = request.form['children_number']
        room_type = request.form['room_type']
        client_id = request.form['client_id']

        cursor.execute(f"""SELECT column_name
                                        FROM information_schema.columns
                                        WHERE table_schema = 'public' and table_name = 'room'
                                    """)

        column_names = [column_name[0] for column_name in cursor.fetchall()]
        return render_template("submit_booking.html", name='room', database=database,
                               column_names=column_names,
                               booking_date=booking_date, arrival_date=arrival_date, departure_date=departure_date,
                               adult_number=adult_number, children_number=children_number, room_type=room_type,
                               client_id=client_id)


@app.route('/main/booking/submit', methods=['POST', 'GET'])
def submit():
    cursor = connection.cursor()
    database = find_room()
    if request.method == 'POST':
        booking_date = request.form['booking_date']
        arrival_date = request.form['arrival_date']
        departure_date = request.form['departure_date']
        adult_number = request.form['adult_number']
        children_number = request.form['children_number']
        room_type = request.form['room_type']
        client_id = request.form['client_id']

        stmt1 = sql.SQL("""INSERT INTO booking(booking_date, arrival_date, departure_date, 
        adult_number, children_number, room_type, client_id) VALUES ({booking_date}, {arrival_date}, {departure_date}, 
        {adult_number}, {children_number}, {room_type}, {client_id}) """).format(booking_date=sql.Literal(booking_date),
                                                                                 arrival_date=sql.Literal(arrival_date),
                                                                                 departure_date=sql.Literal(
                                                                                     departure_date),
                                                                                 adult_number=sql.Literal(adult_number),
                                                                                 children_number=sql.Literal(
                                                                                     children_number),
                                                                                 room_type=sql.Literal(room_type),
                                                                                 client_id=sql.Literal(client_id))

        cursor.execute(stmt1)

        stmt2 = sql.SQL("""SELECT booking_id from booking where booking_id = (SELECT MAX(booking_id) from booking)""")

        cursor.execute(stmt2)
        booking_id = cursor.fetchone()

        ids = []
        for row in database:
            ids.append(row[0])

        for element in ids:
            stmt3 = sql.SQL(
                """INSERT INTO booking_list(booking_id, room_id) VALUES ({booking_id}, {element})""").format(
                booking_id=sql.Literal(booking_id[0]),
                element=sql.Literal(element))
            cursor.execute(stmt3)
    return redirect('/main/booking')


@app.route('/main/client/add_render_client', methods=['POST', 'GET'])
def add_render_client():
    cursor = connection.cursor()
    cursor.execute(f"""SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = 'public' and table_name = 'client'
                            """)

    column_names = [column_name[0] for column_name in cursor.fetchall()]
    column_names_copy = column_names.copy()
    column_names_copy.remove(column_names[0])

    cursor.close()
    return render_template("add_client.html", column_names=column_names)


@app.route('/main/client/add_client', methods=['POST'])
def add_new_client_booking():
    if request.method == 'POST':
        cursor = connection.cursor()
        cursor.execute(f"""SELECT column_name
                                FROM information_schema.columns
                                WHERE table_schema = 'public' and table_name = 'client'
                            """)

        column_names = [column_name[0] for column_name in cursor.fetchall()]
        column_names_copy = column_names.copy()
        column_names_copy.remove(column_names[0])
        add_records = [[column] for column in column_names_copy]
        count = 0
        for column in column_names_copy:
            if not request.form[f'{column}']:
                break
            else:
                add_records[column_names_copy.index(column)].append(request.form[f'{column}'])
                count += 1

        if count == len(column_names_copy):
            stmt = sql.SQL("""INSERT INTO client(""")
            for element in add_records:
                element1 = sql.Identifier(element[0])
                stmt += sql.SQL(""" {element1} """).format(element1=element1)
                if element != add_records[-1]:
                    stmt += sql.SQL(""" , """)
            stmt += sql.SQL(""") VALUES ( """)
            for element in add_records:
                element2 = sql.Literal(element[1])
                stmt += sql.SQL("""{element2} """).format(element2=element2)
                if element != add_records[-1]:
                    stmt += sql.SQL(""" , """)
            stmt += sql.SQL(""")""")
            cursor.execute(stmt)
            connection.commit()
        return redirect('/main/booking/add_booking_render')


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)
