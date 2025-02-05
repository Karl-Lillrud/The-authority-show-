<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

require __DIR__ . 'https://devpodmanager.s3.eu-north-1.amazonaws.com/vendor/autoload.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email'] ?? '');

    if (empty($email) || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
        http_response_code(400);
        die("Invalid email address.");
    }

    $mail = new PHPMailer(true);

    try {
        $mail->isSMTP();
        $mail->Host = 'smtp.gmail.com';
        $mail->SMTPAuth = true;
        $mail->Username = 'theauthorityshowpodcast@gmail.com'; // Din e-postadress
        $mail->Password = 'tmbqtzjfehivbrnk'; // Gmail app-lösenord
        $mail->SMTPSecure = PHPMailer::ENCRYPTION_STARTTLS;
        $mail->Port = 587;

        $mail->setFrom('theauthorityshowpodcast@gmail.com', 'Podcast Manager');
        $mail->addAddress($email);

        $mail->isHTML(true);
        $mail->Subject = "🌟 You've Been Invited!";
        $mail->Body = "
            <p>Hi,</p>
            <p>I've discovered this incredible service that helps me produce my podcast and it actually gives me back time every day. I think you'll find it just as beneficial!</p>
            <p>By joining through this invitation, you'll start with an extra 1,000 credits absolutely free. These credits can significantly enhance your experience and offer immediate benefits as soon as you gain access.</p>
            <p>Simply click the link below to sign up and claim your bonus:</p>
            <p><a href='https://podmanager.ai/signup'>https://podmanager.ai/signup</a></p>
            <p>Let's make the most of every day, together!</p>
            <p>See you there,</p>
        ";

        $mail->send();
        echo "Invitation email sent successfully!";
    } catch (Exception $e) {
        http_response_code(500);
        echo "Failed to send email. Error: {$mail->ErrorInfo}";
    }
} else {
    http_response_code(405);
    echo "Invalid request method.";
}
?>
