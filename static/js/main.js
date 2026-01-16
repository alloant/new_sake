// static/js/main.js
//

const setupModals = () => {
  // 1. Open Modal Logic
  (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
    const modalId = $trigger.dataset.target;
    const $target = document.getElementById(modalId);

    // We remove the old listener and add a new one to prevent double-firing
    $trigger.removeEventListener('click', openHandler); 
    $trigger.addEventListener('click', openHandler);
    
    function openHandler() {
      $target.classList.add('is-active');
      document.documentElement.classList.add('is-clipped');
    }
  });

  // 2. Close Modal Logic
  const closeSelectors = '.modal-background, .modal-close, .modal-card-head .delete, .modal-card-foot .button';
  (document.querySelectorAll(closeSelectors) || []).forEach(($close) => {
    const $target = $close.closest('.modal');

    $close.removeEventListener('click', closeHandler);
    $close.addEventListener('click', closeHandler);

    function closeHandler() {
      $target.classList.remove('is-active');
      document.documentElement.classList.remove('is-clipped');
    }
  });
};

// Run on initial load
document.addEventListener('DOMContentLoaded', setupModals);

// Run every time HTMX swaps content
htmx.onLoad(function(content) {
    setupModals();
});


