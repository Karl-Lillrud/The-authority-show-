<?php
require 'vendor/autoload.php';

use Microsoft\Azure\Cosmos\ClientBuilder;
use Microsoft\Azure\Cosmos\Exception\CosmosException;

// Azure Cosmos DB configuration
$endpoint = 'Key here';
$key = 'Key here';
$databaseName = 'cosmosdbservice';
$containerName = 'MainContainer';

// Initialize Cosmos DB client
$client = ClientBuilder::create($endpoint, $key)->build();
$container = $client->getContainer($databaseName, $containerName);

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = htmlspecialchars($_POST['name']);
    $email = htmlspecialchars($_POST['email']);
    $password = htmlspecialchars($_POST['password']);

    // Basic input validation
    if (empty($name) || empty($email) || empty($password)) {
        echo json_encode(['success' => false, 'message' => 'All fields are required.']);
        exit;
    }

    // Hash the password
    $passwordHash = password_hash($password, PASSWORD_BCRYPT);

    try {
        // Check if the user already exists
        $query = "SELECT * FROM Users u WHERE u.email = @email";
        $queryOptions = [
            'parameters' => [
                ['name' => '@email', 'value' => $email]
            ]
        ];
        $existingUser = $container->queryItems($query, $queryOptions, true);

        if ($existingUser->isNotEmpty()) {
            echo json_encode(['success' => false, 'message' => 'Email already registered.']);
            exit;
        }

        // Create user document
        $userDocument = [
            'id' => uniqid(), // Unique ID for the user
            'name' => $name,
            'email' => $email,
            'passwordHash' => $passwordHash,
            'createdAt' => date('Y-m-d\TH:i:s\Z')
        ];

        // Insert the document into Cosmos DB
        $container->createItem($userDocument);

        echo json_encode(['success' => true, 'message' => 'Registration successful.']);
    } catch (CosmosException $e) {
        // Handle errors
        echo json_encode(['success' => false, 'message' => 'An error occurred: ' . $e->getMessage()]);
    }
}
?>