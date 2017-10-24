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
var logLevel = wexRequest.loglevel ;
var globals = {};
var waitMS = 100 ;
var requestWait = wexRequest.requestWait || 500 ;
var exitTimeoutId = null ;


navigation.push({"requests": Array(), "responses": {}, "started": false});

if (logLevel === null || logLevel === undefined) {
    logLevel = 30;
}

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


// callbacks

phantom.onError = function(msg, trace) {
    logInfo(msg, " [phantomjs.onError(phantom)] ");
};

page.onConsoleMessage = function(msg, prefix) {
    logDebug(msg, " [phantomjs.onConsoleMessage] ");
};

page.onError = function(msg, trace) {
    logInfo(msg, " [phantomjs.onError] ");
};

page.onInitialized = function() {
    requiredModules.map(function(module) {
        try {
            if (module.onInitialized) {
                module.onInitialized();
            }
        }
        catch (err) {
            logError("error in " + module + ": " + err);
        }
    });
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
};

page.onResourceReceived = function(response) {
    navigation[navigation.length-1].responses[response.id] = response;
};

page.onResourceError = function(resourceError) {
    logDebug("onResourceError: " + JSON.stringify(resourceError));
    navigation[navigation.length-1].responses[resourceError.id] = resourceError;
};


//
// Return primary response.
// The primary response is the response to the first request
// for most recent navigation.
function getPrimaryResponse() {

    var i;
    var nav = null;
    var pageUrl = page.url && stripFragment(page.url);

    // Work backwards until we find navigation where onLoadStarted happened
    for (i = navigation.length-1; i >= 0; i--) {
        if (navigation[i].started) {
            nav = navigation[i];
            break;
        }
    }

    if (!nav) {
        return null;
    }

    var request = null;
    var response = null;

    for (i = 0 ; i < nav.requests.length; i++) {
        if (nav.requests[i].url == pageUrl) {
            request = nav.requests[i];
            break;
        }
    }

    if (request === null && nav.requests.length > 0) {
        request = nav.requests[0];
    }

    if (request !== null && request.id in nav.responses) {
        response = nav.responses[request.id];
    }

    return response;
}

var numWaits = 0;

function exitIfReady() {

    var keepWaiting = false;

    logDebug('exitIfReady()');
    numWaits += 1;

    var nav = navigation[navigation.length-1];
    for (var i = 0 ; i < nav.requests.length; i++) {
        var since = Date.now() - nav.requests[i].time.getTime();
        if (!(nav.requests[i].id in nav.responses)) {
            if (since <= requestWait) {
                logDebug("keep waiting for request: " + nav.requests[i].url);
                keepWaiting = true;
                break;
            }
        }
    }

    if (!keepWaiting) {
        // Ask the loaded modules if they need us to keep waiting
        keepWaiting = moduleWaitCallbacks.some(function(keepWaitingCallback) {
            try {
                return keepWaitingCallback(numWaits * waitMS);
            }
            catch (err) {
                logError("error in " + wait + ": " + err);
            }
        });
    }

    if (keepWaiting) {
        logDebug("not ready to exit - try again in " + waitMS + "ms");
        exitTimeoutId = setTimeout(exitIfReadyAtDepth(navigation.length), waitMS);
        return;
    }

    //
    // Now it's time to go

    response = getPrimaryResponse();
    writeWexIn(response);
    logDebug("phantom.exit(0) with: " + JSON.stringify(response));
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

page.onLoadStarted = function() {
     var currentUrl = page.evaluate(function() {
             return window.location.href;
     });
     var readyState = page.evaluate(function() {
             return document.readyState;
     });
    logDebug('onLoadStarted: ' + currentUrl + ' ' + page.url + ' ' + readyState);
    navigation[navigation.length-1].started = true;
};

page.onUrlChanged = function(targetUrl) {
      logDebug('onUrlChanged: ' + targetUrl);
};

page.onLoadFinished = function(status) {

    var response = null ;

    //if (status != "success") {
    if (!page.url) {
        logError("exiting because onLoadFinished(" + status + ") " + page.url) ;
        phantom.exit(1);
        return;
    }

    requiredModules.map(function(module) {
        try {
            if (module.onLoadFinished) {
                wait = module.onLoadFinished();
                // logDebug("wait? " + wait + " " + module);
                if (wait) {
                    moduleWaitCallbacks.push(wait);
                }
            }
        }
        catch (err) {
            logError("error in " + module + ": " + err);
        }
    });

    clearTimeout(exitTimeoutId);
    exitTimeoutId = setTimeout(exitIfReadyAtDepth(navigation.length), 0);

    logDebug("onLoadFinished: " + status);
};

function writeWexIn(response) {

    var wexin = [];
    var status = 502 ;
    var statusText = "PhantomJS error";

    if (response !== null) {
        // sometimes response has null status/statusText
        status = response.status || status;
        statusText = response.statusText || statusText;

        var pageUrl = page.url && stripFragment(page.url);

        if (response.url != pageUrl) {
            logWarning("response.url " + JSON.stringify(response.url) +
                       " is not same as page.url " + JSON.stringify(pageUrl)) ;
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
    if (wexRequest.proxy) {
        wexin.push('X-wex-context-proxy-http: ' + wexRequest.proxy.type + '://' + wexRequest.proxy.username + ':' + wexRequest.proxy.password + '@' + wexRequest.proxy.hostname + ':' + wexRequest.proxy.port);
    }

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
