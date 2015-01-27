from django.conf.urls import patterns, include, url
from django.contrib import admin


urlpatterns = patterns('',
                       # Examples:
                       # url(r'^$', 'rest.views.home', name='home'),
                       # url(r'^blog/', include('blog.urls')),
                       url(r'^api-auth/', include('rest_framework.urls',
                                             namespace='rest_framework')),
                       url('', include(
                           'social.apps.django_app.urls', namespace='social')),
                       url(r'^$', 'mysite.views.login'),
                       url(r'^home/$', 'mysite.views.home'),
                       url(r'^logout/$', 'mysite.views.logout'),
                       url(r'^login/$', 'mysite.views.login'),
                       url(r'^', include('mysite.urls')),


                       url(r'^admin/', include(admin.site.urls)),
                       )
