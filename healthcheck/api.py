# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from flask import Flask, request
from flask.ext.admin import Admin

from healthcheck import admin as hadmin

import inspect
import os


app = Flask(__name__)
app.debug = os.environ.get("API_DEBUG", "0") in ("True", "true", "1")

admin = Admin(app, name="Tsuru healthcheck service")
admin.add_view(
    hadmin.HealthcheckAdmin(name='healthchecks', endpoint='healthchecks'))
admin.add_view(hadmin.UrlAdmin(name='urls', endpoint='urls'))
admin.add_view(hadmin.WatcherAdmin(name='watchers', endpoint='watchers'))


def get_manager():
    from healthcheck.backends import Zabbix
    managers = {
        "zabbix": Zabbix(),
    }
    manager = os.environ.get("API_MANAGER", "zabbix")
    manager_class = managers.get(manager)
    if manager_class:
        return manager_class
    raise ValueError("{0} is not a valid manager".format(manager))


@app.route("/url", methods=["POST"])
def add_url():
    name = request.form.get("name")
    url = request.form.get("url")
    get_manager().add_url(name, url)
    return "", 201


@app.route("/<name>/url/<path:url>", methods=["DELETE"])
def remove_url(name, url):
    get_manager().remove_url(name, url)
    return "", 204


@app.route("/watcher", methods=["POST"])
def add_watcher():
    name = request.form.get("name")
    watcher = request.form.get("watcher")
    get_manager().add_watcher(name, watcher)
    return "", 201


@app.route("/<name>/watcher/<watcher>", methods=["DELETE"])
def remove_watcher(name, watcher):
    get_manager().remove_watcher(name, watcher)
    return "", 204


@app.route("/resources", methods=["POST"])
def new():
    name = request.form.get("name")
    get_manager().new(name)
    return "", 201


@app.route("/resources/<name>", methods=["DELETE"])
def remove(name):
    get_manager().remove(name)
    return "", 204


@app.route("/plugin", methods=["GET"])
def plugin():
    from healthcheck import plugin
    source = inspect.getsource(plugin)
    return source, 200


if __name__ == "__main__":
    app.run(port=8888, debug=True)
