function OpenSearch() {
    document.getElementById("SearchScreen").className = "SearchScreen"
}
class Search {
    constructor(SearchInput) {
        this.SearchInput = SearchInput
        this.SearchTimerId = 0
        this.searchInterval = 500
        SearchInput.addEventListener("input", this)
    }
    handleEvent(ev) {
        if (ev.type != "input") {
            return
        }
        clearTimeout(this.SearchTimerId)
        setTimeout(this.doSearch, this.searchInterval, this)
    }
    static createQueryID() {
        return Math.random() * 100000
    }
    doSearch(self) {
        if (self.controller) {
            self.controller.abort()
        }
        const Query = self.SearchInput.value
        if (Query.length < 3) {
            return
        }
        const AbortControl = new AbortController()
        self.controller = AbortControl
        fetch("/search/" + Query, {method:"GET", credentials:"same-origin", signal: AbortControl.signal}).then(function (Response, QueryID) {
            self.handleSearchResponse(Response)
        })
    }
    handleSearchResponse(Response) {
        if (Response.ok) {
            Response.json().then(function (Results){
                Results = Results["Results"]
                document.getElementById("SearchResultContainer").innerHTML = ""
                for (let Result of Results) {
                    let URL = Result["URL"]
                    let Title = Result["TITLE"]
                    let title = document.createElement("h1")
                    title.textContent = Title
                    title.className = "SearchResult"
                    title.addEventListener("click", function() {
                        location = URL
                    })
                    document.getElementById("SearchResultContainer").appendChild(title)
                }
                if (Results.length == 0) {
                    let title = document.createElement("h1")
                    title.innerHTML = "<i>No Results.</i>"
                    title.className = "NoResultResult"
                    title.addEventListener("click", function () {
                        location.reload()
                    })
                    document.getElementById("SearchResultContainer").appendChild(title)
                }
            })
        }
    }

}
function clearNotification(id) {
    fetch("/notifications/clear/" + id, {method:"POST",credentials:"same-origin"})
}
function renderNotifications(data) {
    for (let notification of data["Notifications"]){
        let NotificationContainer = document.createElement("div")
        NotificationContainer.className = "NotificationContainer"
        let p  = document.createElement("p")
        p.innerText = notification["TITLE"]
        p.className = "NotificationResult"
        p.addEventListener("click", function () {
            window.open(notification["HREF"])
        })
        let deleteNotification = document.createElement("input")
        deleteNotification.type = "checkbox"
        deleteNotification.className = "ClearNotification"
        deleteNotification.addEventListener("click", function () {
            clearNotification(notification["ID"])
            NotificationContainer.remove()
        })
        NotificationContainer.appendChild(deleteNotification)
        NotificationContainer.appendChild(p)
        document.getElementById("NotificationResults").appendChild(NotificationContainer)
    }
    if (data["Notifications"].length == 0) {
        let p  = document.createElement("p")
        p.innerText = "No notifications :)"
        p.className = "NoNotificationResult"
        p.addEventListener("click", function () {
            closeScreens()
        })
        let NotificationContainer = document.createElement("div")
        NotificationContainer.className = "NotificationContainer"
        NotificationContainer.appendChild(p)
        document.getElementById("NotificationResults").appendChild(NotificationContainer)
    }
}
function requestCallBack(R) {
    R.json().then(renderNotifications)
}
function OpenNotifications () {
    let notificationscreen = document.getElementById("NotificationScreen")
    notificationscreen.className = "NotificationScreen"
    let notificationresults = document.getElementById("NotificationResults")
    notificationresults.innerHTML = ""
    fetch("/notifications/", {method:"GET", credentials:"same-origin"}).then(requestCallBack)
}
function closeScreens() {
    document.getElementById("NotificationScreen").className = "NotificationScreen hidden"
    document.getElementById("SearchScreen").className = "SearchScreen hidden"
}
function addProfileLinks() {
    let profilepictures = this.document.getElementsByClassName("AuthorProfile")
    let selfpicture = this.document.getElementsByClassName("SelfProfile")
    if (selfpicture.length == 1) {
        selfpicture[0].addEventListener("click", function () {
            location = "/profile/" + selfpicture[0].dataset.userId
        })
    }
    for (let profilepicture of profilepictures) {
        profilepicture.addEventListener("click",function (ev){ 
            location='/profile/' + profilepicture.dataset.userId
            ev.stopPropagation()
        })
    }
}
function addPostLinks() {
    let posts = this.document.getElementById("Feed").children
    for (let post of posts) {
        post.addEventListener("click", function () {
            location="/post/" + post.dataset.postId
            ev.stopPropagation()
        })
    }
}
document.addEventListener("keydown", function(ev) {
    if (ev.key == "Escape") {
        closeScreens()
    }
})
window.addEventListener("load", function () {
    let search = new Search(this.document.getElementById("SearchBar"))
    if (this.document.getElementById("NewPost")) {
        this.document.getElementById("NewPost").addEventListener("click", function () {
            location = "/post/"
        })
    }
    if (this.document.getElementById("Notifications")) {
        this.document.getElementById("Notifications").addEventListener("click", OpenNotifications)
    }
    this.document.getElementById("OpenSearch").addEventListener("click", OpenSearch)
    addProfileLinks()
    addPostLinks()
})