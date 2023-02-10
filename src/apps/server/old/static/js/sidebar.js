import {runTests} from "./run.js";

const sideBarHeader = document.querySelector(".sidebar__header");
const popupMenu = document.querySelector(".sidebar__popup-menu");
const changeConfigFileButton = document.querySelector("sidebar__change-config-file")
const editConfigFileButton = document.querySelector("sidebar__edit-config")
const testAccordianButtons = document.querySelectorAll(".sidebar__tests-accordian");
const runTestsButton = document.querySelector(".sidebar__run-tests-button");
const loadingContainer = document.querySelector(".sidebar__loading-container");
const testResultsContainer = document.querySelector(".sidebar__test-results-container");

// If the menu is open, and we click somewhere else on the screen, close the menu.
document.addEventListener("click", () => {
    if (popupMenu.classList.contains("sidebar__popup-menu--show")) {
        popupMenu.classList.remove("sidebar__popup-menu--show");
    }
})

// Show the menu when we click on the sidebar header.
sideBarHeader.addEventListener('click', (e) => {
    e.stopPropagation();
    popupMenu.classList.toggle("sidebar__popup-menu--show")
});

// Add a click listener to each accordian to make it toggle open or closed when clicked.
testAccordianButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
        btn.classList.toggle("sidebar__tests-accordian-active")
    })
});

runTestsButton.addEventListener("click", () => {
    runTestsButton.disabled = true;
    loadingContainer.style.display = "flex";
    // Run tests takes a function as a callback to run when it gets the response
    runTests((data) => {
        testResultsContainer.style.display = 'flex';
        appendTestResults(data);
        runTestsButton.disabled = false;
        loadingContainer.style.display = "none";
    });
});

function appendTestResults(data) {
    data.results.forEach((result) => {

        const testResultElement = document.createElement("div");
        const markElement = document.createElement("img");
        markElement.className = "sidebar__success-fail-img";
        testResultElement.className = "sidebar__test-result";
        if (result.passed_tests_ratio !== 100) {
            testResultElement.classList.add("sidebar__test-result--failed");
            markElement.src = "/static/img/failed.svg";
        } else {
            markElement.src = "/static/img/success.svg";
        }

        const testNameElement = document.createElement("span");
        testNameElement.innerHTML = result.name;

        const totalPassedElement = document.createElement("span");
        totalPassedElement.innerHTML =
            `${result.tests.filter((test) => test.result === "ComparisonResult.MATCH").length} / ${result.tests.length}`

        const testPassedRatioElement = document.createElement("span");
        const ratio = result.passed_tests_ratio.toFixed(2);
        testPassedRatioElement.innerHTML = `${ratio}%`;

        testResultElement.appendChild(testNameElement);
        testResultElement.appendChild(totalPassedElement);
        testResultElement.appendChild(testPassedRatioElement);
        testResultElement.appendChild(markElement);

        testResultsContainer.appendChild(testResultElement);
    })
}