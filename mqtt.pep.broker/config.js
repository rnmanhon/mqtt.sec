var config = {};

config.mqtt_port = 2880;

//later for mqtt over tls
config.tls = {
    enabled: false,
    cert_file: 'cert/cert.crt',
    key_file: 'cert/key.key',
    port: 2443
};

config.azf = {
    enabled: true,
//    host: 'authzforce',
    host: 'localhost',
    protocol: 'http',
//    port: 8080,
        port: 8084,
    path: '/authzforce/domains/',
    app_azf_domain: 'A0bdIbmGEeWhFwcKrC9gSQ',
    custom_policy: undefined // use undefined to default policy checks (HTTP verb + path).
};

// Credentials obtained when registering PEP Proxy in Account Portal
config.username = 'idm';
config.password = 'idm';

config.keystone_host = 'localhost';
config.keystone_port = 5000;
config.horizon_host = 'localhost';
config.horizon_port = 8000;


// in seconds
config.chache_time = 300;

// options: oauth2/keystone
config.tokens_engine = 'oauth2';

config.app_id = '589ad81257af4de190622a56ef52726e';
config.app_secret = 'af34af2ee01940abab221f8b0969fddb';
config.app_redirectUrl = 'http://u.ray:3000/secApp';


//config.app_mqtt_host = '172.17.0.1';
//config.app_mqtt_port = '3000';
// Use true if the app server listens in https
//config.app_ssl = false;






//config.pep_port = 80;
// Set this var to undefined if you don't want the server to listen on HTTPS

config.account_host = 'https://account.lab.fiware.org';

// list of paths that will not check authentication/authorization
// example: ['/public/*', '/static/css/']
config.public_paths = [];

config.magic_key = undefined;

module.exports = config;