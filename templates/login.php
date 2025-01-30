<?php
session_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Load Composer's autoloader
require '../vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;

// Configuration Variables
$cosmosEndpoint = "https://cosmosdbservice.documents.azure.com:443/";
$cosmosKey = "K9RahnO3WSXA6P1UaWu4RJOLmSwXweeVFqTrt6L6JBvVfFoMGRG4VaxqzzMcDEJTYuJ8P32Og0KbACDbOaVVLg==";
$databaseName = "PodManagerDb";
$containerName = "Main";
$cosmosApiVersion = "2018-12-31";

// Function to generate the Cosmos DB authorization token
function generateAuthToken($verb, $resourceType, $resourceId, $date, $key, $keyType = 'master', $tokenVersion = '1.0') {
    $masterKey = base64_decode($key);
    $text = strtolower($verb) . "\n" .
            strtolower($resourceType) . "\n" .
            strtolower($resourceId) . "\n" .
            strtolower($date) . "\n" .
            "\n";
    $signature = hash_hmac('sha256', $text, $masterKey, true);
    $base64EncodedSignature = base64_encode($signature);
    return urlencode("type=$keyType&ver=$tokenVersion&sig=$base64EncodedSignature");
}

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    // Retrieve and sanitize user inputs
    $email = filter_var(trim($_POST['email']), FILTER_SANITIZE_EMAIL);
    $password = trim($_POST['password']);

    if (!empty($email) && !empty($password)) {
        // Initialize Guzzle HTTP client
        $client = new Client([
            'base_uri' => $cosmosEndpoint,
            'headers' => [
                'Content-Type' => 'application/query+json',
                'Accept' => 'application/json',
                'x-ms-version' => $cosmosApiVersion,
                'x-ms-date' => gmdate("D, d M Y H:i:s T"),
            ]
        ]);

        // Define the SQL query to find the user by email
        $sqlQuery = [
            "query" => "SELECT c.password, c.id, c.email FROM c WHERE c.email = @email",
            "parameters" => [
                [
                    "name" => "@email",
                    "value" => $email
                ]
            ]
        ];

        // Convert query to JSON
        $queryJson = json_encode($sqlQuery);

        // Generate the authorization token
        $verb = "POST";
        $resourceType = "docs";
        $resourceId = "dbs/$databaseName/colls/$containerName";
        $date = gmdate("D, d M Y H:i:s T");
        $authToken = generateAuthToken($verb, $resourceType, $resourceId, $date, $cosmosKey);

        // Add the authorization header
        $client = new Client([
            'base_uri' => $cosmosEndpoint,
            'headers' => [
                'Content-Type' => 'application/query+json',
                'Accept' => 'application/json',
                'x-ms-version' => $cosmosApiVersion,
                'x-ms-date' => $date,
                'Authorization' => $authToken
            ]
        ]);

        try {
            // Execute the query
            $response = $client->post("dbs/$databaseName/colls/$containerName/docs", [
                'body' => $queryJson
            ]);

            // Parse the response
            $responseBody = json_decode($response->getBody(), true);
            $results = $responseBody['Documents'];

            if (count($results) > 0) {
                $user = $results[0];
                if (password_verify($password, $user['password'])) {
                    // Set session variables
                    $_SESSION['user_id'] = $user['id'];
                    $_SESSION['email'] = $user['email'];

                    // Redirect to dashboard
                    header("Location: dashboard/dashboard.html");
                    exit();
                }
            }

            // Redirect back to login with error if authentication fails
            header("Location: index.html?error=1");
            exit();

        } catch (RequestException $e) {
            // Log the error message (you can implement a logging mechanism here)
            error_log("Cosmos DB Request Exception: " . $e->getMessage());

            // Redirect back to login with error
            header("Location: index.html?error=1");
            exit();
        }
    }

    // Redirect back to login with error if inputs are empty
    header("Location: index.html?error=1");
    exit();
}
?>
