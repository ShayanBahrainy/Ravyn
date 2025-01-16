let Users = []
let UserNames = ""
let UserId
let PostId = ""
let PostName
function verifyUserCheck(response) {
    if (!response.ok) {
        alert('User was not found!')
        return
    }
    response.json().then(function (data) {
        let p = document.createElement("p")
        p.innerText = data["Username"]
        Users.push(UserId)
        UserNames += data["Username"] + ", "
        document.getElementById("UserTable").appendChild(p)
    })
}
function verifyPostCheck(response) {
    if (!response.ok) {
        alert('Unable to located post!')
        return
    }
    response.json().then(function (data) {
        document.getElementById("PostTable").innerHTML = "<p>Post <br>--------------</p>"
        let p = document.createElement("p")
        p.innerText = data["PostName"] + " - " + data["Author"]
        document.getElementById("PostTable").appendChild(p)
        PostId = data["PostID"]
        PostName = data["PostName"]
    })
}
function verifyUser() {
    UserId = document.getElementById("UserId").value
    if (Users[0] == "*") {
        Users = []
        document.getElementById("UserTable").innerHTML = "<p>User <br>--------------</p>"
    }
    if (UserId in Users) {
        return
    }
    fetch("/admin/user/" + UserId + "/", {method:"POST",credentials:"same-origin"}).then(verifyUserCheck)
}

function verifyPost() {
    PostId = document.getElementById("PostId").value
    fetch("/admin/post/" + PostId, {method: "POST", credentials:"same-origin"}).then(verifyPostCheck)
}
function handleAnnounce(response) {
    if (!response.ok) {
        response.json().then(function (data) {
            alert("Announcement failed... " + data["Reason"])
        })
    }
    alert('Announced!')
    location = "/post/" + PostId
}
function submitAnnouncement() {
    if (!PostId) {
        alert("No selected post!")
        return
    }
    if (Users.length == 0) {
        alert("No selected users!")
        return
    }
    Confirmation = `You want to send '${PostName}' to ${UserNames}!?`
    if (!confirm(Confirmation)) {
        return
    }
    if (!confirm("Are you very sure?")) {
        return
    }
    data = {}
    data["PostID"] = PostId
    data["Users"] = Users
    data["BadIdea"] = "Probably"
    fetch("/admin/announcement/", {
        method: "POST", 
        credentials:"same-origin",
        body: JSON.stringify(data),
        headers: new Headers({'content-type': 'application/json'})
    }).then(handleAnnounce)
}

window.addEventListener("load", function (){
    document.getElementById("AddUser").addEventListener("click", verifyUser)
    this.document.getElementById("SendAll").addEventListener("click", function () {
        document.getElementById("UserTable").innerHTML = "<p>User <br>--------------</p>"
        let p = document.createElement("p")
        p.innerText = "All Users (!!)"
        Users = ["*"]
        UserNames = "Everybody!"
        document.getElementById("UserTable").appendChild(p)
    })
    this.document.getElementById("SelectPost").addEventListener("click", verifyPost)
    this.document.getElementById("SendAnnouncement").addEventListener("click", submitAnnouncement)
})
