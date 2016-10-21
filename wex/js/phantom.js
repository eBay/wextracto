/*
 * phantomjs.js
 * ~~~~~~~~~~~~
 *
 * This is the script that runs under PhantomJS.
 * It communicates with Wextracto over stdin/stdout.
 */

var system = require('system');
var wexRequest = JSON.parse(system.stdin.read());
var webpage = require('webpage');
var page = webpage.create();
var navigation = Array();
var requiredModules = Array();
var moduleWaitCallbacks = Array();
var logLevel = wexRequest.loglevel || 30 ;
var globals = {};
var exitTimeoutId = null ;


navigation.push({"requests": Array(), "responses": {}});


//
// update webpage settings

for (var setting in (wexRequest.settings || {})) {
    page.settings[setting] = wexRequest.settings[setting];
}

//
// load the modules specified by the wexRequest

for (var i=0; i < (wexRequest.requires || []).length; i++) {
    requiredModules.push(require(wexRequest.requires[i]));
}


// logging

function log(level, msg, prefix) {
    prefix = prefix || ' [phantomjs] ';
    system.stderr.writeLine(level + prefix + msg);
}

function logDebug(msg, prefix) {
    if (logLevel <= 10) {
        log('DEBUG', msg, prefix);
    }
}

function logInfo(msg, prefix) {
    if (logLevel <= 20) {
        log('INFO ', msg, prefix);
    }
}

function logWarning(msg, prefix) {
    if (logLevel <= 30) {
        log('WARNI', msg, prefix);
    }
}

function logError(msg, prefix) {
    if (logLevel <= 40) {
        log('ERROR', msg, prefix);
    }
}

// set proxy if specified
if (wexRequest.proxy) {
    phantom.setProxy(wexRequest.proxy.hostname,
                     wexRequest.proxy.port,
                     wexRequest.proxy.type,
                     wexRequest.proxy.username,
                     wexRequest.proxy.password);
}


// webpage callbacks

page.onConsoleMessage = function(msg, prefix) {
    logDebug(msg, " [phantomjs.onConsoleMessage] ");
};

page.onError = function(msg, trace) {
    logInfo(msg, " [phantomjs.onError] ");
};

page.onNavigationRequested = function(url, type, willNavigate, main) {
    if (main) {
        logDebug("onNavigationRequested to '" + url + "' (" + type + ")");
        navigation.push({"url": url, "requests": Array(), "responses": {}});
        clearTimeout(exitTimeoutId);
    }
};

page.onResourceRequested = function(requestData, networkRequest) {
    navigation[navigation.length-1].requests.push(requestData);
    //logDebug('onResourceRequested #' + requestData.id + " '" + requestData.url + "'");
};

page.onResourceReceived = function(response) {
    navigation[navigation.length-1].responses[response.id] = response;
    //logDebug("onResourceReceived #" + response.id + " '" + response.url + "'");
};


//
// Return primary response.
// The primary response is the response to the first request
// for most recent navigation.
function getPrimaryResponse() {

    var nav = navigation[navigation.length-1] ;
    var request = null;
    var response = null;

    if (nav.requests.length > 0) {
        request = nav.requests[0];
    }

    if (request !== null && request.id in nav.responses) {
        response = nav.responses[request.id];
    }

    return response;
}


function exitIfReady() {


    keepWaiting = moduleWaitCallbacks.some(function(wait) {
        try {
            return wait();
        }
        catch (err) {
            logError("error in " + wait + ": " + err);
        }
    });

    if (keepWaiting) {
        logDebug("keep waiting");
        // try again later
        exitTimeout = setTimeout(exitIfReady, 100);
        return;
    }

    //
    // Now it's time to go

    response = getPrimaryResponse();
    writeWexIn(response);
    logInfo("phantom.exit(0) with: " + JSON.stringify(response));
    phantom.exit(0);

}

function exitIfReadyAtDepth(depth) {
    return function () {
        if (navigation.length <= depth) {
            exitIfReady();
        } else {
            logDebug('navigation since timeout started');
        }
    };
}

page.onLoadFinished = function(status) {

    var response = null ;

    if (status != "success") {
        logError("exiting because onLoadFinished(" + status + ")") ;
        phantom.exit(1);
        return;
    }

    requiredModules.map(function(module) {
        try {
            if (module.onLoadFinished) {
                wait = module.onLoadFinished();
                if (wait) {
                    moduleWaitCallbacks.push(wait);
                }
            }
        }
        catch (err) {
            logError("error in " + module + ": " + err);
        }
    });

    exitTimeout = setTimeout(exitIfReadyAtDepth(navigation.length), 100);

    logDebug("onLoadFinished: " + status);
};

function writeWexIn(response) {

    var wexin = [];
    var status = 502 ;
    var statusText = "PhantomJS error";

    if (response !== null) {
        status = response.status;
        statusText = response.statusText;

        if (response.url != page.url) {
            logWarning("response.url " + JSON.stringify(response.url) +
                       " is not same as page.url " + JSON.stringify(page.url)) ;
        }
    }

    wexin.push("HTTP/1.1 " + status + " " + statusText);
    if (response !== null) {

        for (var i=0; i<response.headers.length; i++) {
            var header = response.headers[i];
            wexin.push(header.name + ": " + header.value.replace(/\n/g, " "));
        }
    }

    var context = wexRequest.context || {};
    for (var key in context) {
        if (context.hasOwnProperty(key)) {
            wexin.push("X-wex-context-" + key + ": " + context[key]);
        }
    }

    wexin.push("X-wex-request-url: " + wexRequest.url);
    if (page.url) {
        wexin.push("X-wex-url: " + page.url);
    }
    wexin.push("");
    wexin.push(page.content);
    // previously I found PhantomJS will hang if I call write to stdout
    // multiple times (but only for large responses) so we join it all
    // in memory and then send it in one call.
    wexin = wexin.join("\r\n");

    system.stdout.write(wexin);
}


function stripFragment(url) {
    if (url.indexOf('#') >= 0) {
        return url.substring(0, url.indexOf('#'));
    }
    return url ;
}


page.open(stripFragment(wexRequest.url));
