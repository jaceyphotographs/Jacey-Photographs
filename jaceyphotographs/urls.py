# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *

urlpatterns = patterns('jaceyphotographs.views',
    (r'^$','index'),
    (r'^(\d{4})/([a-z]{3})/(\w{1,2})/(?P<slug>[-\w]+)/$','slug'),
    (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/(?P<day>\w{1,2})/$','archive_day'),
    (r'^(?P<year>\d{4})/(?P<month>[a-z]{3})/$','archive_month'),
    (r'^(?P<year>\d{4})/$','archive_year'),
    (r'^contact/$', 'email_jacey'),
    (r'^admin/$', 'admin'),
    (r'^admin/post/new/$','blog_post'),
    (r'^admin/post/edit/(?P<key>\w*)/$','blog_post'),
    (r'^admin/post/delete/$','blog_entry_delete'),
    (r'^admin/post/comment/$','comment_post'),
    (r'^about/$','about'),
    (r'^details/$','details'),
    (r'^tags/(?P<tag_name>\w+)/$','tags'),
    (r'^feed/$','rss_feed'),
    (r'^sitemap.xml$','sitemap'),
    (r'^images$', 'serve_image'),
)