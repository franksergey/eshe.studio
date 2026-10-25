
"use strict";

const LOGIN_URL = "/auth/jwt/login";

function createLoginDialog() {
    const dialog = document.createElement("dialog");
    dialog.id = "login-dialog";

    dialog.innerHTML = `
        <form action="${LOGIN_URL}" method="post"
              enctype="application/x-www-form-urlencoded">
            <h2>Вход</h2>

            <label>
                Имя или почта
                <input name="username" type="text"
                       autocomplete="username" required>
            </label>

            <label>
                Пароль
                <input name="password" type="password"
                       autocomplete="current-password" required>
            </label>

            <p role="alert" aria-live="polite" hidden></p>

            <div class="login-actions">
                <button type="button" data-close>Отмена</button>
                <button class="login-button" type="submit">Войти</button>
            </div>
        </form>
    `;

    const style = document.createElement("style");
    style.textContent = `
        #login-dialog {
            width: min(90vw, 24rem);
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 1.25rem;
        }

        #login-dialog::backdrop {
            background: rgb(0 0 0 / 40%);
        }

        #login-dialog form,
        #login-dialog label {
            display: grid;
            gap: 0.5rem;
        }

        #login-dialog form {
            gap: 1rem;
        }

        #login-dialog input {
            box-sizing: border-box;
            width: 100%;
            padding: 0.5rem;
        }

        #login-dialog .login-actions {
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
        }

        #login-dialog [role="alert"]:not([hidden]) {
            color: #c00;
        }
    `;

    document.head.append(style);
    document.body.append(dialog);

    dialog.querySelector("[data-close]").addEventListener(
        "click",
        () => dialog.close(),
    );

    dialog.addEventListener("close", () => dialog.remove());

    return dialog;
}

function getErrorMessage(response, body) {
    if (body && typeof body.detail === "string") {
        return body.detail;
    }

    if (response.status === 400 || response.status === 401) {
        return "Invalid username or password.";
    }

    return `Login failed (${response.status}). Please try again.`;
}

async function submitLogin(event, dialog) {
    event.preventDefault();

    const form = event.currentTarget;
    const submitButton = form.querySelector(
        'button[type="submit"]',
    );
    const errorElement = form.querySelector('[role="alert"]');

    errorElement.hidden = true;
    submitButton.disabled = true;

    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded",
            },
            body: new URLSearchParams(new FormData(form)),
            credentials: "same-origin",
        });

        if (response.ok) {
            window.location.reload();
            return;
        }

        let body = null;

        try {
            body = await response.json();
        } catch {
            // The server may return an empty or non-JSON response.
        }

        errorElement.textContent = getErrorMessage(response, body);
        errorElement.hidden = false;
    } catch {
        errorElement.textContent =
            "Unable to reach the server. Please try again.";
        errorElement.hidden = false;
    } finally {
        submitButton.disabled = false;
    }
}

function initializeLoginButton() {
    const loginButton = document.querySelector("#login-button");

    if (!loginButton) {
        return;
    }

    loginButton.addEventListener("click", () => {
        const dialog = createLoginDialog();
        const form = dialog.querySelector("form");

        form.addEventListener("submit", (event) => {
            submitLogin(event, dialog);
        });

        dialog.showModal();
        form.elements.username.focus();
    });
}

initializeLoginButton();

const LOGOUT_URL = "/auth/jwt/logout";

function initializeLogoutButton() {
    const logoutButton = document.querySelector("#logout-button");

    if (!logoutButton) {
        return;
    }

    logoutButton.addEventListener("click", async () => {
        logoutButton.disabled = true;

        try {
            const response = await fetch(LOGOUT_URL, {
                method: "POST",
                credentials: "same-origin",
            });

            if (response.ok) {
                window.location.reload();
                return;
            }

            console.error("Logout failed:", response.status);
        } catch (error) {
            console.error("Unable to reach the server:", error);
        } finally {
            logoutButton.disabled = false;
        }
    });
}

initializeLogoutButton();
