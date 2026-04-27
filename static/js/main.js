// static/js/main.js

// Active the menu in the sidebar
function updateSidebarActive(clickedElement) {
    // 1. Get the actual <a> tag even if they clicked the icon inside it
    const link = clickedElement.closest('a');
    if (!link) return;

    // 2. Find the parent menu to clear old states
    const sidebar = link.closest('.menu');
    
    // 3. Clear ALL active states in this menu
    sidebar.querySelectorAll('.is-active').forEach(item => {
        item.classList.remove('is-active');
    });

    // 4. Add to the link
    link.classList.add('is-active');
}
// End sidebar active

// To control sidebar and close it while clicking anywhere
document.addEventListener('DOMContentLoaded', () => {
    const burger = document.getElementById('navbar-burger');
    const sidebar = document.getElementById('main-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const mainContent = document.getElementById('main-content');

    function toggleMenu() {
        burger.classList.toggle('is-active');
        sidebar.classList.toggle('is-active');
        overlay.classList.toggle('is-active');
        if (mainContent) mainContent.classList.toggle('is-darkened');
    }

    if (burger) {
        burger.addEventListener('click', toggleMenu);
    }
    
    // Close sidebar if user clicks the overlay
    if (overlay) {
        overlay.addEventListener('click', toggleMenu);
    }
});


// To toggle checkboxes in forms
function toggleAllTargets(shouldCheck) {
    // Select all checkboxes that are inside the searchable container
    const container = document.getElementById('sortable-targets');
    const checkboxes = container.querySelectorAll('.target-checkbox');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = shouldCheck;
        
        // Optional: Trigger a change event so your existing 
        // department auto-select logic runs if needed
        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
    });
}
// End toggle checkboxes /////


document.addEventListener('click', function (event) {
    const trigger = event.target.closest('.dropdown-trigger');
    const insideMenu = event.target.closest('.dropdown-menu');

    if (trigger) {
        const dropdown = trigger.closest('.dropdown');
        
        // Close other dropdowns
        document.querySelectorAll('.dropdown.is-active').forEach(openDropdown => {
            if (openDropdown !== dropdown) {
                openDropdown.classList.remove('is-active');
            }
        });

        // Toggle current
        dropdown.classList.toggle('is-active');
        event.stopPropagation(); 

    } else if (!insideMenu) {
        // Clicked outside: close all
        closeAllDropdowns();
    }
});

// NEW: Close menu when mouse leaves the dropdown container
document.querySelectorAll('.dropdown').forEach(dropdown => {
    dropdown.addEventListener('mouseleave', () => {
        dropdown.classList.remove('is-active');
    });
});

function closeAllDropdowns() {
    document.querySelectorAll('.dropdown.is-active').forEach(dropdown => {
        dropdown.classList.remove('is-active');
    });
}








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
