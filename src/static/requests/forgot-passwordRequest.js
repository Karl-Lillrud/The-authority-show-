document
  .getElementById("forgotPasswordForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();
    const email = document.getElementById("email").value.trim();

    fetch("/forgotpassword", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email: email })
    })
      .then((response) => response.json())
      .then((data) => {
        alert(data.message || data.error);
        if (data.redirect_url) {
          window.location.href =
            data.redirect_url + "?email=" + encodeURIComponent(email);
        }
      })
      .catch((error) => console.error("Error:", error));
  });
