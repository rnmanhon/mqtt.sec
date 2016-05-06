var config = require('./config'),
    //    fs = require('fs'),
    //    https = require('https'),
    //    Root = require('./controllers/root').Root,
    //    IDM = require("./lib/idm.js").IDM,
    //    errorhandler = require('errorhandler');

    config.azf = config.azf || {};

var mosca = require('mosca');
var Bunyan = require('bunyan');
var logger = Bunyan.createLogger({
    name: 'pepServer',
    streams: [{
        level: Bunyan.DEBUG,
        path: './log.log'
    }]
});

// ?? need to use this with AuthzForce?
// populate the token for PEP user which is used to check token in the future
log.info('Starting PEP proxy. Keystone authentication ...');
IDM.authenticate(function(token) {
    log.info('Success authenticating PEP proxy. Proxy Auth-token: ', token);
}, function(status, e) {
    log.error('Error in keystone communication', e);
});
// ??????


var server = new mosca.Server({
    port: config.mqtt_port,
    bundle: true
});

server.on('ready', setup);

function setup() {
    console.log('Mosca server is up and running port ' + server.port)
    server.authenticate = authenticate;
    server.authorizePublish = authorizePublish;
    server.authorizeSubscribe = authorizeSubscribe;
}


/ Accepts the connection if the username and password are valid
var authenticate = function(client, username, password, callback) {




    var authorized = (username === 'alice' && password === 'secret');
    if authorized client.user = username;
    callback(null, authorized);
}

// In this case the client authorized as alice can publish to /users/alice taking
// the username from the topic and verifing it is the same of the authorized user
var authorizePublish = function(client, topic, payload, callback) {
    callback(null, client.user == topic.split('/')[1]);
}

// In this case the client authorized as alice can subscribe to /users/alice taking
// the username from the topic and verifing it is the same of the authorized user
var authorizeSubscribe = function(client, topic, callback) {
    callback(null, client.user == topic.split('/')[1]);
}









var log = require('./lib/logger').logger.getLogger("Server");





var express = require('express');

process.on('uncaughtException', function(err) {
    log.error('Caught exception: ' + err);
});
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

var app = express();

//app.use(express.bodyParser());

app.use(function(req, res, next) {
    var bodyChunks = [];
    req.on('data', function(chunk) {
        bodyChunks.push(chunk);
    });

    req.on('end', function() {
        req.body = Buffer.concat(bodyChunks);
        next();
    });
});

app.use(errorhandler({
    log: log.error
}))

app.use(function(req, res, next) {
    "use strict";
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'HEAD, POST, GET, OPTIONS, DELETE');
    res.header('Access-Control-Allow-Headers', 'origin, content-type, X-Auth-Token, Tenant-ID, Authorization');
    //log.debug("New Request: ", req.method);
    if (req.method == 'OPTIONS') {
        log.debug("CORS request");
        res.statusCode = 200;
        res.header('Content-Length', '0');
        res.send();
        res.end();
    } else {
        next();
    }
});

var port = config.pep_port || 80;
if (config.https.enabled) port = config.https.port || 443;
app.set('port', port);

for (var p in config.public_paths) {
    log.debug('Public paths', config.public_paths[p]);
    app.all(config.public_paths[p], Root.public);
}

app.all('/*', Root.pep);

if (config.tokens_engine === 'keystone' && config.azf.enabled === true) {
    log.error('Keystone token engine is not compatible with AuthZForce. Please review configuration file.');
    return;
}


if (config.https.enabled === true) {
    var options = {
        key: fs.readFileSync(config.https.key_file),
        cert: fs.readFileSync(config.https.cert_file)
    };

    https.createServer(options, function(req, res) {
        app.handle(req, res);
    }).listen(app.get('port'));
} else {
    app.listen(app.get('port'));
}