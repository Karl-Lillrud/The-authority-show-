document.addEventListener("DOMContentLoaded", function () {
  const successMessage = document.getElementById("success-message");
  const errorMessage = document.getElementById("error-message");
  const sendLoginLinkButton = document.getElementById("send-login-link-button");
  const emailInput = document.getElementById("email");
  const languageSelect = document.getElementById("language-select");
  const centerBox = document.querySelector(".center-box");

  // Set initial language from localStorage or browser preference
  const savedLanguage = localStorage.getItem("preferredLanguage");
  const browserLanguage = navigator.language.split("-")[0];
  const initialLanguage = savedLanguage || browserLanguage || "en";
  
  if (languageSelect) {
    languageSelect.value = initialLanguage;
    document.documentElement.lang = initialLanguage;
    setDirectionForLanguage(initialLanguage);
  }

  // Handle language change
  languageSelect.addEventListener("change", function(e) {
    const selectedLanguage = e.target.value;
    document.documentElement.lang = selectedLanguage;
    localStorage.setItem("preferredLanguage", selectedLanguage);
    
    // Update text content and direction
    setDirectionForLanguage(selectedLanguage);
    updatePageContent(selectedLanguage);
  });

  // Function to set RTL/LTR direction
  function setDirectionForLanguage(lang) {
    const isRTL = lang === 'ar';
    document.documentElement.dir = isRTL ? 'rtl' : 'ltr';
    centerBox.style.left = isRTL ? 'auto' : '2%';
    centerBox.style.right = isRTL ? '2%' : 'auto';
  }

  function updatePageContent(lang) {
    const translations = {
      en: {
        title: "Sign In",
        emailPlaceholder: "Email",
        buttonText: "Send Log-In Link",
        termsText: "Terms of Service",
        privacyText: "Privacy Policy",
        successMessage: "Login link has been sent to your email!",
        errorMessage: "Failed to send login link. Please try again later."
      },
      ar: {
        title: "تسجيل الدخول",
        emailPlaceholder: "البريد الإلكتروني",
        buttonText: "إرسال رابط تسجيل الدخول",
        termsText: "شروط الخدمة",
        privacyText: "سياسة الخصوصية",
        successMessage: "تم إرسال رابط تسجيل الدخول إلى بريدك الإلكتروني!",
        errorMessage: "فشل في إرسال الرابط. يرجى المحاولة مرة أخرى لاحقاً."
      },
      sv: {
        title: "Logga in",
        emailPlaceholder: "E-post",
        buttonText: "Skicka inloggningslänk",
        termsText: "Användarvillkor",
        privacyText: "Integritetspolicy",
        successMessage: "Inloggningslänk har skickats till din e-post!",
        errorMessage: "Misslyckades att skicka inloggningslänk. Försök igen senare."
      },
      es: {
        title: "Iniciar sesión",
        emailPlaceholder: "Correo electrónico",
        buttonText: "Enviar enlace de inicio de sesión",
        termsText: "Términos de servicio",
        privacyText: "Política de privacidad",
        successMessage: "¡Se ha enviado el enlace de inicio de sesión a tu correo!",
        errorMessage: "Error al enviar el enlace. Por favor, inténtalo más tarde."
      },
      fr: {
        title: "Se connecter",
        emailPlaceholder: "Email",
        buttonText: "Envoyer le lien de connexion",
        termsText: "Conditions d'utilisation",
        privacyText: "Politique de confidentialité",
        successMessage: "Le lien de connexion a été envoyé à votre email !",
        errorMessage: "Échec de l'envoi du lien. Veuillez réessayer plus tard."
      },
      de: {
        title: "Anmelden",
        emailPlaceholder: "E-Mail",
        buttonText: "Anmelde-Link senden",
        termsText: "Nutzungsbedingungen",
        privacyText: "Datenschutzrichtlinie",
        successMessage: "Anmelde-Link wurde an Ihre E-Mail gesendet!",
        errorMessage: "Fehler beim Senden des Links. Bitte versuchen Sie es später erneut."
      },
      it: {
        title: "Accedi",
        emailPlaceholder: "Email",
        buttonText: "Invia link di accesso",
        termsText: "Termini di servizio",
        privacyText: "Politica sulla privacy",
        successMessage: "Il link di accesso è stato inviato alla tua email!",
        errorMessage: "Impossibile inviare il link. Per favore riprova più tardi."
      },
      pt: {
        title: "Entrar",
        emailPlaceholder: "Email",
        buttonText: "Enviar link de login",
        termsText: "Termos de serviço",
        privacyText: "Política de privacidade",
        successMessage: "O link de login foi enviado para seu email!",
        errorMessage: "Falha ao enviar o link. Por favor, tente novamente mais tarde."
      },
      ru: {
        title: "Вход",
        emailPlaceholder: "Электронная почта",
        buttonText: "Отправить ссылку для входа",
        termsText: "Условия использования",
        privacyText: "Политика конфиденциальности",
        successMessage: "Ссылка для входа отправлена на вашу почту!",
        errorMessage: "Не удалось отправить ссылку. Пожалуйста, попробуйте позже."
      },
      zh: {
        title: "登录",
        emailPlaceholder: "电子邮箱",
        buttonText: "发送登录链接",
        termsText: "服务条款",
        privacyText: "隐私政策",
        successMessage: "登录链接已发送至您的邮箱！",
        errorMessage: "发送链接失败，请稍后重试。"
      },
      ja: {
        title: "ログイン",
        emailPlaceholder: "メールアドレス",
        buttonText: "ログインリンクを送信",
        termsText: "利用規約",
        privacyText: "プライバシーポリシー",
        successMessage: "ログインリンクをメールに送信しました！",
        errorMessage: "リンクの送信に失敗しました。後でもう一度お試しください。"
      },
      ko: {
        title: "로그인",
        emailPlaceholder: "이메일",
        buttonText: "로그인 링크 보내기",
        termsText: "서비스 약관",
        privacyText: "개인정보 처리방침",
        successMessage: "로그인 링크가 이메일로 전송되었습니다!",
        errorMessage: "링크 전송에 실패했습니다. 나중에 다시 시도해주세요."
      }
    };

    const t = translations[lang] || translations.en;
    
    // Update page content
    document.querySelector(".title").textContent = t.title;
    emailInput.placeholder = t.emailPlaceholder;
    sendLoginLinkButton.textContent = t.buttonText;
    
    // Update links text
    const links = document.querySelectorAll(".policy-links .link");
    links[0].textContent = t.termsText;
    links[1].textContent = t.privacyText;
  }

  // Handle "Send Log-In Link" button click
  if (sendLoginLinkButton) {
    sendLoginLinkButton.addEventListener("click", async function () {
      const email = emailInput.value.trim();
      const currentLang = languageSelect.value;
      const t = translations[currentLang] || translations.en;

      if (!email) {
        errorMessage.textContent = "Please enter your email address.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
        return;
      }

      try {
        const response = await fetch("/send-login-link", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email })
        });

        const result = await response.json();
        if (response.ok) {
          successMessage.textContent = t.successMessage;
          successMessage.style.display = "block";
          errorMessage.style.display = "none";
        } else {
          errorMessage.textContent = t.errorMessage;
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Error sending login link:", error);
        errorMessage.textContent = t.errorMessage;
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Send login link button not found in DOM");
  }

  // Handle token-based login from URL
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (token) {
    // Automatically log in the user using the token
    fetch("/verify-login-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        token,
        language: languageSelect.value // Include selected language
      })
    })
      .then(async (response) => {
        if (!response.ok) {
          const result = await response.json();
          throw new Error(
            `HTTP error! Status: ${response.status}, Message: ${
              result.error || "Unknown error"
            }`
          );
        }
        return response.json();
      })
      .then((data) => {
        if (data.redirect_url) {
          // Store language preference before redirecting
          localStorage.setItem("preferredLanguage", languageSelect.value);
          window.location.href = data.redirect_url;
        } else {
          errorMessage.textContent = data.error || "Failed to log in with the provided link.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      })
      .catch((error) => {
        console.error("Error verifying token:", error);
        const errorMsg = error.message.toLowerCase();
        if (errorMsg.includes("failed to create account")) {
          errorMessage.textContent = "Failed to create account. Please check your email or contact support.";
        } else if (errorMsg.includes("token has expired")) {
          errorMessage.textContent = "Login link has expired. Please request a new one.";
        } else if (errorMsg.includes("invalid token")) {
          errorMessage.textContent = "Invalid login link. Please try with a new link.";
        } else {
          errorMessage.textContent = "An error occurred during login. Please try again or contact support.";
        }
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      });
  }

  // Handle email/password login form (if used)
  const form = document.getElementById("signin-form");
  if (form) {
    form.addEventListener("submit", async function (event) {
      event.preventDefault();

      const email = emailInput.value.trim();
      const password = document.getElementById("password")?.value?.trim();

      if (!email || (password !== undefined && !password)) {
        errorMessage.textContent = "Vänligen ange både e-post och lösenord.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
        return;
      }

      try {
        const response = await fetch("/signin", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, password })
        });

        const result = await response.json();
        if (response.ok) {
          window.location.href = result.redirect_url || "/podprofile";
        } else {
          errorMessage.textContent =
            result.error || "Misslyckades att logga in. Försök igen.";
          errorMessage.style.display = "block";
          successMessage.style.display = "none";
        }
      } catch (error) {
        console.error("Fel under inloggning:", error);
        errorMessage.textContent = "Ett fel uppstod. Försök igen.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    });
  } else {
    console.warn("Inloggningsformulär hittades inte i DOM");
  }

  // Handle OTP verification
  const verifyOTP = async (email, otp) => {
    const currentLang = languageSelect.value;
    try {
      const response = await fetch("/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          email, 
          otp,
          language: currentLang // Include current language
        })
      });

      const result = await response.json();
      if (response.ok) {
        // Store language preference before redirecting
        localStorage.setItem("preferredLanguage", currentLang);
        window.location.href = result.redirect_url || "/podprofile";
      } else {
        errorMessage.textContent = result.error || "Failed to verify OTP. Please try again.";
        errorMessage.style.display = "block";
        successMessage.style.display = "none";
      }
    } catch (error) {
      console.error("Error verifying OTP:", error);
      errorMessage.textContent = "An error occurred. Please try again.";
      errorMessage.style.display = "block";
      successMessage.style.display = "none";
    }
  };
});
