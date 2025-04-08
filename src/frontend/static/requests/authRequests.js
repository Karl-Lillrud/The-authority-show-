export async function signin(email, password, remember) {
  try {
    const response = await fetch(`/signin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, remember })
    });

    if (!response.ok) {
      throw new Error("Invalid email or password.");
    }

    const result = await response.json();
    return result.redirect_url || "/dashboard";
  } catch (error) {
    throw new Error(error.message);
  }
}

export async function register(email, password) {
  // Validate required parameters
  if (!email || !password) {
    throw new Error("Email and password are required.");
  }

  try {
    const response = await fetch(`/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (response.ok) {
      // Automatically log in the user
      const loginResponse = await fetch(`/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!loginResponse.ok) {
        throw new Error("Registration successful, but failed to log in.");
      }

      const loginResult = await loginResponse.json();
      return loginResult.redirect_url || "/dashboard";
    } else {
      const result = await response.json();
      if (result.error === "User already exists") {
        throw new Error("User already exists");
      } else {
        throw new Error(result.error || "An error occurred. Please try again.");
      }
    }
  } catch (error) {
    throw new Error(error.message);
  }
}

export async function registerTeamMember(
  email,
  password,
  fullName,
  phone,
  inviteToken
) {
  try {
    const response = await fetch(`/register-team-member`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, fullName, phone, inviteToken }) // Include invite token
    });

    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.error || "Failed to register.");
    }

    const result = await response.json();

    // If registration is successful, automatically redirect
    return result.redirect_url || "/dashboard";
  } catch (error) {
    throw new Error(error.message);
  }
}

export async function sendVerificationCode(email) {
<<<<<<< HEAD
<<<<<<< HEAD
  const response = await fetch("/send-verification-code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return response.json();
=======
=======
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
  try {
    const response = await fetch("/send-verification-code", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || "Failed to send verification code.");
    }

<<<<<<< HEAD
    return await response.json();
=======
    const result = await response.json();

    // Ensure the function only throws an error for actual failures
    if (result.success === false) {
      throw new Error(result.message || "Failed to send verification code.");
    }

    // Return the success response
    return result;
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
  } catch (error) {
    console.error("Error in sendVerificationCode:", error);
    throw error;
  }
<<<<<<< HEAD
>>>>>>> parent of 003dcac05 (Add verification form and enhance sign-in process with improved error handling and code structure)
=======
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
}

export async function loginWithVerificationCode(email, code) {
  const response = await fetch("/login-with-code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, code }),
  });
  return response.json();
<<<<<<< HEAD
}
<<<<<<< HEAD

export async function sendVerificationCode(email) {
  const response = await fetch("/verification/send-verification-code", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const result = await response.json();
    throw new Error(result.error || "Failed to send verification code.");
  }

  return response.json();
}

=======
>>>>>>> parent of 9490424b6 (Refactor authentication flow: update client secrets, enhance verification code handling, and improve error handling in sendVerificationCode function)
=======
}
>>>>>>> parent of 295f9066f (Implement email verification feature with code generation and validation)
