/*
 * phantomjs.js
 * ~~~~~~~~~~~~
 *
 * This is the script that runs under PhantomJS.
 * It communicates with Wextracto over stdin/stdout.
 */

var system = require('system');
var request = JSON.parse(system.stdin.read());
var webpage = require('webpage');
var page = webpage.create();
var navigation = Array();
var loglevel = request.loglevel || 30 ;


// update webpage settings

for (var setting in (request.settings || {})) {
    page.settings[setting] = request.settings[setting];
}


// logging

function log(level, msg, prefix) {
    prefix = prefix || ' [phantomjs] ';
    system.stderr.writeLine(level + prefix + msg);
}

function logDebug(msg, prefix) {
    if (loglevel <= 10) {
        log('DEBUG', msg, prefix);
    }
}

function logInfo(msg, prefix) {
    if (loglevel <= 20) {
        log('INFO', msg, prefix);
    }
}

function logError(msg, prefix) {
    if (loglevel <= 40) {
        log('ERROR', msg, prefix);
    }
}

// set proxy if specified
if (request.proxy) {
    phantom.setProxy(request.proxy.hostname,
                     request.proxy.port,
                     request.proxy.type,
                     request.proxy.username,
                     request.proxy.password);
}


// webpage callbacks

page.onConsoleMessage = function(msg, prefix) {
    logDebug(msg, " [phantomjs.onConsoleMessage] ");
};

page.onError = function(msg, trace) {
    logError(msg, " [phantomjs.onError] ");
};

page.onNavigationRequested = function(url, type, willNavigate, main) {
    if (main) {
        logDebug("onNavigationRequested to '" + url + "' (" + type + ")");
        navigation.push({"url":url});
    }
};

page.onResourceRequested = function(requestData, networkRequest) {
    for (var i=navigation.length-1;i>=0;i--) {
        if (requestData.url == navigation[i].url) {
            navigation[i].id = requestData.id;
            navigation[i].request = {
                'method': requestData.method,
                'requestTime': requestData.time,
                'requestHeaders': requestData.headers
            };
            logDebug('onResourceRequested #' + requestData.id + " '" +
                     requestData.url + "'");
            break;
       }
    }
};

page.onResourceReceived = function(response) {

    if (response.stage != "end") {
        return;
    }

    for (var i=navigation.length-1;i>=0;i--) {
        if (response.id == navigation[i].id) {
            navigation[i].response = {
                'url': response.url,
                'time': response.time,
                'headers': response.headers,
                'redirectURL': response.redirectURL,
                'status': response.status,
                'statusText': response.statusText
            };
            logDebug("onResourceReceived #" + response.id + 
                     " '" +
                     response.url + "'");
            break;
        }
    }
};


page.onLoadFinished = function(status) {
    logDebug("onLoadFinished: " + status);
    if (navigation[navigation.length-1].response) {
        for (var i=0;i<(request.requires || []).length;i++){
            module = require(request.requires[i]);
            module.apply();
        }
        writeWexOut(navigation[navigation.length-1]);
        phantom.exit(0);
    } else {
        logError("onLoadFinished with no response for '" +
                 navigation[navigation.length-1].url + "'");
        system.stdout.write("HTTP/1.1 502 PHANTOMJS ERROR\r\n\r\n");
        phantom.exit(1);
    }
};

function writeWexOut(nav) {
    var wexout = [];
    wexout.push("HTTP/1.1 " +
                nav.response.status + " " + 
                nav.response.statusText);
    for (var i=0; i<nav.response.headers.length; i++) {
        var header = nav.response.headers[i];
        wexout.push(header.name + ": " + header.value.replace(/\n/g, " "));
    }
    var context = request.context || {};
    for (var key in context) {
        if (context.hasOwnProperty(key)) {
            wexout.push("X-wex-context-" + key + ": " + context[key]);
        }
    }
    wexout.push("X-wex-request-url: " + request.url);
    wexout.push("X-wex-url: " + nav.response.url);
    wexout.push("");
    wexout.push(page.content);
    // previously I found PhantomJS will hang if I call write to stdout
    // multiple times (but only for large responses) so we join it all
    // in memory and then send it in one call.
    wexout = wexout.join("\r\n");
    system.stdout.write(wexout);
}

if (request.url.indexOf('#') >= 0) {
    page.open(request.url.substring(0, request.url.indexOf('#')));
} else {
    page.open(request.url);
}
