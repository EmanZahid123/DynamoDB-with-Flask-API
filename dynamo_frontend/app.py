from flask import Flask, jsonify, request, render_template
import boto3
import csv
from boto3.dynamodb.conditions import Key
import time
from decimal import Decimal, InvalidOperation
from boto3.dynamodb.conditions import Attr

app = Flask(__name__)

# Initialize DynamoDB local instance
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',  # Use DynamoDB Local
    region_name='us-west-2',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)


# Function to create the Products table
def create_products_table():
    try:
        table = dynamodb.create_table(
            TableName='Products',
            KeySchema=[
                {'AttributeName': 'product_id', 'KeyType': 'HASH'}  # Partition Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'product_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='Products')
        print(f"Table 'Products' created successfully!")
    except Exception as e:
        print(f"Error creating Products table: {e}")

# Function to create the Orders table
def create_orders_table():
    try:
        table = dynamodb.create_table(
            TableName='Orders',
            KeySchema=[
                {'AttributeName': 'order_id', 'KeyType': 'HASH'}  # Partition Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'order_id', 'AttributeType': 'S'}  # Define only order_id as a key attribute
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='Orders')
        print(f"Table 'Orders' created successfully!")
    except Exception as e:
        print(f"Error creating Orders table: {e}")


# Function to create the Customers Table
def create_customers_table():
    try:
        table = dynamodb.create_table(
            TableName='Customers',
            KeySchema=[
                {'AttributeName': 'customer_id', 'KeyType': 'HASH'}  # Partition Key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'customer_id', 'AttributeType': 'S'}  # Define customer_id as a String
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        table.meta.client.get_waiter('table_exists').wait(TableName='Customers')
        print(f"Table 'Customers' created successfully!")
    except Exception as e:
        print(f"Error creating Customers table: {e}")

from decimal import Decimal

from decimal import Decimal, InvalidOperation

# Function to import data into DynamoDB table from a CSV file
def import_data(table_name, file_path):
    table = dynamodb.Table(table_name)
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            # Convert appropriate fields to match DynamoDB types (if needed)
            if table_name == 'Products':
                try:
                    row['product_weight_g'] = Decimal(row['product_weight_g'])  # Convert to Decimal
                except (InvalidOperation, ValueError):
                    row['product_weight_g'] = Decimal(0)  # Set a default value or skip
                try:
                    row['product_length_cm'] = Decimal(row['product_length_cm'])
                except (InvalidOperation, ValueError):
                    row['product_length_cm'] = Decimal(0)
                try:
                    row['product_height_cm'] = Decimal(row['product_height_cm'])
                except (InvalidOperation, ValueError):
                    row['product_height_cm'] = Decimal(0)
                try:
                    row['product_width_cm'] = Decimal(row['product_width_cm'])
                except (InvalidOperation, ValueError):
                    row['product_width_cm'] = Decimal(0)
                    
            elif table_name == 'Orders':
                # If you need to do any data conversion for the Orders table
                pass
            elif table_name == 'Customers':
                row['customer_zip_code_prefix'] = int(row['customer_zip_code_prefix'])  # Convert to integer

            # Convert the row dictionary to use Decimal types for numerical values
            row = {key: Decimal(value) if isinstance(value, float) else value for key, value in row.items()}
            table.put_item(Item=row)
    print(f"Data imported into {table_name} successfully!")



# Create tables
#create_products_table()
#create_customers_table()
#create_orders_table()

# Import data from CSV files into respective tables
#import_data('Products', 'Data/df_Products.csv')
#import_data('Customers', 'Data/df_Customers.csv')
#import_data('Orders', 'Data/df_Orders.csv')








# Route to query orders for a specific product ID and date range
@app.route('/query_orders_product')
def query_orders_product():
    order_id = request.args.get('order_id')
    order_approved_at = request.args.get('order_approved_at')
    print(order_id, order_approved_at)

    table = dynamodb.Table('Orders')
    
    start_time = time.time()
    response = table.scan(
        FilterExpression=Key('order_id').eq(order_id) & Attr('order_approved_at').eq(order_approved_at)
    )
    end_time = time.time()

    execution_time = end_time - start_time
    log_execution_time("Query Orders for Product ID", execution_time)

    return jsonify(response['Items'])

# Route to sort products by price
@app.route('/sort_products')
def sort_products():
    table = dynamodb.Table('Products')

    start_time = time.time()
    response = table.scan()
    sorted_products = sorted(response['Items'], key=lambda x: float(x['product_weight_g']), reverse=False)  #price
    end_time = time.time()

    execution_time = end_time - start_time
    log_execution_time("Sort Products by Product Weightg", execution_time)

    return jsonify(sorted_products)

# Route to filter orders by status and customer
@app.route('/filter_orders')
def filter_orders():
    order_id = request.args.get('order_id')
    customer_id = request.args.get('customer_id')
    print("Received customer_id:", customer_id)  # Debugging step
    print("Received order_id:", order_id)  # Debugging step

    

    table = dynamodb.Table('Orders')

    start_time = time.time()
   
    response = table.scan(
        FilterExpression=Key('order_id').eq(order_id) & Attr('customer_id').eq(customer_id)
    )
    end_time = time.time()

    execution_time = end_time - start_time
    log_execution_time("Filter Orders by Customer and State", execution_time)

    return jsonify(response['Items'])

# Route to query orders for a specific customer

@app.route('/query_customer_orders')
def query_customer_orders():
    customer_id = request.args.get('customer_id')
    table = dynamodb.Table('Orders')

    start_time = time.time()
    
    # Test with hardcoded customer_id first
    response = table.scan(
        FilterExpression=Attr('customer_id').eq(customer_id)  # Filter on customer_id
    )

    print("Response Items:", response['Items'])  # Debugging step
    
    end_time = time.time()
    execution_time = end_time - start_time
    log_execution_time("Filter Orders by Customer ID", execution_time)

    return jsonify(response['Items'])



# Function to log execution time to a file
def log_execution_time(query_name, execution_time):
    with open('query_time.txt', 'a') as f:
        f.write(f"{query_name}: {execution_time:.4f} seconds\n")

# Serve the index.html file
@app.route('/')
def home():
    return render_template('index.html')

# Main entry point
if __name__ == '__main__':

  app.run(debug=True)