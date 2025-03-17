export async function getEmail() {
    try {
      const response = await fetch(`/get_email`, {
        method: "GET",
        headers: { "Content-Type": "application/json" }
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