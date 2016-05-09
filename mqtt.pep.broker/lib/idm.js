var config = require('../config.js'),
    proxy = require('./HTTPClient.js');
var querystring = require('querystring');
var request = require('request');
var Bunyan = require('bunyan');
var logger = Bunyan.createLogger({
    name: 'pepIdm',
    streams: [{
        level: Bunyan.DEBUG,
        path: './log.log'
    }]
});

var IDM = (function() {

    var my_token,
        //{token: {user_info: {}, date: Date}}
        tokens_cache = {};

    var authenticate = function(callback, callbackError) {

        var options = {
            host: config.keystone_host,
            port: config.keystone_port,
            path: '/v3/auth/tokens',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        };
        var body = {
            auth: {
                identity: {
                    methods: ['password'],
                    password: {
                        user: {
                            name: config.username,
                            password: config.password,
                            domain: {
                                id: "default"
                            }
                        }
                    }
                }
            }
        };
        proxy.sendData('http', options, JSON.stringify(body), undefined, function(status, resp, headers) {
            my_token = headers['x-subject-token'];
            callback(my_token);
        }, callbackError);
    };

    var check_token = function(token, callback, callbackError) {
        var options;
        logger.info('token . . ->' + token + '<-');

        if (config.tokens_engine === 'keystone') {
            options = {
                host: config.keystone_host,
                port: config.keystone_port,
                path: '/v3/auth/tokens/',
                method: 'GET',
                headers: {
                    'X-Auth-Token': my_token,
                    'X-Subject-Token': encodeURIComponent(token),
                    'Accept': 'application/json'
                }
            };
        } else {
            options = {
                host: config.keystone_host,
                port: config.keystone_port,
                path: '/v3/access-tokens/' + encodeURIComponent(token),
                method: 'GET',
                headers: {
                    'X-Auth-Token': my_token,
                    'Accept': 'application/json'
                }
            };
        }

        if (tokens_cache[token]) {
            logger.info('Token in cache, checking timestamp...');
            var current_time = (new Date()).getTime();
            var token_time = tokens_cache[token].date.getTime();

            if (current_time - token_time < config.chache_time * 1000) {
                tokens_cache[token].date = new Date();
                callback(tokens_cache[token].user_info);
                return;
            } else {
                log.info('Token in cache expired');
                delete tokens_cache[token];
            }
        }

        logger.info('Checking token with IDM...');
        logger.info('options %j...', options);

        proxy.sendData('http', options, undefined, undefined, function(status, resp) {
            var user_info = JSON.parse(resp);
            tokens_cache[token] = {};
            tokens_cache[token].date = new Date();
            tokens_cache[token].user_info = user_info;
            logger.debug(JSON.stringify(user_info));
            callback(user_info);
        }, function(status, e) {
            if (status === 401) {
                logger.error('Error validating token. Proxy not authorized in keystone. Keystone authentication ...');
                authenticate(function(status, resp) {
                    my_token = JSON.parse(resp).access.token.id;
                    logger.info('Success authenticating PEP proxy. Proxy Auth-token: ', my_token);
                    check_token(token, callback, callbackError);
                }, function(status, e) {
                    logger.error('Error in IDM communication ', e);
                    callbackError(503, 'Error in IDM communication');
                });
            } else {
                callbackError(status, e);
            }
        });
    };


    //    var grantAccessToken = function(userName, userPassword, callback, callbackError) {
    var grantAccessToken = function(userName, userPassword) {
        return new Promise(function(callback, callbackError) {
                var apiOptions = {
                    horizonServer: "http://" + config.horizon_host + ":" + config.horizon_port
                };

                var requestOptions;
                var path = "/oauth2/token";
                logger.info('grantAccessToken .... ');

                var clientID = config.app_id;
                var clientSecret = config.app_secret;

                var auth = "Basic " + new Buffer(clientID + ":" + clientSecret).toString("base64");
                var form = {
                    grant_type: 'password',
                    username: userName,
                    password: userPassword,
                    redirect_uri: config.app_redirectUrl
                };

                logger.debug('redirect_uri ' + form.redirect_uri);
                var formData = querystring.stringify(form);
                var contentLength = formData.length;

                logger.debug('form %j ', form);
                logger.debug('formData ' + formData);
                logger.debug('contentLength ' + contentLength);

                requestOptions = {
                    url: apiOptions.horizonServer + path,
                    method: "POST",
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept': 'application/json',
                        "Authorization": auth,
                        'Content-Length': contentLength,
                    },
                    body: formData,
                };
                logger.debug("requestOptions  %j ", requestOptions);

                request(
                    requestOptions,
                    function(err, response, body) {
                        var i, data;
                        logger.info('after return from horizon server .... ');
                        logger.debug('token return response are %j', response);
                        logger.debug('token return body are %j', JSON.parse(body));

                        if ((typeof(response) != "undefined") &&
                            (response.statusCode === 200)) {

                            var accessToken = _.getPath(JSON.parse(body), "access_token");
                            console.log('accessToken  is ', accessToken);
                            callback(accessToken);
                        } else {
                            console.log('err %j', err);
                            console.log('response %j ', response);
                            callbackError(503, 'Error in getting access token from IDM');
                        }
                    }
                ); // request
            }) // Promise
    };

    return {
        authenticate: authenticate,
        check_token: check_token,
        grantAccessToken: grantAccessToken
    }

})();
exports.IDM = IDM;