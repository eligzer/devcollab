document.addEventListener("DOMContentLoaded", function () {

const wrapper = document.querySelector(".profile-wrapper");
const menu = document.getElementById("profileMenu");

if(!wrapper || !menu) return;

wrapper.addEventListener("click", function(e){
e.stopPropagation();
menu.classList.toggle("active");
});

document.addEventListener("click", function(){
menu.classList.remove("active");
});

});