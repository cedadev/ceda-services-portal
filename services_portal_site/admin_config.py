import django.contrib.admin.apps


class CEDAAdminConfig(django.contrib.admin.apps.AdminConfig):
    default_site = "services_portal_site.admin_site.AdminSite"
