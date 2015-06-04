exports.apply = function () {
    page.evaluate(
        function () {
            var index = 0;
            var nodeStack = [];
            nodeStack.push(document.documentElement);
            while (true) {
                var elem = nodeStack.pop();
                if (elem === undefined) {
                    break ;
                }
                var bcr = elem.getBoundingClientRect();
                if (bcr.left !== 0) {
                    elem.setAttribute("bcr-left", bcr.left);
                }
                if (bcr.top !== 0) {
                    elem.setAttribute("bcr-top", bcr.top);
                }
                if (bcr.right !== 0) {
                    elem.setAttribute("bcr-right", bcr.right);
                }
                if (bcr.bottom !== 0) {
                    elem.setAttribute("bcr-bottom", bcr.bottom);
                }
                for (var i=elem.childNodes.length-1; i>=0;--i) {
                    if (elem.childNodes[i].nodeType == Node.ELEMENT_NODE) {
                        nodeStack.push(elem.childNodes[i]);
                    }
                }
            }
        }
    );
};
