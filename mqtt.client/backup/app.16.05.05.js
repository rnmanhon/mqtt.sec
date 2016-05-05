// MQTT client
// ***********
var mosca = require('mosca');
var mqtt = require('mqtt');

var mqttClient = mqtt.connect("mqtt://localhost:3881");


var server = new mosca.Server({
    port: 3880,
    bundle: true
});
server.on('ready', setup);
var token = "asdfasdf";

server.on('clientConnected', function(client) {
    // do the authentication and get the token


    console.log('client connected', client.id);
});

server.on('published', function(packet, client) {
    if (packet.topic.indexOf('$SYS') === 0) {
        return;
    }

    console.log('Published topic', packet.topic);
    console.log('Published.payload', packet.payload);
    console.log('Published retain', packet.retain);
    console.log('Published qos', packet.qos);

    mqttClient.publish(
        //        "pep/" + packet.topic + "/" + token, {
        packet.topic, {
            token: token,
            payload: packet.payload
        }, {
            retain: packet.retain,
            qos: packet.qos
        });

    //    topic: 'echo/' + packet.topic,
    //    payload: packet.payload,
    //    retain: packet.retain,
    //    qos: packet.qos    
    //console.log('Published', packet.toString());
});

server.on('subscribed', function(topic, client) {
    console.log("Subscribed :=", client.packet);
    console.log("Subscribed topic :=", topic);

    mqttClient.subscribed(
        "pep/" + client.topic + "/" + token,
        packet.payload, {
            retain: packet.retain,
            qos: packet.qos
        });

});




function setup() {
    console.log('Mosca client is up and running')
}
console.log(process.pid);