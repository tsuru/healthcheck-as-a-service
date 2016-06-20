# healthcheck-as-a-service

[![Build Status](https://travis-ci.org/tsuru/healthcheck-as-a-service.png?branch=master)](https://travis-ci.org/tsuru/healthcheck-as-a-service)

This project is a http API to abstract healthcheck operations, like verify if a web application is working fine and notify to some users if some of this applications are in trouble.

## supported backends:

 * [zabbix](http://zabbix.com)

## configuring

* `API_URL` - the api base url
* `API_DEBUG` - enables the debug mode

### zabbix backend

* `ZABBIX_URL` - the zabbix api endpoint
* `ZABBIX_USER` - zabbix user
* `ZABBIX_PASSWORD` - zabbix password
* `ZABBIX_HOST_GROUP` - host group used to create the web monitoring
* `ZABBIX_HOST` - host used to create the web monitoring


## deploying

TODO

## installing healthcheck tsuru plugin

tsuru plugin-install hc <API-URL>/plugin

## using healtch tsuru plugin

### creating a new healtcheck

    $ tsuru service-instance-add <healthcheck-service> <healthcheck-name>

### removing a healthcheck

    $ tsuru service-instance-remove <healthcheck-service> <healthcheck-name>

### adding a new url to be monitored

    $ tsuru hc add-url <healthcheck-name> <url> [expected string]

## removing a url

    $ tsuru hc remove-url <healthcheck-name> <url>

## adding a new watcher

    $ tsuru hc add-watcher <healthcheck-name> <email>

## removing a watcher

    $ tsuru hc remove-watcher <healthcheck-name> <email>

## development

 * [Source hosted at GitHub](http://github.com/tsuru/healthcheck-as-a-service)
 * [Report issues on GitHub Issues](http://github.com/tsuru/healthcheck-as-a-service/issues)

Pull requests are very welcomed! Make sure your patches are well tested.

### Running tests

If you are using a virtualenv, all you need is:

    $ make test
