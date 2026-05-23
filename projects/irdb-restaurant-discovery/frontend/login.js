import { api } from "./common.js";

const loginForm = document.getElementById("loginForm");
const loginMsg = document.getElementById("msg");

function setLoginMsg(msg) {
  if (loginMsg) loginMsg.textContent = msg;
}

if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    setLoginMsg("Logging in...");

    try {
      const loginResult = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      const role = loginResult?.role;
      setLoginMsg(`Welcome ${role || "user"} - redirecting...`);

      if (role === "admin") {
        window.location.assign("/admin/admin-queue");
      } else if (role === "restaurant") {
        window.location.assign("/restaurant-portal");
      } else {
        window.location.assign("/discovery");
      }
    } catch (err) {
      setLoginMsg(err.message || "Login failed");
    }
  });
}

const registerForm = document.getElementById("registerForm");
const registerMsg = document.getElementById("r_msg");

function setRegisterMsg(msg) {
  if (registerMsg) registerMsg.textContent = msg;
}

if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("r_email").value.trim();
    const password = document.getElementById("r_password").value;

    setRegisterMsg("Creating account...");

    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      });

      setRegisterMsg("Account created. You can now log in.");

      const loginEmail = document.getElementById("email");
      if (loginEmail) loginEmail.value = email;

      document.getElementById("r_password").value = "";
    } catch (err) {
      setRegisterMsg(err.message || "Registration failed");
    }
  });
}
