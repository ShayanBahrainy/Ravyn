window.addEventListener("load", function () {
    this.document.getElementById("PostOptions").addEventListener("change", function (ev) {
        if (this.value == "Upload") {
            this.selectedIndex = "0"
            document.getElementById("Image-Upload").click()
        }
    })
})