from eralchemy import render_er

# Replace "1384" with your actual PostgreSQL password
db_connection_string = "postgresql://postgres:1384@localhost/BankManagement"

# This creates a file called 'schema.png' in the same folder
render_er(db_connection_string, "D:\\Shiraz University\\Term 6\\Database\\Project\\BankDB\\schema.png")
print("Relational Schema image 'schema.png' generated successfully!")