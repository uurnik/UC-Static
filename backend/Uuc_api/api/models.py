from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
import json
import ast


class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        if not email:
            raise ValueError("Users must have an email address")
        if not username:
            raise ValueError("Users must have a username")

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser):
    email = models.EmailField(verbose_name="email", max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    date_joined = models.DateTimeField(verbose_name="date joined", auto_now_add=True)
    last_login = models.DateTimeField(verbose_name="last login", auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = AccountManager()

    def __str__(self):
        return self.email

    # For checking permissions
    def has_perm(self, perm, obj=None):
        return self.is_admin

    # Does this user have permission to view this app?
    def has_module_perms(self, app_label):
        return True


class Hosts(models.Model):
    ip = models.CharField(max_length=15, blank=False)
    name = models.CharField(max_length=30, blank=False, primary_key=True)
    username = models.CharField(max_length=30)
    password = models.CharField(default=False, max_length=30)
    platform = models.CharField(default="ios", max_length=20)
    group = models.CharField(max_length=6, default=False)
    is_configured = models.BooleanField(default=False)
    wan_int = models.CharField(max_length=30, blank=True)
    wan_subnet = models.CharField(max_length=15, blank=True)
    next_hop = models.CharField(max_length=15, blank=True)
    tunnel_ip = models.CharField(max_length=30, blank=True)
    loop_back = models.CharField(max_length=35, blank=True)
    vendor = models.CharField(max_length=40, blank=True)
    model = models.CharField(max_length=30, blank=True)
    os_version = models.TextField(max_length=100, blank=True)
    serial_no = models.CharField(max_length=50, blank=True)
    dev_name = models.TextField(max_length=30, blank=True)
    interfaces = models.TextField(max_length=200, blank=True)
    fqdn = models.TextField(max_length=100, blank=True)
    ram_size = models.CharField(max_length=20, blank=True)
    copp_bw = models.IntegerField(null=True)
    #

    fhrp = models.BooleanField(default=False)
    fhrp_interface = models.CharField(max_length=30, blank=True)
    primary_router = models.BooleanField(default=False)
    virtual_ip = models.GenericIPAddressField(null=True)

    advertised_interfaces = models.CharField(max_length=400, blank=True)
    advertised_static_routes = models.CharField(max_length=800, blank=True)

    crypto = models.IntegerField(null=True)
    tunnel_int = models.IntegerField(null=True)
    routing = models.IntegerField(null=True)
    vrfs = models.IntegerField(null=True)
    tcl_scp = models.IntegerField(null=True)
    acl = models.IntegerField(null=True)
    nat = models.IntegerField(null=True)
    route_map_prefix_list = models.IntegerField(null=True)

    snmp_int_index = models.IntegerField(null=True)

    logging_host = models.GenericIPAddressField(null=True)
    logging_level = models.TextField(max_length=15, null=True)
    logging_facility = models.TextField(max_length=15, null=True)
    logging_configured = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Routes(models.Model):
    route = models.ForeignKey(Hosts, related_name="routes", on_delete=models.CASCADE)
    lan_routes = models.CharField(max_length=20, blank=True)
    custom_route = models.CharField(max_length=60, blank=True)
    protocol = models.TextField(max_length=15, null=True)
    advertised = models.BooleanField(default=False)
    protocol = models.TextField(null=True, max_length=10)


class Defaults(models.Model):
    tunnel_int = models.CharField(max_length=5, default="414")
    asn = models.CharField(max_length=5, default="65414")
    policy_num = models.CharField(max_length=5, default="22")
    ipsec_key = models.CharField(max_length=16, default="uurnik123")
    trans_name = models.CharField(max_length=15, default="UURNIK")
    profile_name = models.CharField(max_length=15, default="UURNIK_CONNECT")
    nhs_server = models.CharField(max_length=200, default="none")
    nhs_nbma = models.CharField(max_length=200, default="none")
    access_type = models.IntegerField(blank=True, null=True)
    ip_sla_process = models.CharField(max_length=3, blank=False, default="214")
    track_ip = models.GenericIPAddressField(null=True)
    is_sla_configured = models.BooleanField(default=False)
    is_device_hardening_configured = models.BooleanField(default=False)
    is_copp_configured = models.BooleanField(default=False)
    hubs_fqds = models.TextField(max_length=300, blank=True)
    dns = models.GenericIPAddressField(null=True)


class TunnelPool(models.Model):
    ip = models.CharField(max_length=15, primary_key=True)
    is_used = models.BooleanField(default=False)


class CacheTable(models.Model):
    ip = models.CharField(max_length=15, primary_key=True)
    in_use = models.BooleanField(default=False)
    device_ip = models.CharField(max_length=15)
