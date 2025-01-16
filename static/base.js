let clicked 
let ctxmenu 
function CopyUserId() {
    if (clicked.dataset.userId) {
        navigator.clipboard.writeText(clicked.dataset.userId)
        return
    }
    if (clicked.parentNode.dataset.userId) {
        navigator.clipboard.writeText(clicked.parentNode.dataset.userId)
    }
}
function CopyPostId() {
    if (clicked.dataset.postId) {
        navigator.clipboard.writeText(clicked.dataset.postId)
        return
    }
    if (clicked.parentNode.dataset.postId) {
        navigator.clipboard.writeText(clicked.parentNode.dataset.postId)
    }
}
const PostAdminMenu = `
<p onclick="CopyPostId()">Copy PostId</p>
`
const UserAdminMenu = `
<p onclick="CopyUserId()">Copy UserId</p>
`
function generateAdminMenu(e) {
    if (!clicked) {
        return ''
    }
    if (clicked.nodeName == "HTML") {
        return ''
    }
    //We only check parents if the element doesn't match either a post or user
    if (clicked.dataset.postId) {
        e.preventDefault()
        return PostAdminMenu
    }
    if (clicked.dataset.userId || clicked.parentNode.dataset.userId) {
        e.preventDefault()
        return UserAdminMenu
    }
    if (clicked.parentNode.dataset.postId) {
        e.preventDefault()
        return PostAdminMenu;
    }
    if (clicked.parentNode.dataset.userId) {
        e.preventDefault()
        return UserAdminMenu
    }
    return ''
}
oncontextmenu = (e) => {
    if (ctxmenu) {
        ctxmenu.outerHTML = ''
    }
    clicked = e.target
    let menu = document.createElement("div")
    menu.id = "ctxmenu"
    menu.style = `top:${e.pageY-10}px;left:${e.pageX-40}px`
    menu.onmouseleave = () => menu.outerHTML = ''
    menu.onclick = () => menu.outerHTML = ''
    function callback(ev) {
            if (document.elementFromPoint(ev.pageX,ev.pageY) != menu) {
                document.removeEventListener("mousemove", callback)
                if (ctxmenu) {
                    ctxmenu.outerHTML = ''
                }
            }
    }
    document.addEventListener("mousemove", callback)
    menu.innerHTML = generateAdminMenu(e) 
    document.body.appendChild(menu)
}