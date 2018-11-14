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

### mongodb storage

* `MONGODB_DATABASE` - default is hcapi
* `MONGODB_URI` - mongodb full address

## deploying

### zabbix (optional)

    $ git clone git@github.com:zabbix/zabbix-docker.git
    $ cd zabbix-docker
    $ docker-compose -f docker-compose_v3_alpine_mysql_latest.yaml up -d

### hcaas

    $ git clone git@github.com:tsuru/healthcheck-as-a-service.git
    $ cd healthcheck-as-a-service
    $ tsuru app-create hcaas python
    $ tsuru env-set -a hcaas API_DEBUG=true ZABBIX_URL=$ZABBIX_URL MONGODB_URI=$MONGODB_URI
    $ tsuru app-deploy -a hcaas .
    $ export API_URL=$(tsuru app-info -a hcaas | grep Address: |awk '{print $2}')

## installing healthcheck tsuru plugin

    $ tsuru plugin-install hc <API-URL>/plugin

## using healthcheck tsuru plugin

### creating new service

edit `service.yaml` `endpoint:production` with hcaas address

    $ tsuru service create service.yaml

### creating a new healtcheck

    $ tsuru service-instance-add <healthcheck-service> <healthcheck-name>

### removing a healthcheck

    $ tsuru service-instance-remove <healthcheck-service> <healthcheck-name>

### adding a new url to be monitored

    $ tsuru hc add-url <healthcheck-service> <healthcheck-name> <url> [expected string]

## removing a url

    $ tsuru hc remove-url <healthcheck-name> <url>

## adding a new watcher

    $ tsuru hc add-watcher <healthcheck-service> <healthcheck-name> <email>

## removing a watcher

    $ tsuru hc remove-watcher <healthcheck-name> <email>

## listing service hostgroups

    $ tsuru hc list-service-groups <healthcheck-service> [search-keyword]

## adding instance to a hostgroup

    $ tsuru hc add-group <healthcheck-service> <healthcheck-name> <hostgroup-name>

## removing instance from a hostgroup

    $ tsuru hc-remove-group <healthcheck-service> <healthcheck-name> <hostgroup-name>

## listing instance hostgroups

    $ tsuru hc list-groups <healthcheck-service> <healthcheck-name>

## development

 * [Source hosted at GitHub](http://github.com/tsuru/healthcheck-as-a-service)
 * [Report issues on GitHub Issues](http://github.com/tsuru/healthcheck-as-a-service/issues)

Pull requests are very welcomed! Make sure your patches are well tested.

### Running tests

If you are using a virtualenv, all you need is:

    $ make test
