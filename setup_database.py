import sqlite3
import os

DB_FILE = "attendance.db"
STUDENT_DATA = [
    ('Y24120001', 'ANSHUL TAMRAKAR', 'BA'), ('Y24120002', 'KHUSHVEER SINGH SURYAVANSHI', 'BA'),
    ('Y24120003', 'SHREYASHI JAIN', 'BA'), ('Y24120004', 'AAKASH ROHIT', 'BA'),
    ('Y24120005', 'AJAY PATEL', 'BA'), ('Y24120006', 'AMITESH SINGH', 'BA'),
    ('Y24120007', 'ANJALI VISHWAKARMA', 'BA'), ('Y24120008', 'ASMIT SINGH RAJPOOT', 'BA'),
    ('Y24120009', 'AYUSHI', 'BA'), ('Y24120010', 'DEEPAK YADAV', 'BA'),
    ('Y24120011', 'DUSHYANT YADAV', 'BA'), ('Y24120012', 'HEERENDRA SINGH GOND', 'BA'),
    ('Y24120013', 'MUSKAN SHEIKH', 'BA'), ('Y24120014', 'NIKETA VISHWKARMA', 'BA'),
    ('Y24120015', 'RUDRA PRATAP SINGH CHOUHAN', 'BA'), ('Y24120016', 'SANDEEP IRPACHI', 'BA'),
    ('Y24120017', 'SANI RAM', 'BA'), ('Y24120018', 'SHRUTI TIWARI', 'BA'),
    ('Y24120019', 'VAIDEHI KILEDAR', 'BA'), ('Y24120020', 'ANKUSH KUMAR', 'BA'),
    ('Y24120021', 'JYOTI GUPTA', 'BA'), ('Y24120022', 'NEETESH AHIRWAR', 'BA'),
    ('Y24120023', 'NIKHIL AHIRWAR', 'BA'), ('Y24120024', 'RASHMI AHIRWAR', 'BA'),
    ('Y24120025', 'ROHIT SURYAVANSHI', 'BA'), ('Y24120026', 'RUPENDRA BAIGA', 'BA'),
    ('Y24120027', 'PRACHI DAKSH', 'BA'), ('Y24120028', 'SHUBHAM KUSHWAHA', 'BA'),
    ('Y24120029', 'POORVI SAHU', 'BA'), ('Y24120030', 'SNEHA MOURYA', 'BA'),
    ('Y24120031', 'SOUMYA SHARMA', 'BA'), ('Y24120032', 'ADITYA SINGH GOND', 'BA'),
    ('Y24120033', 'GUNGUN RAIKWAR', 'BA'), ('Y24120034', 'JAYA KURMI', 'BA'),
    ('Y24120035', 'PRINCE', 'BA'), ('Y24120036', 'PUSHPENDRA PATEL', 'BA'),
    ('Y24120037', 'RAGNI', 'BA'), ('Y24120038', 'SANJANA KURMI', 'BA'),
    ('Y24120039', 'SHREYA CHOUKSEY', 'BA'), ('Y24120040', 'AKASH VERMA', 'BA'),
    ('Y24120041', 'VIJAY KUMAR', 'BA'), ('Y24120042', 'ADITYA NAMDEV', 'BA'),
    ('Y24120043', 'JYOTI DEVI', 'BA'), ('Y24120044', 'DEVANSH RAJPOOT', 'BA'),
    ('Y24120045', 'GARIMA', 'BA'), ('Y24120046', 'KHUSHI AWADHIYA', 'BA'),
    ('Y24120047', 'RAGHAV RAM DANGI', 'BA'), ('Y24120048', 'RITIK AHIRWAR', 'BA'),
    ('Y24120049', 'SHILPI DEVI AHIRWAR', 'BA'), ('Y24120050', 'SNEHA DEVI LODH', 'BA'),
    ('Y24120053', 'LOKESH YADAV', 'BA'), ('Y24120054', 'RIMJHIM RAJPOOT', 'BA'),
    ('Y24120055', 'VIJAY AHIRWAR', 'BA'), ('Y24120056', 'HARSHVARDHAN RAJ', 'BA'),
    ('Y24120057', 'SAGAR PANDEY', 'BA'), ('Y24120058', 'SONAM GANDHARV', 'BA'),
    ('Y24120059', 'SWPIN TIWARI', 'BA'), ('Y24120060', 'AARYA GOANTIYA', 'BA'),
    ('Y24120061', 'ANIYA PARTE', 'BA'), ('Y24120062', 'SATYAM SEN', 'BA'),
    ('Y24120063', 'AASTHA JAIN', 'BA'), ('Y24120064', 'AMAN KUMAR', 'BA'),
    ('Y24120065', 'HARSH KUMAR', 'BA'), ('Y24120066', 'KARTIK CHADAR', 'BA'),
    ('Y24120067', 'KAUSHAL KUMAR', 'BA'), ('Y24120068', 'MADHUR SINGH THAKUR', 'BA'),
    ('Y24120069', 'MAHAK RAJPOOT', 'BA'), ('Y24120070', 'MOHINI CHOUDHARY', 'BA'),
    ('Y24120071', 'RADHIKA PATEL', 'BA'), ('Y24120072', 'RIDDHIMA DAS', 'BA'),
    ('Y24120073', 'SOURABH AHIRWAR', 'BA'), ('Y24120074', 'TEJRAJ SINGH KUSHWAH', 'BA'),
    ('Y24120076', 'ABHAY DUBEY', 'BA'), ('Y24120077', 'AKASH GHARU', 'BA'),
    ('Y24120078', 'ANUJ GOSWAMI', 'BA'), ('Y24120079', 'ANUSHKA CHADAR', 'BA'),
    ('Y24120080', 'HARSH DUBEY', 'BA'), ('Y24120081', 'HARSHIT DUBEY', 'BA'),
    ('Y24120082', 'HITESH RAJPOOT', 'BA'), ('Y24120083', 'IKRA KHAN', 'BA'),
    ('Y24120084', 'JYOTSANA PRADHAN', 'BA'), ('Y24120085', 'MAHESH KUMAR PATEL', 'BA'),
    ('Y24120086', 'SAAD AHMED', 'BA'), ('Y24120087', 'AGRATI AGRAWAL', 'BA'),
    ('Y24120088', 'SHUBHAM CHOUBEY', 'BA'), ('Y24120090', 'MAHAK SONI', 'BA'),
    ('Y24120091', 'POORNIMA PATEL', 'BA'), ('Y24120092', 'PRADHUMN JOSHI', 'BA'),
    ('Y24120093', 'RASHI TOMAR', 'BA'), ('Y24120094', 'SRAVAN KUMAR MAHAR', 'BA'),
    ('Y24120095', 'SUBHECHHA SONI', 'BA'), ('Y24120096', 'ARTI GOUND', 'BA'),
    ('Y24120097', 'BHAWNA YADAV', 'BA'), ('Y24120098', 'BRIJESH KURMI', 'BA'),
    ('Y24120099', 'HARI KRISHN DEV BARMAN', 'BA'), ('Y24120101', 'NITESH KUMAR VAISHYA', 'BA'),
    ('Y24120102', 'ABHIMAN SINGH', 'BA'), ('Y24120103', 'ALOK KUMAR', 'BA'),
    ('Y24120104', 'ANUSHKA THAKUR DANGI', 'BA'), ('Y24120105', 'AYUSH KUMAR', 'BA'),
    ('Y24120106', 'DEEKSHA GADARIYA', 'BA'), ('Y24120107', 'PAYAL CHADAR', 'BA'),
    ('Y24120108', 'PRIYAM VEER PAL', 'BA'), ('Y24120109', 'PRIYANSHU SINGH GOND', 'BA'),
    ('Y24120110', 'RAVISHANKAR PANIKA', 'BA'), ('Y24120111', 'SHIVANSH SHUKLA', 'BA'),
    ('Y24120112', 'SHOURYA AGRAWAL', 'BA'), ('Y24120113', 'SUPRIYA MISHRA', 'BA'),
    ('Y24120114', 'UTSAV RAJ', 'BA'), ('Y24120115', 'VANSHIKA MISHRA', 'BA'),
    ('Y24120116', 'HARSH LODHI', 'BA'), ('Y24120118', 'ARVIND SINGH GOUND', 'BA'),
    ('Y24120119', 'VAISHALI RAJPOOT', 'BA'), ('Y24120120', 'LAKHAN SAHU', 'BA'),
    ('Y24120121', 'KASHISH MISHRA', 'BA'), ('Y24120122', 'NAMAN KUMAR', 'BA'),
    ('Y24120124', 'YUVRAJ PRAJAPATI', 'BA'), ('Y24120125', 'SUSHIL KUMAR', 'BA'),
    ('Y24120126', 'SHIVANI PRAJAPATI', 'BA'), ('Y24120127', 'RITIK RAJ', 'BA'),
    ('Y24120128', 'AKSHARA AWASTHI', 'BA'), ('Y24120572', 'ARYA PANDEY', 'BA'),
    ('Y24120575', 'VINEETA LODHI', 'BA'), ('Y24120578', 'AADARSH RAJPOOT', 'BA'),
    ('Y24120580', 'MADHAV SAHU', 'BA'), ('Y24120581', 'NITIN BANSAL', 'BA'),
    ('Y24120583', 'SAIYAM JAIN', 'BA'), ('Y24120584', 'AARYAN VISHWAKARMA', 'BA'),
    ('Y24120585', 'SHREYA SAHU', 'BA'), ('Y24120588', 'RAHUL UIKEY', 'BA'),
    ('Y24120589', 'SATYAM LODHI', 'BA'), ('Y24120590', 'UTTSAV PANDEY', 'BA'),
    ('Y24120591', 'RISHABH DEV', 'BA'), ('Y24120611', 'BRAJ RAJAK', 'BA'),
    ('Y24120627', 'RAJEEV DANGI', 'BA'), ('Y24120630', 'AMAN PATEL', 'BA'),
    ('Y24120633', 'ARJUN SEN', 'BA'), ('Y24120642', 'SATYA PRAKASH KUMAR', 'BA'),
    ('Y24120647', 'APOORVA THAKUR', 'BA'), ('Y24120648', 'NEELESH VISHWAKARMA', 'BA'),
    ('Y24120662', 'MAHI SONI', 'BA'), ('Y24130001', 'ADITYA RAJPUT', 'BA'),
    ('Y24130002', 'ANAMIKA TIWARI', 'BA'), ('Y24130003', 'JIMI BANO', 'BA'),
    ('Y24130004', 'ROHIT DAGOUR', 'BA'), ('Y24130005', 'LOKENDRA SINGH', 'BA'),
    ('Y24130007', 'RAJ PATEL', 'BA'), ('Y24130008', 'SHALNI DANGI', 'BA'),
    ('Y24130009', 'SHOBHNA YADAV', 'BA'), ('Y24130058', 'MUSKAN BANO', 'BA'),
]

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def setup_database():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Old database removed.")

    sql_create_students_table = """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT, enrollment_number TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
        course TEXT, password TEXT, device_id TEXT UNIQUE
    );"""
    
    sql_create_attendance_sessions_table = """
    CREATE TABLE IF NOT EXISTS attendance_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, session_date DATE NOT NULL, start_time DATETIME NOT NULL,
        end_time DATETIME NOT NULL, admin_lat REAL NOT NULL, admin_lon REAL NOT NULL
    );"""

    sql_create_admins_table = "CREATE TABLE IF NOT EXISTS admins (id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL);"
    sql_create_attendance_records_table = """
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, session_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')), marked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students (id), FOREIGN KEY (session_id) REFERENCES attendance_sessions (id)
    );"""
    sql_create_reregistration_requests_table = """
    CREATE TABLE IF NOT EXISTS reregistration_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL UNIQUE, request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Pending', FOREIGN KEY (student_id) REFERENCES students (id)
    );"""

    conn = create_connection(DB_FILE)
    if conn is not None:
        create_table(conn, sql_create_admins_table)
        create_table(conn, sql_create_students_table)
        create_table(conn, sql_create_attendance_sessions_table)
        create_table(conn, sql_create_attendance_records_table)
        create_table(conn, sql_create_reregistration_requests_table)
        print("Tables created successfully.")
        
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ('admin', 'password'))
        print("Default admin created (username: admin, password: password)")
        cursor.executemany("INSERT INTO students (enrollment_number, name, course) VALUES (?, ?, ?)", STUDENT_DATA)
        print(f"{len(STUDENT_DATA)} students added to the database.")
        conn.commit()
        conn.close()
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    setup_database()