# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from flask import Flask, request
from flask_admin import Admin
from terminaltables import AsciiTable

from raven.contrib.flask import Sentry

from healthcheck import admin as hadmin
from healthcheck import auth
from healthcheck.storage import ItemNotFoundError
from healthcheck.backends import GroupNotInInstanceError, GroupNotExists

import json
import inspect
import os
import logging

app = Flask(__name__)
app.debug = os.environ.get("API_DEBUG", "0") in ("True", "true", "1")
handler = logging.StreamHandler()
if app.debug:
    logging.basicConfig(level=logging.DEBUG)
    handler.setLevel(logging.DEBUG)
else:
    handler.setLevel(logging.WARN)
app.logger.addHandler(handler)

SENTRY_DSN = os.environ.get("SENTRY_DSN")
if SENTRY_DSN:
    app.config['SENTRY_DSN'] = SENTRY_DSN
    sentry = Sentry(app)

admin = Admin(app, name="Tsuru healthcheck service")
admin.add_view(
    hadmin.HealthcheckAdmin(name='healthchecks', endpoint='healthchecks'))
admin.add_view(hadmin.UrlAdmin(name='urls', endpoint='urls'))
admin.add_view(hadmin.WatcherAdmin(name='watchers', endpoint='watchers'))


@app.errorhandler(404)
def page_not_found(e):
    return "", 404


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


@app.route("/resources/<name>/url", methods=["POST"])
@auth.required
def add_url(name):
    if not request.data:
        return "url is required", 400
    data = json.loads(request.data)
    if "url" not in data:
        return "url is required", 400
    data["name"] = name
    get_manager().add_url(**data)
    return "", 201


@app.route("/resources/<name>/url", methods=["DELETE"])
@auth.required
def remove_url(name):
    if not request.data:
        return "url is required", 400
    data = json.loads(request.data)
    if "url" not in data:
        return "url is required", 400
    data["name"] = name
    try:
        get_manager().remove_url(**data)
    except ItemNotFoundError:
        return "URL not found.", 404
    return "", 204


@app.route("/resources/<name>/url", methods=["GET"])
@auth.required
def list_urls(name):
    urls = get_manager().list_urls(name)

    if request.headers.get("accept") == "application/json":
        return json.dumps([
            {
                "url": r[0],
                "comment": r[1],
            }
            for r in urls
        ]), 200

    table_urls = [["Url", "Comment"]]
    table_urls.extend(urls)
    table = AsciiTable(table_urls)
    return table.table, 200


@app.route("/resources/<name>/watcher", methods=["POST"])
@auth.required
def add_watcher(name):
    if not request.data:
        return "watcher is required", 400

    data = json.loads(request.data)

    if "watcher" not in data:
        return "watcher is required", 400

    watcher = data["watcher"]
    password = data.get("password")

    get_manager().add_watcher(name, watcher, password)

    return "", 201


# This route only exists for compatibility with old plugin versions and its an
# alias to /resources/<name>/watcher/<watcher>
@auth.required
@app.route("/resources/<name>/<ignored>/watcher/<watcher>", methods=["DELETE"])
def remove_watcher_compat(name, ignored, watcher):
    get_manager().remove_watcher(name, watcher)
    return "", 204


@app.route("/resources/<name>/watcher/<watcher>", methods=["DELETE"])
@auth.required
def remove_watcher(name, watcher):
    get_manager().remove_watcher(name, watcher)
    return "", 204


@app.route("/resources/<name>/watcher", methods=["GET"])
@auth.required
def list_watchers(name):
    watchers = get_manager().list_watchers(name)
    return json.dumps(watchers), 200


@app.route("/resources/<name>/servicegroups", methods=["GET"])
@auth.required
def list_service_groups(name):
    keyword = request.args.get('keyword')
    if keyword:
        groups = get_manager().list_service_groups(keyword)
    else:
        groups = get_manager().list_service_groups()

    return json.dumps(groups), 200


@app.route("/resources/<name>/groups", methods=["GET"])
@auth.required
def list_groups(name):
    groups = get_manager().list_groups(name)
    return json.dumps(groups), 200


@app.route("/resources/<name>/groups", methods=["POST"])
@auth.required
def add_group(name):
    if not request.data:
        return "group is required", 400

    data = json.loads(request.data)

    if "group" not in data:
        return "group is required", 400

    group = data["group"]
    get_manager().add_group(name, group)

    return "", 201


@app.route("/resources/<name>/groups", methods=["DELETE"])
@auth.required
def remove_group(name):
    if not request.data:
        return "group is required", 400

    data = json.loads(request.data)
    if "group" not in data:
        return "group is required", 400

    try:
        get_manager().remove_group(name, data["group"])
    except GroupNotInInstanceError:
        return "group not found in instance", 400
    except GroupNotExists:
        return "group not exists", 400

    return "", 204


@app.route("/resources", methods=["POST"])
@auth.required
def new():
    name = request.form.get("name")
    get_manager().new(name)
    return "", 201


@app.route("/resources/<name>", methods=["DELETE"])
@auth.required
def remove(name):
    get_manager().remove(name)
    return "", 204


@app.route("/plugin", methods=["GET"])
def plugin():
    from healthcheck import plugin
    source = inspect.getsource(plugin)
    return source, 200


@app.route("/resources/<name>/bind", methods=["POST"])
def bind_unit(name):
    return "", 201


@app.route("/resources/<name>/bind-app", methods=["POST"])
def bind_app(name):
    return "{}", 200


@app.route("/resources/<name>/bind", methods=["DELETE"])
def unbind_unit(name):
    return "", 200


@app.route("/resources/<name>/bind-app", methods=["DELETE"])
def unbind_app(name):
    return "", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8888, debug=True)
