<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require __DIR__ . '/../../vendor/autoload.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

$servername = "localhost";
$username = "root";
$password = "";
$dbname = "login";

$conn = new mysqli($servername, $username, $password, $dbname);

if ($_SERVER["REQUEST_METHOD"] === "POST") {
    $email = trim($_POST['email']);

    if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        die("Invalid email address.");
    }

    // Kontrollera om e-posten finns i databasen
    $sql = "SELECT * FROM users WHERE email = ?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("s", $email);
    $stmt->execute();
    $result = $stmt->get_result();

    if ($result->num_rows > 0) {
        // Skapa en unik kod och token
        $code = random_int(100000, 999999); // 6-siffrig kod
        $token = bin2hex(random_bytes(32));
        $expires_at = date("Y-m-d H:i:s", strtotime("+1 hour"));

        // Lägg till kod och token i databasen
        $sql = "INSERT INTO password_resets (email, code, token, expires_at) VALUES (?, ?, ?, ?)";
        $stmt = $conn->prepare($sql);
        $stmt->bind_param("ssss", $email, $code, $token, $expires_at);
        $stmt->execute();

        // Förbered återställningslänk
        $reset_link = "http://localhost/PodManager/template/reset-password.php?token=" . $token;

        // Skicka e-post med PHPMailer
        $mail = new PHPMailer(true);

        try {
            // Serverinställningar
            $mail->isSMTP();
            $mail->Host = 'smtp.gmail.com';
            $mail->SMTPAuth = true;
            $mail->Username = 'theauthorityshowpodcast@gmail.com'; // Din e-post
            $mail->Password = 'tmbqtzjfehivbrnk'; // Gmail app-lösenord
            $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
            $mail->Port = 587;

            // Mottagare
            $mail->setFrom('theauthorityshowpodcast@gmail.com', 'Podcast Manager');
            $mail->addAddress($email);

            // Innehåll
            $mail->isHTML(true);
            $mail->Subject = 'Password Reset Request';
            $mail->Body = "
                <p>You requested a password reset. Use the code below or click the link to reset your password:</p>
                <p><strong>Reset Code: $code</strong></p>
                <p>Or click the link: <a href='$reset_link'>$reset_link</a></p>
                <p>If you did not request this, please ignore this email.</p>
            ";

            $mail->send();
            echo "<script>
                    alert('Password reset email sent with a reset code. Check your inbox.');
                    window.location.href = 'enter-code.html';
                  </script>";
        } catch (Exception $e) {
            echo "<script>
                    alert('Failed to send reset email. Error: {$mail->ErrorInfo}');
                    window.location.href = '../index.html';
                  </script>";
        }
    } else {
        echo "<script>
                alert('Email not found.');
                window.location.href = '../index.html';
              </script>";
    }
}
?>
