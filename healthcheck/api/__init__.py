import flask


app = flask.Flask(__name__)


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
