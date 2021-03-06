var mqtt = require('mqtt'),
    util = require('util'),
    fs = require('fs'),
    path = require('path');

var script = path.basename(process.argv[1]);

if (process.argv.length < 4) {
    console.log("Usage: node %s [<host>:]<port>  <mapfile>", script)
    process.exit(-1);
}

var connect = process.argv[2] || "1883",
    host = 'localhost',
    port,
    secPort;

if (connect.indexOf(':') != -1) {
    host = connect.split(':')[0];
    port = connect.split(':')[1];
} else {
    port = connect;
}
secPort = (parseInt(port) + 1).toString();

console.log("%s: %s %s:%s (Use Cntl-c to exit)", script, "Listening on", host, port)


function refreshMap() {
    // Replace with an on HUP signal and rebuild with reg ex?
    return require(__dirname + '/' + process.argv[3] || 'map.json');
}

function getMap(client) {
    var maps = refreshMap();
    var map;

    test = function(a, b) {
        b = (b === 'undefined') ? "" : b;
        s = new RegExp(a.replace('*', '\.*') + '$')
        return s.test(b);
    }

    for (i in maps) {
        if (this.test(maps[i].username, client.username) &&
            this.test(maps[i].clientId, client.clientId)) {
            map = i; // find first match
            break;
        }
    }
    return (map === 'undefined') ? null : maps[map];
}

function handleClient(client) {

    console.log("on client ..")

    var self = this;

    if (!self.proxies) self.proxies = {};
    if (!self.clients) self.clients = {};

    process.on('SIGINT', function() {
        console.log('Received interrupt');
        for (c in self.clients) {
            self.clients[c].emit('close');
        }
        process.exit();
    });

    client.now = function() {
        return (new Date()).valueOf();
    };

    client.on('connect', function(packet) {

        client.timestamp = client.now();
        client.id = packet.clientId + '-' + client.timestamp;
        client.subscriptions = [];

        var options = {}
        options.clientId = client.id;
        if ('username' in packet) {
            options.username = packet.username;
            options.password = packet.password;
        }

        var map = getMap(packet)
        if (!map) {
            console.log('WARNING: Failed to find map for: (%s) ', packet.clientId);
            client.connack({
                returnCode: 3
            });
            return;
        }

        console.log("CONNECT: client id: " + client.id);
        console.log("CONNECT: user name: " + packet.username);
        console.log("CONNECT: password: " + packet.password);

        options.port = map.port;
        options.host = map.host;
        options.clean = packet.clean;
        options.keepalive = packet.keepalive;
        client.keepalive = packet.keepalive;
        options.dup = packet.dup;
        options.qos = packet.qos;
        options.protocolVersion = packet.protocolVersion;
        options.protocolId = packet.protocolId;

        self.proxies[client.id] = mqtt.connect(options);
        self.clients[client.id] = client;

        var rc = 0;
        var proxy = self.proxies[client.id]
        var stream = self.proxies[client.id].stream

        stream.on('connect', function() {
            console.log('Proxy stream connect')
        });

        stream.on('error', function(e) {
            console.log('Proxy stream error')
            console.log(e);

            // for some reason client.connack fails here
            // so we store rc globally and it gets
            // returned on close

            switch (e.code) {
                case 'ECONNREFUSED':
                    rc = 3;
                    // Todo: Add mores codes
                default:
                    rc = 3;
            }
        });

        stream.on('close', function(e) {
            console.log('Proxy stream close')

            client.connack({
                returnCode: rc
            });
            client.end();
            this.end();
            delete self.proxies[client.id];
            delete self.clients[client.id];
        });
        
//        stream.on('packet', function() {
//            console.log('Proxy stream packet');
//        });

        proxy.on('connect', function() {
            console.log('Proxy connect');
            client.connack({
                returnCode: rc
            });
        });
        

        proxy.on('error', function(e) {
            //Check for Auth errors!
            console.log('Proxy: ' + e);
            rc = 1
            if (e.toString().indexOf('Not authorized')) {
                rc = 5;
            } // Todo: Add more checks.  
            proxy.end();
        });


        proxy.on('message', function(topic, payload, qos) {
            var delta = Math.round(1 / 1000 * (client.now() - client.timestamp));
            console.log('Proxy message: ' + payload);

            // ping requests are not proxied
            // so if client has gone away, close connections
            if (client.keepalive - delta < 0) {
                console.log('Keep alive timeout on client');
                client.emit('close');
                return;
            }

            var c = client;
            for (var i = 0; i < c.subscriptions.length; i++) {
                var s = c.subscriptions[i];
                if (s.test(topic)) {
                    c.publish({
                        topic: topic,
                        payload: payload
                    });
                    break;
                }
            }
        });

        // Not sure if we need these ... 
        proxy.on('puback', function(_packet) {
            console.log('Proxy puback: ' + _packet);
            client.puback(_packet)
        });

        proxy.on('pubrel', function(_packet) {
            console.log('Proxy pubrel: ' + _packet);
            client.pubrel(_packet);
        });

        proxy.on('pubrec', function(_packet) {
            console.log('Proxy pubrec: ' + _packet);
            client.pubrel(_packet);
        });

        proxy.on('suback', function(_packet) {
            console.log('Proxy suback.. ');
            client.suback({
                messageId: _packet.messageId,
                granted: _packet.subscriptions.map(function(e) {
                    return e.qos;
                })
            });
        });


        proxy.on('disconnect', function(rc) {
            console.log('Proxy disconnect');
        });

    });


    client.on('subscribe', function(packet) {
        var granted = [];

        console.log("SUBSCRIBE(%s): %j", client.id, packet);

        for (var i = 0; i < packet.subscriptions.length; i++) {
            console.log('subscribe topic ' + i + ' : ' + packet.subscriptions[i].topic);
            var qos = packet.subscriptions[i].qos,
                topic = packet.subscriptions[i].topic,
                reg = new RegExp(topic.replace(new RegExp('\/', "g"), '\\/').replace('\$', '\\$').replace('+', '[^\/]+').replace('#', '.+', 'g') + '$');

            console.log('subscribe reg ' + i + ' : ' + reg);
            granted.push(qos);
            client.subscriptions.push(reg);
            if (client.id in self.proxies) {
                self.proxies[client.id].publish('proxyPoll', "poll from proxy ...", qos)
                self.proxies[client.id].subscribe(topic, qos);
                console.log('subscribe to proxy topic: ' + topic + ' qos: ' + qos);
            }
        }
//        client.suback({
//            messageId: packet.messageId,
//            granted: packet.subscriptions.map(function(e) {
//                return e.qos;
//            })
//        });

    });

    client.on('publish', function(packet) {
        console.log("PUBLISH(%s): %j", client.id, packet);
        if (client.id in self.proxies)
            self.proxies[client.id].publish(packet.topic, packet.payload, packet.qos)
    });

    client.on('pingreq', function(packet) {
        console.log('PINGREQ(%s)', client.id);
        if (client.id in self.proxies && self.proxies[client.id].connected)
            client.timestamp = (new Date()).valueOf();
        client.pingresp();
    });

    client.on('disconnect', function(packet) {
        if (client.id in self.proxies)
            self.proxies[client.id].end();
    });


    client.on('close', function(packet) {
        console.log("Client: close (%s)", packet)
        if (client.id in self.proxies)
            self.proxies[client.id].end();
        client.end();
        delete self.proxies[client.id];
        delete self.clients[client.id];
    });


    client.on('error', function(e) {
        client.stream.end();
        delete self.proxies[client.id];
        delete self.clients[client.id];
        console.log('Client error: (%s)', (e === 'undefined') ? '' : e);
    });

}


console.log("before normal mqtt create server")
var server = new mqtt.MqttServer(handleClient).listen(port, host);



var KEY = __dirname + '/ssl/agent1-key.pem';
var CERT = __dirname + '/ssl/agent1-cert.pem';
var opts = {};

if ('string' === typeof KEY && 'string' === typeof CERT) {
    opts.key = fs.readFileSync(KEY);
    opts.cert = fs.readFileSync(CERT);
} else if ('object' === typeof keyPath) {
    opts = keyPath;
    listener = certPath;
}

server.on('error', function(e) {
    console.log(script + ": %s", e);
});


console.log("before secured mqtt create server")
var secServer = new mqtt.MqttSecureServer(opts, handleClient).listen(secPort, host);

secServer.on('error', function(e) {
    console.log(script + ": %s", e);
});

console.log('Server listen on port %s', port);
console.log('Server listen on sec port %s', secPort);
console.log('Server listen on host %s', host);