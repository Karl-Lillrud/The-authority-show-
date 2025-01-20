<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "login";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $token = $_POST['token'];
    $new_password = trim($_POST['password']);

    if (empty($new_password)) {
        die("Password is required.");
    }

    // Kontrollera token
    $sql = "SELECT email, expires_at FROM password_resets WHERE token = ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("s", $token);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        $row = $result->fetch_assoc();

        if (strtotime($row['expires_at']) > time()) {
            $email = $row['email'];

            // Uppdatera lösenordet (ingen hashing)
            $sql = "UPDATE users SET password = ? WHERE email = ?";
            $stmt = $conn->prepare($sql);
            $stmt->bind_param("ss", $new_password, $email);
            $stmt->execute();

            // Ta bort token
            $sql = "DELETE FROM password_resets WHERE token = ?";
            $stmt = $conn->prepare($sql);
            $stmt->bind_param("s", $token);
            $stmt->execute();

            echo "Password updated successfully! <a href='index.html'>Login here</a>";
        } else {
            echo "Token has expired.";
        }
    } else {
        echo "Invalid token.";
    }
}
?>
