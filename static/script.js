// SECCIONES 
document.addEventListener("DOMContentLoaded", () => {
    // Menú desplegable
    const menuHeaders = document.querySelectorAll(".menu-header");
    menuHeaders.forEach(header => {
        header.addEventListener("click", function () {
            const menuItem = this.parentElement;
            menuItem.classList.toggle("active");
        });
    });
});