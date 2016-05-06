var config = {};

config.pep_port = 80;

// Set this var to undefined if you don't want the server to listen on HTTPS
config.https = {
    enabled: false,
    cert_file: 'cert/cert.crt',
    key_file: 'cert/key.key',
    port: 443
};

config.account_host = 'https://account.lab.fiware.org';

config.keystone_host = 'idm';
config.keystone_port = 5000;

config.app_host = 'www.google.es';
config.app_port = '80';
// Use true if the app server listens in https
config.app_ssl = false;

// Credentials obtained when registering PEP Proxy in Account Portal
config.username = 'idm';
config.password = 'idm';

// in seconds
config.chache_time = 300;

// if enabled PEP checks permissions with AuthZForce GE. 
// only compatible with oauth2 tokens engine
//
// you can use custom policy checks by including programatic scripts 
// in policies folder. An script template is included there
config.azf = {
//      enabled: false,
//    host: 'auth.lab.fiware.org',
//    port: 6019,
//    path: '/authzforce/domains/',
//    custom_policy: undefined // use undefined to default policy checks (HTTP verb + path).
        enabled: true,
    host: 'authzforce',
    protocol: 'http',
    port: 8080,
    path: '/authzforce/domains/',
        app_azf_domain: 'A0bdIbmGEeWhFwcKrC9gSQ',
    custom_policy: undefined // use undefined to default policy checks (HTTP verb + path).
};

// list of paths that will not check authentication/authorization
// example: ['/public/*', '/static/css/']
config.public_paths = [];

// options: oauth2/keystone
config.tokens_engine = 'oauth2';

config.magic_key = undefined;

module.exports = config;