function sendReport() {
  let ID = document.getElementById("PostID").dataset.id
  fetch("/report/" + ID, {method: "POST", credentials:"same-origin"})
}
function submitComment() {
  const comment = document.getElementById("NewComment").value
  const PostID = document.getElementById("PostID").dataset.id
  let data = {Comment:comment}
  fetch("/comment/" + PostID, {method:"POST", credentials:"same-origin", body:JSON.stringify(data), headers:{
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }})
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
  this.document.getElementById("SubmitComment").addEventListener("click", function (ev) {
    submitComment()
  })
})