function OpenSearch() {
    document.getElementById("SearchScreen").className = "SearchScreen"
}
window.addEventListener("load", function () {
    if (!this.document.getElementById("NewPost")) {
        return
    }
    this.document.getElementById("NewPost").addEventListener("click", function () {
        location = "/post/"
    })
    this.document.getElementById("OpenSearch").addEventListener("click", OpenSearch)
})