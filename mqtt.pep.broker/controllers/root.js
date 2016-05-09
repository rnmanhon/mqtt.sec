var config = require('./../config.js'),
    //    proxy = require('./../lib/HTTPClient.js'),
    IDM = require('./../lib/idm.js').IDM,
    AZF = require('./../lib/azf.js').AZF;

var Bunyan = require('bunyan');
var logger = Bunyan.createLogger({
    name: 'pepRoot',
    streams: [{
        level: Bunyan.DEBUG,
        path: './log.log'
    }]
});

var Root = (function() {
    var pep = function(auth_token, action, topic) {

        return new Promise(function(success, fail) {
            if (auth_token === undefined) {
                logger.error('Auth-token not found!');
                fail("Auth-token not found");
            } else {
                if (config.magic_key && config.magic_key === auth_token) {
                    logger.info('auth_token equal to magic key, Access allowed!');
                    success();
                }

                IDM.check_token(auth_token, function(user_info) {
                    if (config.azf.enabled) {

                        AZF.check_permissions(auth_token, user_info, action, topic, function() {
                            logger.info('auth_token valid (azf enabled)!');
                            success();
                        }, function(status, e) {
                            if (status === 401) {
                                log.error('User access-token not authorized by AZF: ', e);
                                fail('User access-token not authorized by AZF');
                            } else if (status === 404) {
                                log.error('Domain not found in AZF: ', e);
                                fail('Domain not found in AZF');
                            } else {
                                log.error('Error in AZF communication ', e);
                                fail('Error in AZF communication');
                            }
                        });
                    } else {
                        logger.info('auth_token valid (azf disabled)!');
                        success();
                    }

                }, function(status, e) {
                    if (status === 404) {
                        log.error('User access-token not authorized by IDM');
                        fail('User access-token not authorized by IDM');
                    } else {
                        log.error('Error in IDM communication ', e);
                        fail('Error in IDM communication');
                    }
                });
            }

        })

    }







    return {
        pep: pep,
        //        public: public
    }
})();

exports.Root = Root;