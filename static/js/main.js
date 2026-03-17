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
    // 1. Find if the user clicked the button or anything INSIDE the button (like the icon)
    const trigger = event.target.closest('.dropdown-trigger');
    
    // 2. If it's a dropdown trigger, toggle its parent
    if (trigger) {
        const dropdown = trigger.closest('.dropdown');
        
        // Close any other open dropdowns first (Optional, but cleaner)
        document.querySelectorAll('.dropdown.is-active').forEach(openDropdown => {
            if (openDropdown !== dropdown) {
                openDropdown.classList.remove('is-active');
            }
        });

        // Toggle the current one
        dropdown.classList.toggle('is-active');
        
        // Prevent the click from "bubbling up" to the document listener below
        event.stopPropagation(); 
    } else {
        // 3. If the user clicked anywhere else, close all open dropdowns
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
