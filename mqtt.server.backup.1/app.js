// MQTT sever
// ***********

var mosca = require('mosca');
var server = new mosca.Server({
    port: 3882,
    bundle: true
        //}
});


server.on('ready', setup);
var counter = 1;

server.on('clientConnected', function(client) {
    console.log('client connected', client.id);
    client.token = 'abcTesting:'+counter;
    console.log('client token', client.token);
    ++counter;
});

server.on('published', function(packet, client) {

    console.log('Published topic', packet.topic);
    console.log('Published.payload', packet.payload);
    console.log('Published retain', packet.retain);
    console.log('Published qos', packet.qos);
    console.log('Published more', packet.more);
    if (typeof client != 'undefined') {
        console.log('client token', client.token);
    }
});

server.on('subscribed', function(topic, client) {
    console.log("Subscribed topic :=", topic);
    console.log("Subscribed client:=", client);
});



function setup() {
    console.log('Mosca server is up and running')
}
console.log(process.pid);