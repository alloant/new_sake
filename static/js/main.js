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

/// DROPDOWNS
//
// Dropdown Manager using Event Delegation
/*
document.addEventListener('mouseover', function (event) {
    // Handling Mouseover (hover)
    const dropdown = event.target.closest('.dropdown');
    if (dropdown) {
        // Optional: if you want hover to open it, add is-active here
    }
});

document.addEventListener('mouseout', function (event) {
    // Handling Mouseleave via delegation
    const dropdown = event.target.closest('.dropdown');
    // If we are leaving the dropdown container entirely
    if (dropdown && !dropdown.contains(event.relatedTarget)) {
        dropdown.classList.remove('is-active');
    }
});

// Add this function before or after the dropdown event listeners
function closeAllDropdowns() {
    document.querySelectorAll('.dropdown.is-active').forEach(dropdown => {
        dropdown.classList.remove('is-active');
    });
}

document.addEventListener('click', function (event) {
    const trigger = event.target.closest('.dropdown-trigger');
    const insideMenu = event.target.closest('.dropdown-menu');
    const dropdown = event.target.closest('.dropdown');

    if (trigger) {
        // Close other dropdowns
        document.querySelectorAll('.dropdown.is-active').forEach(openDropdown => {
            if (openDropdown !== dropdown) {
                openDropdown.classList.remove('is-active');
            }
        });
        dropdown.classList.toggle('is-active');
        event.stopPropagation(); 
    } else if (!insideMenu) {
        closeAllDropdowns();
    }
});
*/
// END DROPDOWNS

// NEW DROPDOWNS
// Function to close all open menus and sub-menus
function closeAllDropdowns() {
    document.querySelectorAll('.dropdown.is-active').forEach(dropdown => {
        dropdown.classList.remove('is-active');
    });
    document.querySelectorAll('.template-accordion.is-open').forEach(acc => {
        acc.classList.remove('is-open');
    });
}

document.addEventListener('click', function (event) {
    const trigger = event.target.closest('.dropdown-trigger');
    const templateTrigger = event.target.closest('.template-trigger');
    const insideMenu = event.target.closest('.dropdown-menu');
    const dropdown = event.target.closest('.dropdown');

    // 1. Clicked inside the template sub-menu toggle
    if (templateTrigger) {
        const accordion = templateTrigger.closest('.template-accordion');
        accordion.classList.toggle('is-open');
        event.stopPropagation();
        return;
    }

    // 2. Clicked main dropdown trigger button
    if (trigger) {
        document.querySelectorAll('.dropdown.is-active').forEach(openDropdown => {
            if (openDropdown !== dropdown) {
                openDropdown.classList.remove('is-active');
            }
        });
        dropdown.classList.toggle('is-active');
        event.stopPropagation();
        return;
    }

    // 3. Clicked completely outside the open dropdown
    if (!insideMenu) {
        closeAllDropdowns();
    }
});
// END NEW DROPDOWNS



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


