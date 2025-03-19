export function forgotPasswordRequest(email) {
  return fetch("/forgotpassword", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  }).then((res) => res.json());
}

export function enterCodeRequest(email, code) {
  return fetch("/enter-code", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, code }),
  }).then((res) => res.json());
}

export function resendCodeRequest(email) {
  return fetch("/resend-code", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email }),
  }).then((res) => res.json());
}

export function resetPasswordRequest(email, password) {
  return fetch("/reset-password", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
  }).then((res) => res.json());
}
