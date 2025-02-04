<?php
session_start();
error_reporting(E_ALL);
ini_set('display_errors', 1);

// Load Composer's autoloader
require '../vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;
use Dotenv\Dotenv;

// Load environment variables
$dotenv = Dotenv::createImmutable(__DIR__ . '/..');
$dotenv->load();

// Configuration Variables from .env
$cosmosEndpoint = getenv("COSMOS_ENDPOINT");
$cosmosKey = getenv("COSMOS_KEY");
$databaseName = getenv("COSMOS_DATABASE");
$containerName = getenv("COSMOS_CONTAINER");
$cosmosApiVersion = "2018-12-31";

// Function to generate the Cosmos DB authorization token
function generateAuthToken($verb, $resourceType, $resourceId, $date, $key, $keyType = 'master', $tokenVersion = '1.0') {
    $masterKey = base64_decode($key);
    $text = strtolower($verb) . "\n" .
            strtolower($resourceType) . "\n" .
            strtolower($resourceId) . "\n" .
            strtolower($date) . "\n" . "\n";
    $signature = hash_hmac('sha256', $text, $masterKey, true);
    $base64EncodedSignature = base64_encode($signature);
    return urlencode("type=$keyType&ver=$tokenVersion&sig=$base64EncodedSignature");
}

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $email = filter_var(trim($_POST['email']), FILTER_SANITIZE_EMAIL);
    $password = trim($_POST['password']);

    if (!empty($email) && !empty($password)) {
        $client = new Client([
            'base_uri' => $cosmosEndpoint,
            'headers' => [
                'Content-Type' => 'application/query+json',
                'Accept' => 'application/json',
                'x-ms-version' => $cosmosApiVersion,
                'x-ms-date' => gmdate("D, d M Y H:i:s T"),
            ]
        ]);

        $sqlQuery = [
            "query" => "SELECT c.password, c.id, c.email FROM c WHERE c.email = @email",
            "parameters" => [["name" => "@email", "value" => $email]]
        ];
        
        $queryJson = json_encode($sqlQuery);

        $verb = "POST";
        $resourceType = "docs";
        $resourceId = "dbs/$databaseName/colls/$containerName";
        $date = gmdate("D, d M Y H:i:s T");
        $authToken = generateAuthToken($verb, $resourceType, $resourceId, $date, $cosmosKey);

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
            $response = $client->post("dbs/$databaseName/colls/$containerName/docs", ['body' => $queryJson]);
            $responseBody = json_decode($response->getBody(), true);
            $results = $responseBody['Documents'];

            if (count($results) > 0) {
                $user = $results[0];
                if (password_verify($password, $user['password'])) {
                    $_SESSION['user_id'] = $user['id'];
                    $_SESSION['email'] = $user['email'];
                    header("Location: dashboard/dashboard.html");
                    exit();
                }
            }
            header("Location: index.html?error=1");
            exit();
        } catch (RequestException $e) {
            error_log("Cosmos DB Request Exception: " . $e->getMessage());
            header("Location: index.html?error=1");
            exit();
        }
    }
    header("Location: index.html?error=1");
    exit();
}
?>
