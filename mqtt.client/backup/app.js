var mqtt = require('mqtt');


var mqttClient = mqtt.connect("mqtt://localhost:3881");
mqttClient.on('connect', function() {
    mqttClient.subscribe('test/commands/+');
    console.log("subscribed for test command");
});


var inquirer = require("inquirer");

var preguntas = [{
    type: 'input',
    name: 'command',
    message: 'what you want to do next?',
    default: 'publish'
}, ];


while (true) {
    inquirer.prompt(preguntas, function(answer) {
        console.log(answer);
        if (answer == 'exit')
        {
            process.exit();
        }
    });
}