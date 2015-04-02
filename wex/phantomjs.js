/*
 * phantomjs.js - inter-process communication between Wextracto and PhantomJS
 *
 */

var system = require('system')
var fs = require('fs')
var webpage = require('webpage')

/**
 * Read request from STDIN, parse it and perform it.
 *
 * In a previous version of this the script looped
 * so that multiple requests could be performed by
 * the same process.  Actually PhantomJS seems
 * pretty fast to start up so it turned out not to
 * be worth it.
 */
function handle_request() {

    var line = system.stdin.readLine();
    if (!line) {
        phantom.exit(0)
    }
    try {
        request = JSON.parse(line)
        performRequest(request)
    }
    catch (err) {
        system.stderr.writeLine(err);
        phantom.exit(1);
    }
}


function onConsoleMessage(msg) {
    //if (!msg.startsWith('Unsafe JavaScript attempt to access frame')) {
    system.stderr.writeLine("[phantomjs.onConsoleMessage] " + msg);
    //}
}


function onError(msg, trace) {
    system.stderr.writeLine("[phantomjs.onError] " + msg);
}

function configurePageSettings(page, request) {
    var settings = request.settings || {};
    for (var setting in settings) {
        if (!settings.hasOwnProperty) {
            continue;
        }
        page.settings[setting] = settings[setting];
    }
}

/**
 * Open the page and set-up a callback for when the results come in.
 */
function performRequest(request) {

    page = webpage.create();
    configurePageSettings(page, request);
    page.onConsoleMessage = onConsoleMessage;
    page.onError = onError ;

    page.onLoadStarted = function() {
        var href = page.evaluate(function() { return window.location.href; });
        if (href === "about:blank") {
            page.loadTimeout = setTimeout(
                function() {
                    system.stderr.writeLine("[phantomjs] '" + request.url + "' timeout");
                    phantom.exit(1);
                },
                request.timeout || 60000
            );
        }
    }

    wexout = fs.open(request.wexout, 'w');

    page.onResourceReceived = function(response) {

        if (response.stage != "end" || response.id != 1) {
            // this isn't the resource we're looking for
            return;
        }


        wexout.writeLine("HTTP/1.1 " + response.status + " " +
                         response.statusText + "\r");
        for (var i=0; i<response.headers.length; i++) {
            var header = response.headers[i];
            wexout.writeLine(header.name + ": " + header.value.replace(/\n/g, " ") + "\r");
        }

        wexout.writeLine("X-wex-request-url: " + request.wex_url + "\r");
        wexout.writeLine("X-wex-url: " + response.url + "\r");
        wexout.writeLine("\r");
        wexout.flush();
    }

    page.open(
        request.url,
        function onPageOpenFinished(status) {

            // Evaluate files containing JavaScript
            var evaluate = request.evaluate || [] ;
            for (var i=0; i < evaluate.length; i++) {
                page.evaluateJavaScript(fs.read(evaluate[i]));

            }

            wexout.write(page.content);
            wexout.flush();
            wexout.close();
            clearTimeout(page.loadTimeout);
            phantom.exit();
        }
    );
}


/* Let's get this party started!  */
handle_request()
