
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('select.tom-select:not(.ts-loaded)').forEach(el => {
    new TomSelect(el, {
      maxOptions: 1000,
      hideSelected: true,
      dropdownClass: 'bg-slate-800 text-slate-800 dark:text-white border border-slate-300 dark:border-slate-600 rounded-xl shadow-lg mt-1',
    });
    el.classList.add('ts-loaded');
  });
});

