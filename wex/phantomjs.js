/*
 * phantomjs.js - A tool for dumping the rendered web page DOM.
 *
 * It is designed for use from controlling process, but you can try it yourself:
 *     $ phantomjs dumpdom.js
 *     {"url": "http://httpbin.org/html"}<enter>
 *     {[....]}
 *
 */

var system = require('system')
var fs = require('fs')
var webpage = require('webpage')
var defaults = {
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36',
    viewportSize: {width: 1024, height:768}
}
var jquery = 'http://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js'

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
        perform_request(request)
    }
    catch (err) {
        system.stderr.writeLine(err);
        phantom.exit(1);
    }
}


function onConsoleMessage(msg) {
    system.stderr.writeLine("[phantomjs.onConsoleMessage] " + msg);
}


function onError(msg, trace) {
    system.stderr.writeLine("[phantomjs.onError] " + msg);
}


/**
 * Open the page and set-up a callback for when the results come in.
 */
function perform_request(request) {

    var consoleMessages = Array();

    page = webpage.create();
    page.viewportSize = request.viewportSize || defaults.viewportSize;
    page.settings.userAgent = request.userAgent || defaults.userAgent;
    page.onConsoleMessage = onConsoleMessage;
    page.onError = onError ;

    page.onLoadStarted = function() {
        console.log('onLoadStarted');
        page.loadTimeout = setTimeout(
            function() {
                system.stderr.writeLine("[phantomjs] '" + request.url + "' timeout");
                phantom.exit(1);
            },
            request.timeout || 60000
        )
    }

    page.onNavigationRequested = function(url, type, willNavigate, main) {
        console.log('Trying to navigate to: ' + url);
      //#console.log('Caused by: ' + type);
      //#console.log('Will actually navigate: ' + willNavigate);
      //#console.log('Sent from the page\'s main frame: ' + main);
    }

    wexout = fs.open(request.wexout, 'w');

    page.onResourceReceived = function(response) {

        console.log("RECEIVED:" +  response.url + response.status);

        if (response.status != 200) {
            var line = "received: " + response.url + " - " + response.status;
            system.stderr.writeLine(line);
        }

        if (response.stage != "end" || response.id != 1) {
            // this isn't the resource we're looking for
            return;
        }

        wexout.writeLine("HTTP/1.1 " + response.status + " " +
                         response.statusText + "\r");
        for (var i=0; i<response.headers.length; i++) {
            var header = response.headers[i];
            wexout.writeLine(header.name + ": " + header.value + "\r");
        }

        wexout.writeLine("X-wex-url: " + request.wex_url + "\r");
        wexout.writeLine("\r");
        wexout.flush();
    }

    page.open(
        request.url,
        function onPageOpenFinished(status) {
            console.log("HELLO");
            clearTimeout(page.loadTimeout);
            page.includeJs(
                jquery,
                function() {
                    page.evaluate(
                        function() {
                            console.log("INSIDE");
                            console.log("XX:" + $("input[autocomplete=off]").val("mixer").parents("form:first").submit());
                            console.log("SUBMIT");
                            //window.jq211 = jQuery.noConflict();
                            //console.log("INSIDE:" + window.jq211);
                        }
                    );
                    wexout.close();
                }
            );
            //console.log(" hello " + window.jq211);
            //            //wexout.write(page.content);
            //            //wexout.flush();
            //            //wexout.close();
            //            ////phantom.exit();
            //        }
            //    );
            //}
            //wexout.write(page.content);
            //wexout.flush();
            //wexout.close();
        }
    );
}


/**
 * Let's get this party started!
 */
handle_request()
