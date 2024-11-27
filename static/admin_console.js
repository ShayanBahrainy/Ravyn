function freePost (id, name) {
    let confirmation = confirm("Clear all reports for \"" + name + "\"?")
    if (confirmation) {
        fetch("/report/clear/" + id, {method: "POST", credentials:"same-origin"})
    }
}
function deletePost (id,name) {
    let confirmation = confirm("Delete the post \"" + name + "\"?")
    if (confirmation) {
        fetch("/report/delete/" + id, {method: "POST", credentials:"same-origin"})
    }
}
window.addEventListener("load", function () {
    this.document.getElementById("Free").addEventListener("click", freePost)
})