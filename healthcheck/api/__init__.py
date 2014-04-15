from flask import Flask, request

import inspect


app = Flask(__name__)


@app.route("/url", methods=["POST"])
def add_url():
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    name = request.form.get("name")
    url = request.form.get("url")
    zabbix.add_url(name, url)
    return "", 201


@app.route("/<name>/url/<path:url>", methods=["DELETE"])
def remove_url(name, url):
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    zabbix.remove_url(name, url)
    return "", 204


@app.route("/watcher", methods=["POST"])
def add_watcher():
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    name = request.form.get("name")
    watcher = request.form.get("watcher")
    zabbix.add_watcher(name, watcher)
    return "", 201


@app.route("/<name>/watcher/<watcher>", methods=["DELETE"])
def remove_watcher(name, watcher):
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    zabbix.remove_watcher(name, watcher)
    return "", 204


@app.route("/", methods=["POST"])
def new():
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    name = request.form.get("name")
    zabbix.new(name)
    return "", 201


@app.route("/<name>", methods=["DELETE"])
def remove(name):
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    zabbix.remove(name)
    return "", 204


@app.route("/plugin", methods=["GET"])
def plugin():
    from healthcheck import plugin
    source = inspect.getsource(plugin)
    return source, 200
