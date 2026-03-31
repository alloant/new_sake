
def notification(message, color):
    return f"""<div id="notification" class="notification is-{color} is-google-snackbar" hx-swap-oob="true">
                    <div class="notification-content">
                        {message}
                    </div>
                    <button class="delete"></button>
                </div>
            """
