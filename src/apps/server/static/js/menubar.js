const dropDownMenuButton = document.querySelector(".dropdown__button");
const dropDownMenuContent = document.querySelector(".dropdown__content");

// If the menu is open, and we click somewhere else on the screen, close the menu.
document.addEventListener("click", () => {
    if (dropDownMenuContent.classList.contains("dropdown__content--show")) {
        dropDownMenuContent.classList.remove("dropdown__content--show");
    }
})

//Show the dropdown menu content when the dropdown menu button is clicked.
dropDownMenuButton.addEventListener('click', (event) => {
    event.stopPropagation(); //Don't pass this click to the document.
    dropDownMenuContent.classList.toggle("dropdown__content--show");
});