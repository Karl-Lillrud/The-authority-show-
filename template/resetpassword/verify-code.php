<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "login";

$conn = new mysqli($servername, $username, $password, $dbname);

<<<<<<< HEAD
if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $email = isset($_POST['email']) ? trim($_POST['email']) : null;

    if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        die("Invalid email address.");
    }

    // Skapa en unik kod och sätt en utgångstid
    $code = bin2hex(random_bytes(4)); // Genererar en 8 tecken lång kod
    $expires_at = date("Y-m-d H:i:s", strtotime("+10 minutes"));

    // Kontrollera om email redan finns i password_resets-tabellen
    $check_sql = "SELECT * FROM password_resets WHERE email = ?";
    $check_stmt = $conn->prepare($check_sql);
    $check_stmt->bind_param("s", $email);
    $check_stmt->execute();
    $check_result = $check_stmt->get_result();

    if ($check_result->num_rows > 0) {
        // Uppdatera kod och utgångstid om posten redan finns
        $update_sql = "UPDATE password_resets SET code = ?, expires_at = ? WHERE email = ?";
        $update_stmt = $conn->prepare($update_sql);
        $update_stmt->bind_param("sss", $code, $expires_at, $email);
        $update_stmt->execute();
    } else {
        // Infoga ny post om email inte finns
        $insert_sql = "INSERT INTO password_resets (email, code, created_at, expires_at) VALUES (?, ?, NOW(), ?)";
        $insert_stmt = $conn->prepare($insert_sql);
        if (!$insert_stmt) {
            die("SQL prepare error: " . $conn->error);
        }
        $insert_stmt->bind_param("sss", $email, $code, $expires_at);
        $insert_stmt->execute();
    }

    // Bekräftelsemeddelande
    echo "Reset code sent to $email! Code: $code (expires in 10 minutes)";

    // Debug-log för att verifiera tiden (kan tas bort i produktion)
    error_log("Code: $code, Expires at: $expires_at");
}
=======
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
>>>>>>> 1197087 (uppdaterade. ändra inte sökvägarna.)
?>
