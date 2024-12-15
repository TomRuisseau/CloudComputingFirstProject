from flask import Flask, jsonify, request, render_template
from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv
from flasgger import Swagger
import os

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)
app.config['SWAGGER'] = {
    'title': 'Shop WebApp API',
    'version': '0.1.0',
    'description': 'API documentation for the Shop WebApp, providing endpoints for items, users, and baskets.',
    'specs_route': '/',
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Shop WebApp API",
        "description": "API documentation for the Shop WebApp, providing endpoints for items, users, and baskets.",
        "version": "0.1.0"
    },
    "tags": [
        {"name": "Users", },
        {"name": "Items", },
        {"name": "Baskets", },
        {"name": "Clear Database", },
    ],
}
swagger = Swagger(app, template=swagger_template)

# Cosmos DB configuration
COSMOS_ENDPOINT = "https://taume-cosmos-account.documents.azure.com:443/"
COSMOS_KEY = "NlKPDtH2WuKJkpAvO5HCUh4VG7fAo6feVHWm8HO4vZtdNgyke8EvcaHQatfigUV4yZsptuxWmOweACDbsdVqjw=="
DATABASE_NAME = "taumedatabase"
ITEMS_CONTAINER = "items"
USERS_CONTAINER = "users"
BASKETS_CONTAINER = "baskets"

# Validate environment variables
if not COSMOS_ENDPOINT or not COSMOS_KEY:
    raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set in the .env file")

# Cosmos DB client and database
client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = client.create_database_if_not_exists(DATABASE_NAME)

# Create containers
items_container = database.create_container_if_not_exists(
    id=ITEMS_CONTAINER,
    partition_key=PartitionKey(path="/category"),
    offer_throughput=400
)
users_container = database.create_container_if_not_exists(
    id=USERS_CONTAINER,
    partition_key=PartitionKey(path="/user_id"),
    offer_throughput=400
)
baskets_container = database.create_container_if_not_exists(
    id=BASKETS_CONTAINER,
    partition_key=PartitionKey(path="/user_id"),
    offer_throughput=400
)

# Clear Database route

@app.route('/clear', methods=['DELETE'])
def clear_containers():
    """
    Delete all items from all containers.
    ---
    tags:
      - "Clear Database"
    responses:
      200:
        description: All containers have been cleared.
    """
    # Delete items from items_container
    for item in items_container.query_items(
        query="SELECT * FROM items",
        enable_cross_partition_query=True
    ):
        items_container.delete_item(item, partition_key=item['category'])

    # Delete items from users_container
    for user in users_container.query_items(
        query="SELECT * FROM users",
        enable_cross_partition_query=True
    ):
        users_container.delete_item(user, partition_key=user['user_id'])

    # Delete items from baskets_container
    for basket in baskets_container.query_items(
        query="SELECT * FROM baskets",
        enable_cross_partition_query=True 
    ):
        baskets_container.delete_item(basket, partition_key=basket['user_id'])

    return jsonify({"message": "All containers have been cleared."}), 200

# Create User route

@app.route('/users', methods=['POST'])
def add_user():
    """
    Add a new user.
    ---
    tags:
      - "Users"
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            id:
              type: string
              example: "456"
            user_id:
              type: string
              example: "user123"
            name:
              type: string
              example: "John Doe"
    responses:
      200:
        description: User added successfully
    """
    data = request.get_json()
    users_container.upsert_item(data)
    return jsonify({"message": "User added successfully", "user": data}), 200

# Get Users route

@app.route('/users', methods=['GET'])
def get_users():
    """
    Retrieve all users.
    ---
    tags:
      - "Users"
    responses:
      200:
        description: List of users
    """
    query = "SELECT * FROM users"
    users = list(users_container.query_items(query=query, enable_cross_partition_query=True))
    return jsonify(users)

# Create Item route

@app.route('/items', methods=['POST'])
def add_item():
    """
    Add a new item.
    ---
    tags:
      - "Items"
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            id:
              type: string
              example: "123"
            name:
              type: string
              example: "Smartphone"
            category:
              type: string
              example: "electronics"
            price:
              type: number
              example: 299.99
    responses:
      200:
        description: Item added successfully
    """
    data = request.get_json()
    items_container.upsert_item(data)
    return jsonify({"message": "Item added successfully", "item": data}), 200

# Get Items route

@app.route('/items', methods=['GET'])
def get_items():
    """
    Retrieve all items.
    ---
    tags:
      - "Items"
    responses:
      200:
        description: List of items
    """
    query = "SELECT * FROM items"
    items = list(items_container.query_items(query=query, enable_cross_partition_query=True))
    return jsonify(items)

# Create Basket route

@app.route('/baskets', methods=['POST'])
def add_basket():
    """
    Add a new basket.
    ---
    tags:
      - "Baskets"
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            id:
              type: string
              example: "789"
            user_id:
              type: string
              example: "user123"
            items:
              type: array
              items:
                type: object
                properties:
                  item_id:
                    type: string
                    example: "123"
                  quantity:
                    type: integer
                    example: 2
    responses:
      200:
        description: Basket added successfully
    """
    data = request.get_json()
    baskets_container.upsert_item(data)
    return jsonify({"message": "Basket added successfully", "basket": data}), 200

# Get Baskets route

@app.route('/baskets', methods=['GET'])
def get_baskets():
    """
    Retrieve all baskets.
    ---
    tags:
      - "Baskets"
    responses:
      200:
        description: List of baskets
    """
    query = "SELECT * FROM baskets"
    baskets = list(baskets_container.query_items(query=query, enable_cross_partition_query=True))
    return jsonify(baskets)

# Get Basket by User ID route

@app.route('/baskets/<user_id>', methods=['GET'])
def get_basket(user_id):
    """
    Retrieve a basket by user ID.
    ---
    tags:
      - "Baskets"
    parameters:
      - name: user_id
        in: path
        required: true
        type: string
        example: "user123"
    responses:
      200:
        description: Basket retrieved successfully
    """
    query = f"SELECT * FROM baskets b WHERE b.user_id = '{user_id}'"
    basket = list(baskets_container.query_items(query=query, enable_cross_partition_query=True))
    return jsonify(basket)

# Run the app
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
