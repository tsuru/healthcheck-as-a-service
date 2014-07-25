# Copyright 2014 healthcheck-as-a-service authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

from flask.ext.admin import BaseView, expose


class HealthcheckAdmin(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')


class UrlAdmin(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')


class WatcherAdmin(BaseView):
    @expose('/')
    def index(self):
        return self.render('index.html')
