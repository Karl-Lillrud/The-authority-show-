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
    $token = $_POST['token'];
    $password = $_POST['password'];
    $confirm_password = $_POST['confirm_password'];

    if ($password !== $confirm_password) {
        echo "<script>
                alert('Passwords do not match.');
                window.history.back();
              </script>";
        exit;
    }

    // Hämta användarens e-postadress baserat på token
    $sql = "SELECT email FROM password_resets WHERE token = ?";
    $stmt = $conn->prepare($sql);
    if (!$stmt) {
        die("SQL error: " . $conn->error);
    }
    $stmt->bind_param("s", $token);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows === 0) {
        echo "<script>
                alert('Invalid or expired token.');
                window.location.href = '../index.html';
              </script>";
        exit;
    }

    $row = $result->fetch_assoc();
    $email = $row['email'];

    // Uppdatera lösenordet
    $hashed_password = password_hash($password, PASSWORD_BCRYPT);
    $update_sql = "UPDATE users SET password = ? WHERE email = ?";
    $update_stmt = $conn->prepare($update_sql);
    $update_stmt->bind_param("ss", $hashed_password, $email);
    if (!$update_stmt->execute()) {
        die("Error updating password: " . $update_stmt->error);
    }

    // Ta bort återställningstoken
    $delete_sql = "DELETE FROM password_resets WHERE token = ?";
    $delete_stmt = $conn->prepare($delete_sql);
    $delete_stmt->bind_param("s", $token);
    $delete_stmt->execute();

    // Omdirigera med ett meddelande
    echo "<script>
            alert('Password has been reset successfully.');
            window.location.href = '../index.html';
          </script>";
    exit;
}

$conn->close();
?>
