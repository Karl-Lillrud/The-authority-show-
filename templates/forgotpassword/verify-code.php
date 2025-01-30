<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "login";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $code = isset($_POST['code']) ? trim($_POST['code']) : null;

    if (empty($code)) {
        die("Invalid code.");
    }

    // Kontrollera om koden finns i databasen och inte har gått ut
    $sql = "SELECT * FROM password_resets WHERE code = ? AND expires_at > NOW()";
    $stmt = $conn->prepare($sql);
    if (!$stmt) {
        die("SQL error: " . $conn->error);
    }
    $stmt->bind_param("s", $code);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();
        $token = $row['token']; // Hämta token från databasen

        // Skicka användaren till reset-password.php med token
        header("Location: reset-password.php?token=" . urlencode($token));
        exit;
    } else {
        echo "<script>
                alert('Invalid or expired code.');
                window.location.href = 'enter-code.html';
              </script>";
    }

    $stmt->close();
}

$conn->close();
?>
