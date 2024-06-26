// Affichage du point rouge dans le navbar
window.addEventListener("load", () => {
  document.body.style.display = 'none';
  setTimeout(()=>{
    document.body.style.display='block';
  }, 500)
 
  let notif = document.getElementById('nav-not');

  // Vérifie le panier dans le localStorage d el'utilisateur
  const checkcart = () => { 
    let c = true
    let user_cart = JSON.parse(localStorage.getItem('navabe-user-cart')); 
    user_cart == null ? c = false : (user_cart.length == 0 ? c= false : c = true);
    return c;
  }

  // Mettre ou pas (dépendamment du cas le point rouge sur le panier)
  const setNotif = () => {
    if (checkcart()){

      notif.style.visibility = 'visible';
      notif.style.opacity = '1';
    } else {
      
      notif.style.visibility = 'hidden';
      notif.style.opacity = '0';
    }
  }
  

  setNotif();

  // Vérification continuelle du DOM
  document.addEventListener('click', setNotif);

});

