# healthcheck-as-a-service

[![Build Status](https://travis-ci.org/tsuru/healthcheck-as-a-service.png?branch=master)](https://travis-ci.org/tsuru/healthcheck-as-a-service)

This project is a http API to abstract healthcheck operations, like verify if a web application is working fine and notify to some users if some of this applications are in trouble.

## supported backends:

 * [zabbix](http://zabbix.com)
    
## configuring

TODO

## deploying

TODO

## development

 * [Source hosted at GitHub](http://github.com/tsuru/healthcheck-as-a-service)
 * [Report issues on GitHub Issues](http://github.com/tsuru/healthcheck-as-a-service/issues)

Pull requests are very welcomed! Make sure your patches are well tested.

### Running tests

If you are using a virtualenv, all you need is:

    $ make test
