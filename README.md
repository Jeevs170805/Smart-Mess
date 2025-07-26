📖 Project Overview
The Smart Mess Management System is designed for hostel environments where hundreds of students rely on mess services. This system digitizes and automates all core mess operations, from student registration and meal cancellations to monthly fee announcements and real-time UPI-based payments. Admins can track payment status, approve cancellations, and notify students — all via a responsive and user-friendly web interface.

✨ Features
👤 Student Module
Secure Registration & Login

Cancel Meals for future dates (with validation to prevent abuse)

View announced fees, cancellation statuses, and payment QR codes

Click "Paid" to confirm UPI payment

🧑‍💼 Admin Module
Approve/reject student registrations

View and manage meal cancellation requests

Announce monthly mess fee with customizable GST

View pending and received payments

Mark payments as "Received" or "Not Received"

Generate payment history reports by month

💳 Payment Integration
UPI-based QR code generation per student

Fee displayed with GST applied

Easy tracking via Payment Received dashboard

📬 Email Notification System
Students receive emails on:

Registration approval/rejection

Cancellation approval/rejection

Fee announcements

Payment confirmation

🧠 How It Works
Registration Workflow

Student fills out the registration form.

Admin approves the registration.

Student gets email confirmation.

Mess Cancellation

Student selects a valid future date range (>2 days ahead).

Request goes to admin for approval.

Approved dates are excluded from fee calculation.

Fee Announcement

Admin selects GST percentage and announces monthly fee.

Fee is calculated and stored per student (fee_amount).

Notification is sent.

UPI Payment

Student sees a QR code for the fee amount.

After payment, they click "Paid".

Entry goes to payments_received.

Payment Confirmation

Admin reviews received payments.

Marks them as “Received” (logs to payment_history) or “Not Received” (removes entry).

Fee is updated in students table accordingly.

Reports

Admin filters and views payment history month-wise.

Total amount received is displayed.

🛠️ Tech Stack
Layer	Technology
Frontend	HTML, CSS, Bootstrap, Jinja2
Backend	Flask (Python)
Database	MySQL
Email	Flask-Mail + SMTP
Payment	QR Code Generator for UPI
Hosting	(Localhost / XAMPP / WAMP / Render / Heroku)

🗃️ Database Schema
students
Field	Type	Description
DIGITAL_ID	VARCHAR(20)	Primary Key
NAME	VARCHAR(100)	Student full name
EMAIL	VARCHAR(100)	Email address
MOBILE	VARCHAR(20)	Mobile number
PASSWORD	VARCHAR(100)	Encrypted password
STATUS	VARCHAR(20)	pending / approved / rejected
FEE_AMOUNT	FLOAT	Monthly fee to be paid
FEE_STATUS	VARCHAR(20)	paid / unpaid

cancellations
Field	Type
ID	INT (PK)
DIGITAL_ID	VARCHAR(20)
FROM_DATE	DATE
TO_DATE	DATE
STATUS	VARCHAR(20)

payment_received
Field	Type
DIGITAL_ID	VARCHAR(20)
AMOUNT	FLOAT
PAID_DATE	DATE

payment_history
Field	Type
ID	INT (PK)
DIGITAL_ID	VARCHAR(20)
AMOUNT	FLOAT
PAID_DATE	DATE

student_fee_log
Field	Type
ID	INT (PK)
DIGITAL_ID	VARCHAR(20)
AMOUNT	FLOAT
GST	FLOAT
TOTAL	FLOAT
ANNOUNCED_ON	DATE

🚀 Setup Instructions
⚙️ Requirements
Python 3.x

MySQL Server (XAMPP/WAMP or standalone)

Flask (pip install flask flask-mysqldb flask-mail)

Email credentials for SMTP

QR code module (pip install qrcode)

🧩 Steps
Clone the Repository

bash
Copy
Edit
git clone https://github.com/your-username/smart-mess-management.git
cd smart-mess-management
Set up the Database

Create database mess_system

Import the SQL file provided or run the schema manually (students, cancellations, etc.)

Configure config.py (or in-app constants)

Set your DB user, password, host

Add your SMTP email credentials

Run the Flask App

bash
Copy
Edit
python app.py
Visit http://127.0.0.1:5000 in your browser.

📸 Screenshots
Add screenshots of:

Registration form

Admin dashboard

Cancellation requests

Fee announcement form

Payment QR screen

Payment history report

📧 Email Notification Events
Event	Trigger
Student registration approved	Admin action
Registration rejected	Admin action
Cancellation approved	Admin action
Cancellation rejected	Admin action
Payment marked as received	Admin action
Fee announced	Admin action

📌 Future Improvements
🔒 OTP-based student verification

🧠 AI-based mess utilization prediction

📈 Monthly analytics dashboard

📲 Mobile app integration with React Native or Flutter

🔐 JWT-based login and role-based access

📄 License
This project is open-source and available under the MIT License.
