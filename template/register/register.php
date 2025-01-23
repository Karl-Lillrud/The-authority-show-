<?php
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
        header("Location: /waitinglist/index.html");
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
