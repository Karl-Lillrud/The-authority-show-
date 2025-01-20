<?php
if (!isset($_GET['token']) || empty($_GET['token'])) {
    die("Invalid or missing token.");
}

$token = $_GET['token'];
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Password</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="center-box">
        <h1>Reset Password</h1>
        <form id="reset-password-form" action="update-password.php" method="POST">
            <input type="hidden" name="token" value="<?php echo htmlspecialchars($token); ?>">
            <div class="input-group">
                <label for="password">New Password:</label>
                <input type="password" id="password" name="password" class="input" placeholder="Enter your new password" required>
            </div>
            <div class="input-group">
                <label for="confirm-password">Confirm Password:</label>
                <input type="password" id="confirm-password" name="confirm_password" class="input" placeholder="Confirm your new password" required>
            </div>
            <button type="submit" class="button">Reset Password</button>
        </form>
    </div>
</body>
</html>
