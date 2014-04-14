from flask import Flask, request

import inspect


app = Flask(__name__)


@app.route("/resources/<name>", methods=["POST"])
def bind(name):
    return "", 201


@app.route("/resources/<name>/hostname/<host>", methods=["DELETE"])
def unbind(name, host):
    return "", 200


@app.route("/resources", methods=["POST"])
def add_instance():
    return "", 201


@app.route("/resources/<name>", methods=["DELETE"])
def remove_instance(name):
    return "", 200


@app.route("/resources/<name>/status", methods=["GET"])
def status(name):
    return "", 204


@app.route("/url", methods=["POST"])
def add_url():
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    name = request.form.get("name")
    url = request.form.get("url")
    zabbix.add_url(name, url)
    return "", 201


@app.route("/watcher", methods=["POST"])
def add_watcher():
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    name = request.form.get("name")
    watcher = request.form.get("watcher")
    zabbix.add_watcher(name, watcher)
    return "", 201


@app.route("/", methods=["POST"])
def new():
    from healthcheck.backends import Zabbix
    zabbix = Zabbix()
    name = request.form.get("name")
    zabbix.new(name)
    return "", 201


@app.route("/plugin", methods=["GET"])
def plugin():
    from healthcheck import plugin
    source = inspect.getsource(plugin)
    return source, 200
