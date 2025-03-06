const API_BASE_URL =
  window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
    ? "http://127.0.0.1:8000"
    : "https://app.podmanager.ai"; // Use LOCAL_BASE_URL for localhost and PROD_BASE_URL for production

export async function signin(email, password, remember) {
  try {
    const response = await fetch(`${API_BASE_URL}/signin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, remember }),
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
  try {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (response.ok) {
      return `${API_BASE_URL}/signin?message=Registration successful. Please log in.`;
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

export async function getEmail() {
  try {
    const response = await fetch(`${API_BASE_URL}/get_email`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch email.");
    }

    const result = await response.json();
    return result.email;
  } catch (error) {
    throw new Error(error.message);
  }
}
