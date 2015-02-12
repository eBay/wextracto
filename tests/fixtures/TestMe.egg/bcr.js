function () {
    var index = 0;
    var nodeStack = new Array();
    nodeStack.push(document.documentElement);
    while (true) {
        var elem = nodeStack.pop();
        if (elem === undefined) {
            break ;
        }
        var bcr = elem.getBoundingClientRect();
        elem.setAttribute("bcr-left", bcr.left);
        elem.setAttribute("bcr-top", bcr.top);
        elem.setAttribute("bcr-right", bcr.right);
        elem.setAttribute("bcr-bottom", bcr.bottom);
        for (var i=elem.childNodes.length-1; i>=0;--i) {
            if (elem.childNodes[i].nodeType == Node.ELEMENT_NODE) {
                nodeStack.push(elem.childNodes[i]);
            }
        }
    }
}
