function sendReport() {
  let ID = document.getElementById("PostID").dataset.id
  fetch("/report/" + ID, {method: "POST", credentials:"same-origin"})
}
window.addEventListener("load", function (e) {
  this.document.getElementById("menu").addEventListener("change", function (ev) {
    if (document.getElementById("menu").value == "report") {
      sendReport()
      document.getElementById("menu").selectedIndex = 0
    }
  })
  this.document.getElementById("backButton").addEventListener("click", function (ev) {
    history.back()
  })
})