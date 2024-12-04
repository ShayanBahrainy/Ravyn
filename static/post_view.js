function sendPostReport() {
  let ID = document.getElementById("PostID").dataset.id
  fetch("/report/" + ID, {method: "POST", credentials:"same-origin"})
}
function submitCommentReport(id) {
  fetch("/report/" + id, {method: "POST", credentials:"same-origin"})
}

function submitComment() {
  const comment = document.getElementById("NewComment").value
  const PostID = document.getElementById("PostID").dataset.id
  let data = {Comment:comment}
  fetch("/comment/" + PostID, {method:"POST", credentials:"same-origin", body:JSON.stringify(data), headers:{
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }}).then(function (Response) {
    if (Response.ok) {
      const urlparams = new URLSearchParams()
      urlparams.set("commentSuccess","True")
      location.search = urlparams
    }
    else {
      const urlparams = new URLSearchParams()
      urlparams.set("commentSuccess","False")
      location.search = urlparams
    }
  })
  document.getElementById("NewComment").value = ""
}
window.addEventListener("load", function (e) {
  this.document.getElementById("menu").addEventListener("change", function (ev) {
    if (document.getElementById("menu").value == "report") {
      sendPostReport()
      document.getElementById("menu").selectedIndex = 0
    }
  })
  this.document.getElementById("backButton").addEventListener("click", function (ev) {
    location="/"
  })
  this.document.getElementById("SubmitComment").addEventListener("click", function (ev) {
    submitComment()
  })
  let commentOptions = this.document.getElementsByClassName("CommentOptions")
  for (let element of commentOptions){
    element.addEventListener("change", function () {
      if (this.value == "Report") {
        submitCommentReport(element.dataset.id)
        element.selectedIndex = 0
      }
    })
  }
})