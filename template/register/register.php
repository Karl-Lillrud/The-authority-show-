<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Kontrollera att alla fält är ifyllda
    $email = isset($_POST['email']) ? trim($_POST['email']) : null;
    $password = isset($_POST['password']) ? trim($_POST['password']) : null;

    if (empty($email) || empty($password)) {
        echo "All fields are required.";
        exit;
    }

    // Hasha lösenordet
    $hashed_password = password_hash($password, PASSWORD_DEFAULT);

    // Databasanslutning
    $conn = new mysqli("localhost", "root", "", "login");

    if ($conn->connect_error) {
        die("Connection failed: " . $conn->connect_error);
    }

    // Spara användaren i databasen
    $stmt = $conn->prepare("INSERT INTO users (email, password) VALUES (?, ?)");
    $stmt->bind_param("ss", $email, $hashed_password);

    if ($stmt->execute()) {
        // Registreringen lyckades, omdirigera till index.html
        header("Location: ../index.html");
        exit;
    } else {
        echo "Error: " . $stmt->error;
    }

    $stmt->close();
    $conn->close();
}
?>
