var querystring = require('querystring');
var stringify = require('json-stringify-safe');
var _ = require('lodash-getpath');
var config = require('./../config.js');

var apiOptions = {
    keystoneServer: "http://" + config.keystone_host + ":" + config.keystone_port,
    horizonServer: "http://" + config.horizon_host + ":" + config.horizon_port
};

var sendJSONresponse = function(res, status, content) {
    res.status(status);
    res.json(content);
};


/* grant access token*/
module.exports.grantAccessToken = function(userID, userPassword) {
    var requestOptions, path;
    console.log('grantAccessToken .... ');

    // get application secert
    console.log('get application secret .... ');
    console.log("grantAccessToken req body %j ", req.body);

    var clientID = _.getPath(req, "body.state");
    var userCode = _.getPath(req, "body.code");
    path = "/v3/OS-OAUTH2/consumers/" + clientID;
    requestOptions = {
        url: apiOptions.keystoneServer + path,
        method: "GET",
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Auth-Token': 'ADMIN'
        },
        json: {}
    };
    request(
        requestOptions,
        function(err, response, body) {
            var i, data;
            console.log('after return from keystone server .... ');

            if ((typeof(response) != "undefined") &&
                (response.statusCode === 200)) {
                console.log('return body are %j', body);

                var clientSecret = _.getPath(body, "consumer.secret");
                var consumerDetail = _.getPath(body, "consumer");
                console.log('consumer detail is  %j', consumerDetail);
                doGetAccessToken(userCode, clientID, clientSecret, consumerDetail, res);
                //                sendJSONresponse(res, 200, {
                //                    "message": "list of apps ...",
                //                    "accessToken": 
                //                });
            } else {
                console.log('err %j', err);
                console.log('response %j ', response);
                sendJSONresponse(res, 200, {
                    "message": err
                });
            }
        }
    );
}; // grantAccessToken


var doGetAccessToken = function(userCode, cilentID, clientSecret, consumerDetail, res) {
    var requestOptions, path;
    console.log('doGetAccessToken .... ');
    path = "/oauth2/token";
    var auth = "Basic " + new Buffer(cilentID + ":" + clientSecret).toString("base64");
    var form = {
        grant_type: consumerDetail.grant_type,
        code: userCode,
        redirect_uri: consumerDetail.url
    };
    var formData = querystring.stringify(form);
    var contentLength = formData.length;

    //    console.log('grant_type ' + consumerDetail.grant_type);
    //    console.log('code ' + userCode);
    //    console.log('redirect_uri ' + consumerDetail.url);
    console.log('form %j ', form);
    console.log('formData ' + formData);
    console.log('contentLength ' + contentLength);

    requestOptions = {
        url: apiOptions.horizonServer + path,
        method: "POST",
        //        'auth': {
        //            'user': cilentID,
        //            'pass': clientSecret,
        //            'sendImmediately': false
        //        },
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            "Authorization": auth,
            'Content-Length': contentLength,
        },
        //        body: form,  
        body: formData,

        //        form: {
        //            grant_type: consumerDetail.grant_type,
        //            code: userCode,
        //            redirect_uri: consumerDetail.url,
        //            test: 'test'
        //        },
        //        json: {}
    };
    console.log("requestOptions  %j ", requestOptions);

    request(
        requestOptions,
        function(err, response, body) {
            var i, data;
            console.log('after return from horizon server .... ');
            console.log('tken return response are %j', response);
            console.log('tken return body are %j', JSON.parse(body));

            if ((typeof(response) != "undefined") &&
                (response.statusCode === 200)) {

                var accessToken = _.getPath(JSON.parse(body), "access_token");
                console.log('accessToken  is ', accessToken);
                sendJSONresponse(res, 200, {
                    "message": "accessToken  ...",
                    "accessToken": accessToken,
                    "authorizedApp": consumerDetail.name,
                });
            } else {
                console.log('err %j', err);
                console.log('response %j ', response);
                sendJSONresponse(res, 200, {
                    "message": err
                });
            }
        }
    );  // request





}