<?php
if (!isset($_GET['token'])) {
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
    <div class="container">
        <h1>Reset Password</h1>
        <form id="reset-password-form" action="update-password.php" method="POST">
            <input type="hidden" name="token" value="<?php echo htmlspecialchars($token); ?>">
            <div class="input-group">
                <label for="password">New Password:</label>
                <input type="password" id="password" name="password" placeholder="Enter your new password" required>
            </div>
            <button type="submit" class="button">Reset Password</button>
        </form>
    </div>
</body>
</html>
