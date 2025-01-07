function setPage(page) {
    console.log(page)
    document.getElementById("PageNumber").innerHTML = page + 1
    let params = new URLSearchParams(window.location.search)
    params.set("page",page)
    window.location.search = params.toString()
}
function NextPage() {
    let params = new URLSearchParams(window.location.search)
    page = Number(params.get("page"))
    if (page != NaN){
        page += 1
        setPage(page)
    }
    else {
        page = 0
        setPage(page)
    }
}
function PreviousPage() {
    let params = new URLSearchParams(window.location.search)
    page = Number(params.get("page"))
    if (page != NaN && page > 0){
        page -= 1
        setPage(page)
    }
    else {
        page = 0
        setPage(page)
    }
}
function Back() {
    location = '/'
}
window.addEventListener("load", function () {
    this.document.getElementById("NextButton").addEventListener("click",NextPage)
    this.document.getElementById("BackButton").addEventListener("click",PreviousPage)
    this.document.getElementById("backButton").addEventListener("click",Back)
    let params = new URLSearchParams(window.location.search)
    page = parseInt(params.get("page"))
    if (!Object.is(page,NaN)) {
        this.document.getElementById("PageNumber").innerText = page + 1
    }
    else {
        page = 0
        setPage(0)
    }
})