function OpenSearch() {
    document.getElementById("SearchScreen").className = "SearchScreen"
}
class Search {
    constructor(SearchInput) {
        this.SearchInput = SearchInput
        this.SearchTimerId = 0
        this.searchInterval = 500
        SearchInput.addEventListener("input", this)
        document.addEventListener("keydown", this)
    }
    handleEvent(ev) {
        if (ev.type == "keydown" && ev.key == "Escape") {
            document.getElementById("SearchScreen").className = "SearchScreen hidden"
        }
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
window.addEventListener("load", function () {
    let search = new Search(this.document.getElementById("SearchBar"))
    if (this.document.getElementById("NewPost")) {
        this.document.getElementById("NewPost").addEventListener("click", function () {
            location = "/post/"
        })
    }
    this.document.getElementById("OpenSearch").addEventListener("click", OpenSearch)
})