
var mqtt = require('mqtt');

var KEY = __dirname + '/ssl/agent2-key.pem';
var CERT = __dirname + '/ssl/agent2-cert.pem';

//var PORT = 8443;
var PORT = 3880;

var options = {
  keyPath: KEY,
  certPath: CERT,
  rejectUnauthorized : false 
};

var client = mqtt.createSecureClient(PORT, options);

client.subscribe('messages');
client.publish('messages', 'Current time is: ' + new Date());
client.on('message', function(topic, message) {
  console.log(message);
});

