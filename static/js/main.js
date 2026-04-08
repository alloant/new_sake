// static/js/main.js
//

// Handle the burger menu for mobile to show the sidebar
document.getElementById('navbar-burger').addEventListener('click', function() {
    const sidebar = document.getElementById('main-sidebar');
    const content = document.getElementById('main-content');

    sidebar.classList.toggle('is-active'); // Show the sidebar
    content.classList.toggle('is-darkened'); // Darken main content

    // Optionally, toggle the burger icon to indicate state
    this.classList.toggle('is-active');
});

document.addEventListener('click', function (event) {
    const trigger = event.target.closest('.dropdown-trigger');
    const insideMenu = event.target.closest('.dropdown-menu');

    if (trigger) {
        const dropdown = trigger.closest('.dropdown');
        
        // 1. Close other dropdowns
        document.querySelectorAll('.dropdown.is-active').forEach(openDropdown => {
            // ONLY close if it's not the one we clicked AND it's not a parent of the one we clicked
            if (openDropdown !== dropdown && !openDropdown.contains(dropdown)) {
                openDropdown.classList.remove('is-active');
            }
        });

        // 2. Toggle the current one
        dropdown.classList.toggle('is-active');
        
        event.stopPropagation(); 

    } else if (insideMenu) {
        // If clicking inside the menu (form fields, labels), do nothing so it stays open
        return;
    } else {
        // Clicked outside everything: close all
        document.querySelectorAll('.dropdown.is-active').forEach(dropdown => {
            dropdown.classList.remove('is-active');
        });
    }
});






// Request permission on page load
if (Notification.permission !== "granted") {
    Notification.requestPermission().then(permission => {
        console.log("Notification permission:", permission);
    });
}

function sendNotification(msg) {
    console.log("Function sendNotification called with:", msg);

    if (Notification.permission === "granted") {
        var myNotification = new Notification("Sake", {
            "body": msg,
            "icon": "/static/icons/sake.png", // Ensure the leading slash for absolute path
        });
        
        myNotification.onclick = (e) => {
            window.focus(); // Good practice: focus the tab when clicked
            myNotification.close();
        };
    } else {
        console.warn("Notifications are blocked or not yet granted.");
        // Fallback: use a standard alert so you can at least see it's working
        alert("Notification: " + msg);
    }
}
