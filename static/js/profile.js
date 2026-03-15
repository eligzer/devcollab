document.addEventListener("DOMContentLoaded", function () {

const avatar = document.querySelector(".profile-avatar");
const menu = document.getElementById("profileMenu");

if(!avatar || !menu) return;


/* open / close dropdown */

avatar.addEventListener("click", function(e){

e.stopPropagation();

menu.classList.toggle("active");

});


/* prevent closing when clicking menu */

menu.addEventListener("click", function(e){

e.stopPropagation();

});


/* close when clicking outside */

document.addEventListener("click", function(){

menu.classList.remove("active");

});

});