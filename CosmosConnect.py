from azure.cosmos import CosmosClient, PartitionKey

# Replace with your connection details
endpoint = "https://cosmosdbservice.documents.azure.com:443/;AccountKey=K9RahnO3WSXA6P1UaWu4RJOLmSwXweeVFqTrt6L6JBvVfFoMGRG4VaxqzzMcDEJTYuJ8P32Og0KbACDbOaVVLg==;"
key = "K9RahnO3WSXA6P1UaWu4RJOLmSwXweeVFqTrt6L6JBvVfFoMGRG4VaxqzzMcDEJTYuJ8P32Og0KbACDbOaVVLg"

# Initialize client
client = CosmosClient(endpoint, key)

# Access database and container
database_name = 'PodcastDb'
container_name = 'MainContainer'
database = client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/type"),
    offer_throughput=400
)

# Add an item
item = {
    'id': '1',
    'partitionKey': 'example',
    'name': 'Azure Cosmos DB Demo'
}
container.create_item(body=item)

print("Item added successfully!")