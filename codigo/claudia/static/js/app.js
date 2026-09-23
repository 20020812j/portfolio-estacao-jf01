document.querySelector('.mobile-menu')?.addEventListener('click', () => {
  document.querySelector('.site-header nav').classList.toggle('open');
});
document.querySelectorAll('.ajax-cart').forEach(form => {
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const button = form.querySelector('button');
    const old = button.textContent;
    button.disabled = true;
    const response = await fetch(form.action, {
      method:'POST',
      headers:{'X-Requested-With':'XMLHttpRequest'},
      body:new FormData(form)
    });
    const data = await response.json();
    if(data.ok){
      document.getElementById('cart-count').textContent=data.count;
      button.textContent='✓ Adicionado';
      setTimeout(()=>button.textContent=old, 1200);
    }
    button.disabled=false;
  });
});
