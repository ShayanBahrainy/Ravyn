function sendPostReport() {
  let ID = document.getElementById("PostID").dataset.postId
  fetch("/report/" + ID, {method: "POST", credentials:"same-origin"})
}
function submitCommentReport(id) {
  fetch("/report/" + id, {method: "POST", credentials:"same-origin"})
}

function submitComment() {
  const comment = document.getElementById("NewComment").value
  if (comment.length < 10) {
    alert('Comment too short!')
    return
  }
  const PostID = document.getElementById("PostID").dataset.postId
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
function handleResult(response) {
  if (response.ok) {
      return
  }
  if (response.status == 404) {
      alert('404; Not found!')
      return
  }
  if (409 > response.status && response.status > 400) {
    alert('Try logging in or making an account :)')
    return
  }
  alert("I'm so sorry an unkown error occurred")
}
function addUpLiftandDownShiftButtons() {
  let UpLift = document.getElementsByClassName("UpLift")
  let DownShift = document.getElementsByClassName("DownShift")
  for (let button of UpLift) {
      button.addEventListener("click", function (ev) {
          fetch("/post/" + button.dataset.postId + "/uplift/", {method: "POST", credentials:"same-origin"}).then(handleResult)
          ev.stopPropagation()
      })
  }
  for (let button of DownShift) {
      button.addEventListener("click", function (ev) {
          fetch("/post/" + button.dataset.postId + "/downshift/", {method: "POST", credentials:"same-origin"}).then(handleResult)
          ev.stopPropagation()
      }) 
  }
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
  let params = new URLSearchParams(this.location.search)
  if (params.get("showComment") != null) {
    this.document.getElementById(params.get("showComment")).scrollIntoView(true)
  }
  let profiles = this.document.getElementsByClassName("CommentImage")
  for (let profile of profiles) {
    profile.addEventListener("click", function (){
      location = "/profile/" + profile.dataset.userId
    })
  }
  let authorlink = this.document.getElementById("AuthorName")
  authorlink.addEventListener("click", function () {
    location = "/profile/" + authorlink.dataset.userId
  })
  addUpLiftandDownShiftButtons()
})
