from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.settings.multisettings \
    import views as settings_views


urlpatterns = patterns('',
    url(r'^$', settings_views.MultiFormView.as_view(), name='index'),
    url(r'^accountstatus/$', settings_views.AccountStatusView.as_view(), name='status'),
    url(r'^password/$', settings_views.PasswordView.as_view(), name='password'),
    url(r'^email/$', settings_views.EmailView.as_view(), name='useremail'),
    url(r'^email/verify$', settings_views.email_verify_and_update, name='useremail_verify'),
    url(r'^cancel/$', settings_views.CancelView.as_view(), name='cancelaccount'),
    url(r'^twofactor/$', settings_views.ManageTwoFactorView.as_view(), name='twofactor'),
    url(r'^twofactor/newkey/$', settings_views.TwoFactorNewKeyView.as_view(), name='newkey'),
    url(r'^twofactor/disable/$', settings_views.DisableTwoFactorView.as_view(), name='twofactor_disable'),
    url(r'^twofactor/forgetdevices/$', settings_views.ForgetTwoFactorDevicesView.as_view(), name='forgetdevices')
)
