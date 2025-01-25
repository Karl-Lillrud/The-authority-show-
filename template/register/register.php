<?php
<<<<<<< HEAD
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
=======
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = $_POST['email'];
    $password = $_POST['password'];

    // Example database connection
    $servername = "localhost"; // Replace with your database server
    $username = "root"; // Replace with your database username
    $db_password = ""; // Replace with your database password
    $dbname = "mydatabase"; // Replace with your database name

    // Create connection
    $conn = new mysqli($servername, $username, $db_password, $dbname);

    // Check connection
    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // Insert into the database
    $stmt = $conn->prepare("INSERT INTO users (email, password) VALUES (?, ?)");
    $stmt->bind_param("ss", $email, password_hash($password, PASSWORD_DEFAULT)); // Hash the password

    if ($stmt->execute()) {
        // Redirect on successful registration
        header("Location: https://devpodmanager.s3.eu-north-1.amazonaws.com/waitinglist/index.html");
        exit();
    } else {
        echo "Error: " . $stmt->error;
    }

    $stmt->close();
    $conn->close();
} else {
    echo "Invalid request method.";
}
?>
>>>>>>> d113c0a624dbeaa8c294e4553dd5fc53c65d58c6
