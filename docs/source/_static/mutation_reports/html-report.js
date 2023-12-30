function addShowHideEventListeners() {
    var acc = document.getElementsByClassName("show_hide_row");
    var i;

    for (i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            this.classList.toggle("active");
            this.children[0].innerHTML = this.classList.contains("active") ? "&#x25BE;" : "&#x25B8;";
            var panel = this.nextElementSibling;
            if (panel.style.display === "table-row") {
                panel.style.display = "none";
            } else {
                panel.style.display = "table-row";
            }
        });
    };
};