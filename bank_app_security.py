import psycopg2
from psycopg2 import extras
import getpass 

def get_customer_safe(email_input, db_password):
    connection = None
    try:
        connection = psycopg2.connect(
            dbname="BankManagement",
            user="postgres",
            password=db_password,
            host="localhost",
            port="5432"
        )
        
        cursor = connection.cursor(cursor_factory=extras.DictCursor)

        sql_query = "SELECT CustomerID, FirstName, LastName FROM Customer WHERE Email = %s;"
        
        cursor.execute(sql_query, (email_input,))
        
        customer = cursor.fetchone()
        
        if customer:
            print(f"\nCustomer found: {customer['firstname']} {customer['lastname']} (ID: {customer['customerid']})")
        else:
            print("\nCustomer not found.")

    except Exception as error:
        print(f"\nDatabase error: {error}")
    
    finally:
        if connection:
            cursor.close()
            connection.close()


print("\n--- Database Login ---")
db_password = getpass.getpass("Please enter your PostgreSQL password: ")

print("\n--- Normal User Test ---")
normal_input = "john.doe@email.com" 
get_customer_safe(normal_input, db_password) 

print("\n--- Hacker Test ---")
hacker_input = "john.doe@email.com' OR '1'='1"
get_customer_safe(hacker_input, db_password)