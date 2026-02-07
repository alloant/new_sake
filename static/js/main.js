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

