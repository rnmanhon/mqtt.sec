// MQTT sever
// ***********

var mosca = require('mosca');
var server = new mosca.Server({
    port: 3881,
    bundle: true
  //}
});


server.on('ready', setup);
 
server.on('clientConnected', function(client) {
      console.log('client connected', client.id);     
});
 
server.on('published', function(packet, client) {
    
    console.log('Published topic', packet.topic);
    console.log('Published.payload', packet.payload);
    console.log('Published retain', packet.retain);
    console.log('Published qos', packet.qos);
    console.log('Published more', packet.more);
        
});

function setup() {
    console.log('Mosca server is up and running')
}
console.log(process.pid);
