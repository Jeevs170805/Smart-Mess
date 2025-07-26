from flask import Flask, render_template, request, redirect, url_for, session
from db_config import get_db_connection
from datetime import datetime, timedelta
import sys
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os

app = Flask(__name__)
app.secret_key = 'your_super_secret_key' 
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = EMAIL_USER         # ✅ your email
app.config['MAIL_PASSWORD'] = EMAIL_PASS            # ✅ use App Password (not your main Gmail password)
app.config['MAIL_DEFAULT_SENDER'] = 'jeevs170805@gmail.com'   # ✅ same as above

mail = Mail(app)

def send_email(to, subject, body):
    try:
        msg = Message(subject, recipients=[to])
        msg.body = body
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send email to {to}: {e}")



 # set this securely in production

# -----------------------------
# Home Page
# -----------------------------
@app.route('/')
def home():
    return render_template('Login.html')


# -----------------------------
# Student Login Page
# -----------------------------
@app.route('/student_login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM STUDENTS WHERE USERNAME = %s AND PASSWORD = %s", (username, password))
        student = cursor.fetchone()
        cursor.close()
        db.close()

        if student:
            if student['STATUS'] == 'approved':
                session['digital_id'] = student['DIGITAL_ID']
                session['name'] = student['NAME']
                return redirect('/student_dashboard')
            else:
                return render_template('Student_Login.html', error="Account not approved by admin yet.")
        else:
            return render_template('Student_Login.html', error="Invalid username or password.")

    return render_template('Student_Login.html')



# -----------------------------
# Admin Login Route
# -----------------------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == '123':
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('Admin_Login.html', error='Invalid credentials')
    return render_template('Admin_Login.html')


# -----------------------------
# Admin Dashboard
# -----------------------------
@app.route('/admin_dashboard')
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    today = datetime.today().date()

    # Get last updated date
    cursor.execute("SELECT FEE_DATE FROM STUDENT_FEE_LOG ORDER BY ID DESC LIMIT 1")
    row = cursor.fetchone()
    last_updated = row['FEE_DATE'] if row else (today - timedelta(days=1))

    # Update fees only if needed
    num_days = (today - last_updated).days
    if num_days > 0:
        cursor.execute("SELECT DIGITAL_ID FROM STUDENTS")
        students = cursor.fetchall()

        for student in students:
            total_fee = 0
            for i in range(1, num_days + 1):
                check_date = last_updated + timedelta(days=i)

                # Check if cancelled
                cursor.execute("""
                    SELECT 1 FROM CANCELLATIONS
                    WHERE DIGITAL_ID = %s AND STATUS = 'approved'
                    AND %s BETWEEN FROM_DATE AND TO_DATE
                """, (student['DIGITAL_ID'], check_date))

                if not cursor.fetchone():
                    total_fee += 120

            if total_fee > 0:
                cursor.execute("""
                    UPDATE STUDENTS SET FEE_AMOUNT = FEE_AMOUNT + %s
                    WHERE DIGITAL_ID = %s
                """, (total_fee, student['DIGITAL_ID']))

        # Update the log
        cursor.execute("INSERT INTO STUDENT_FEE_LOG (FEE_DATE) VALUES (%s)", (today,))
        conn.commit()

    # 🔽 Your existing admin logic (render template, etc)
    return render_template('Admin_Page.html')




# -----------------------------
# Student Registration
# -----------------------------
@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        name = request.form['name']
        year = request.form['year']
        department = request.form['department']
        hostel = request.form['hostel']
        room = request.form['room']
        email = request.form['email']
        digital_id = request.form['digital_id']
        mobile = request.form['mobile']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('Student_Registration.html', error="Passwords do not match.")

        try:
            db = get_db_connection()
            cursor = db.cursor()

            # ✅ Check if Digital ID already exists
            cursor.execute("SELECT * FROM STUDENTS WHERE DIGITAL_ID = %s", (digital_id,))
            existing_digital_id = cursor.fetchone()

            if existing_digital_id:
                cursor.close()
                db.close()
                return render_template('Student_Registration.html', error="Digital ID already registered. Please use a different one.")

            # ✅ Proceed with registration
            cursor.execute("""
                INSERT INTO STUDENTS (NAME, YEAR, DEPARTMENT, HOSTEL, ROOM, EMAIL, DIGITAL_ID, MOBILE, USERNAME, PASSWORD, STATUS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            """, (name, year, department, hostel, room, email, digital_id, mobile, username, password))

            db.commit()
            cursor.close()
            db.close()

            return render_template('Student_Registration.html', success="Registration successful! Waiting for admin approval.")

        except Exception as e:
            print("Error:", e)
            return render_template('Student_Registration.html', error="Registration failed. Try again.")

    return render_template('Student_Registration.html')




# -----------------------------
# Student Dashboard
# -----------------------------
@app.route('/student_dashboard')
def student_dashboard():
    if 'digital_id' not in session:
        return redirect('/student_login')

    student_id = session['digital_id']
    name = session.get('name', 'Student')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT FEE_AMOUNT FROM STUDENTS WHERE DIGITAL_ID = %s", (student_id,))
    student = cursor.fetchone()
    conn.close()

    import qrcode
    import io
    import base64

    def generate_upi_qr(upi_id, amount, name):
        upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
        qr = qrcode.make(upi_url)
        buf = io.BytesIO()
        qr.save(buf, format='PNG')
        qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return qr_base64

    # If fee is present, show it and generate QR code
    if student and float(student['FEE_AMOUNT']) > 0:
        fee = float(student['FEE_AMOUNT'])
        due_amount = f"₹{int(fee)}"
        qr_code = generate_upi_qr("jeevs170805@oksbi", fee, name)
    else:
        due_amount = "₹XXXX"
        qr_code = None

    return render_template('Student_Page.html', name=name, due_amount=due_amount, qr_code=qr_code)

# -----------------------------
# Student Management (Admin)
# -----------------------------
@app.route('/student_management', methods=['GET', 'POST'])
def student_management():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    year_filter = request.args.get('year', 'All')
    search_query = request.args.get('search', '').strip()

    query = "SELECT * FROM STUDENTS WHERE 1=1"
    params = []

    if year_filter != 'All':
        query += " AND YEAR = %s"
        params.append(year_filter)

    if search_query:
        query += " AND (NAME LIKE %s OR USERNAME LIKE %s)"
        like_search = f"%{search_query}%"
        params.extend([like_search, like_search])

    cursor.execute(query, tuple(params))
    students = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        'Student_Management.html',
        students=students,
        selected_year=year_filter,
        search_query=search_query
    )


# -----------------------------
# Approve Student (Set status to 'approved')
# -----------------------------
@app.route('/approve_student/<string:digital_id>')
def approve_student(digital_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    # ✅ Fetch email by DIGITAL_ID
    cursor.execute("SELECT EMAIL FROM STUDENTS WHERE DIGITAL_ID=%s", (digital_id,))
    result = cursor.fetchone()

    if result:
        email = result['EMAIL']
        cursor.execute("UPDATE STUDENTS SET STATUS='approved' WHERE DIGITAL_ID=%s", (digital_id,))
        db.commit()
        send_email(email, "Smart Mess - Registration Approved", "Your registration has been approved by the admin.")

    cursor.close()
    db.close()
    return redirect(url_for('student_management'))


@app.route('/reject_student/<int:student_id>')
def reject_student(student_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT EMAIL FROM STUDENTS WHERE ID=%s", (student_id,))
    email = cursor.fetchone()['EMAIL']

    cursor.execute("DELETE FROM STUDENTS WHERE ID=%s", (student_id,))
    db.commit()
    cursor.close()
    db.close()

    send_email(email, "Smart Mess - Registration Rejected", "Your registration has been rejected by the admin.")
    return redirect(url_for('student_management'))

# -----------------------------
# Fee Announcement Page
# -----------------------------
@app.route('/fee_announcement')
def fee_announcement():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ Fetch pending payments
    cursor.execute("SELECT * FROM PAYMENTS_RECEIVED")
    payments = cursor.fetchall()

    # ✅ Fetch payment history
    cursor.execute("SELECT * FROM PAYMENT_HISTORY")
    payment_history = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('fee_announcement.html', payments=payments, payment_history=payment_history)



@app.route('/submit_cancellation', methods=['POST'])
def submit_cancellation():
    digital_id = request.form['digital_id']
    from_date_str = request.form['from_date']
    to_date_str = request.form['to_date']

    # Convert to date objects
    from_date = datetime.strptime(from_date_str, "%Y-%m-%d").date()
    to_date = datetime.strptime(to_date_str, "%Y-%m-%d").date()
    today = datetime.today().date()

    # Rule 1: Check dates are in the future (not today or past)
    if from_date <= today or to_date <= today:
        return render_template("Student_Page.html", error="Dates must be in the future (not today or past).", digital_id=digital_id)

    # Rule 2: Date range should be more than 2 days
    if (to_date - from_date).days <= 2:
        return render_template("Student_Page.html", error="Cancellation range must be more than 2 days.", digital_id=digital_id)

    # Save to DB
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO CANCELLATIONS (DIGITAL_ID, FROM_DATE, TO_DATE, STATUS)
            VALUES (%s, %s, %s, 'pending')
        """, (digital_id, from_date_str, to_date_str))
        db.commit()
        cursor.close()
        db.close()
        return render_template("Student_Page.html", success="Cancellation request submitted successfully.", digital_id=digital_id)
    except Exception as e:
        print("Error:", e)
        return render_template("Student_Page.html", error="Error submitting cancellation. Try again.", digital_id=digital_id)

@app.route('/admin_cancellations')
def admin_cancellations():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT C.ID, C.DIGITAL_ID, S.NAME, C.FROM_DATE, C.TO_DATE, C.STATUS
        FROM cancellations C
        JOIN students S ON C.DIGITAL_ID = S.DIGITAL_ID
        WHERE C.STATUS = 'pending'
    """)

    requests = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('Admin_Cancellations.html', requests=requests)

@app.route('/approve_cancellation/<int:request_id>', methods=['POST'])
def approve_cancellation(request_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT S.EMAIL FROM CANCELLATIONS C
        JOIN STUDENTS S ON C.DIGITAL_ID = S.DIGITAL_ID
        WHERE C.ID = %s
    """, (request_id,))
    email = cursor.fetchone()['EMAIL']

    cursor.execute("UPDATE CANCELLATIONS SET STATUS = 'approved' WHERE ID = %s", (request_id,))
    db.commit()
    cursor.close()
    db.close()

    send_email(email, "Smart Mess - Cancellation Approved", "Your mess cancellation request has been approved.")
    return redirect(url_for('admin_cancellations'))


@app.route('/deny_cancellation/<int:request_id>', methods=['POST'])
def deny_cancellation(request_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT S.EMAIL FROM CANCELLATIONS C
        JOIN STUDENTS S ON C.DIGITAL_ID = S.DIGITAL_ID
        WHERE C.ID = %s
    """, (request_id,))
    email = cursor.fetchone()['EMAIL']

    cursor.execute("UPDATE CANCELLATIONS SET STATUS = 'denied' WHERE ID = %s", (request_id,))
    db.commit()
    cursor.close()
    db.close()

    send_email(email, "Smart Mess - Cancellation Denied", "Your mess cancellation request has been denied.")
    return redirect(url_for('admin_cancellations'))


@app.route('/announce_fee', methods=['POST'])
def announce_fee():
    gst_percent = float(request.form['gst'])

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch all students
    cursor.execute("SELECT DIGITAL_ID, FEE_AMOUNT FROM STUDENTS")
    students = cursor.fetchall()

    for student in students:
        base_fee = float(student['FEE_AMOUNT'])  # Convert Decimal to float
        gst_amount = base_fee * (gst_percent / 100)
        updated_fee = round(base_fee + gst_amount)

        cursor.execute("""
            UPDATE STUDENTS SET FEE_AMOUNT = %s WHERE DIGITAL_ID = %s
        """, (updated_fee, student['DIGITAL_ID']))
    
    cursor.execute("UPDATE STUDENTS SET FEE_STATUS = TRUE")
    cursor.execute("SELECT * FROM PAYMENTS_RECEIVED")
    payments = cursor.fetchall()

    # Send email to all students
    for student in students:
        cursor.execute("SELECT EMAIL FROM STUDENTS WHERE DIGITAL_ID = %s", (student['DIGITAL_ID'],))
        email = cursor.fetchone()['EMAIL']
        send_email(email, "Smart Mess - Fee Updated", "Your mess fee has been updated. Please check your dashboard.")


    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('fee_announcement'))


@app.route('/admin_mark_payment', methods=['POST'])
def admin_mark_payment():
    digital_id = request.form['digital_id']
    amount = float(request.form['amount'])
    paid_date = request.form['paid_date']
    paid_date = paid_date if paid_date != '' else None  # Handle blank

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert into PAYMENT_HISTORY
    cursor.execute("""
        INSERT INTO PAYMENT_HISTORY (DIGITAL_ID, AMOUNT, PAID_DATE)
        VALUES (%s, %s, %s)
    """, (digital_id, amount, paid_date))

    # Update student table
    cursor.execute("""
        UPDATE STUDENTS
        SET FEE_AMOUNT = 0, FEE_STATUS = 'paid'
        WHERE DIGITAL_ID = %s
    """, (digital_id,))

    # Delete from PAYMENTS_RECEIVED based on whether date is NULL
    if paid_date:
        cursor.execute("""
            DELETE FROM PAYMENTS_RECEIVED
            WHERE DIGITAL_ID = %s AND AMOUNT = %s AND PAID_DATE = %s
        """, (digital_id, amount, paid_date))
    else:
        cursor.execute("""
            DELETE FROM PAYMENTS_RECEIVED
            WHERE DIGITAL_ID = %s AND AMOUNT = %s AND PAID_DATE IS NULL
        """, (digital_id, amount))

    # Send email
    cursor.execute("SELECT EMAIL FROM STUDENTS WHERE DIGITAL_ID = %s", (digital_id,))
    result = cursor.fetchone()
    if result:
        email = result[0]
        send_email(email, "Smart Mess - Payment Received", f"Your payment of ₹{amount} has been received.")

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('fee_announcement'))



@app.route('/admin_ignore_payment', methods=['POST'])
def admin_ignore_payment():
    digital_id = request.form['digital_id']
    amount = float(request.form['amount'])
    paid_date = request.form['paid_date']
    paid_date = paid_date if paid_date != '' else None  # Handle blank

    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete from PAYMENTS_RECEIVED correctly
    if paid_date:
        cursor.execute("""
            DELETE FROM PAYMENTS_RECEIVED
            WHERE DIGITAL_ID = %s AND AMOUNT = %s AND PAID_DATE = %s
        """, (digital_id, amount, paid_date))
    else:
        cursor.execute("""
            DELETE FROM PAYMENTS_RECEIVED
            WHERE DIGITAL_ID = %s AND AMOUNT = %s AND PAID_DATE IS NULL
        """, (digital_id, amount))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('fee_announcement'))

 # Update if needed


@app.route('/mark_payment', methods=['POST'])
def mark_payment():
    digital_id = request.form['digital_id']
    amount = float(request.form['amount'])

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO PAYMENTS_RECEIVED (DIGITAL_ID, AMOUNT) VALUES (%s, %s)", (digital_id, amount))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/student_dashboard')

@app.route('/payment_history', methods=['GET', 'POST'])
def payment_history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    month = None
    total_received = 0

    if request.method == 'POST':
        month = request.form['month']
        cursor.execute("""
            SELECT * FROM PAYMENT_HISTORY
            WHERE MONTH(PAID_DATE) = %s
        """, (month,))
    else:
        cursor.execute("SELECT * FROM PAYMENT_HISTORY")

    payments = cursor.fetchall()

    # Calculate total
    for p in payments:
        total_received += float(p['AMOUNT'])

    cursor.close()
    conn.close()

    return render_template('payment.html', payments=payments, month=month, total=total_received)


# -----------------------------
# Run the App
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
