# Generated by Django 3.1.5 on 2021-08-04 06:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('email', models.EmailField(max_length=60, unique=True, verbose_name='email')),
                ('username', models.CharField(max_length=30, unique=True)),
                ('date_joined', models.DateTimeField(auto_now_add=True, verbose_name='date joined')),
                ('last_login', models.DateTimeField(auto_now=True, verbose_name='last login')),
                ('is_admin', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CacheTable',
            fields=[
                ('ip', models.CharField(max_length=15, primary_key=True, serialize=False)),
                ('in_use', models.BooleanField(default=False)),
                ('device_ip', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='Defaults',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tunnel_int', models.CharField(default='414', max_length=5)),
                ('asn', models.CharField(default='65414', max_length=5)),
                ('policy_num', models.CharField(default='22', max_length=5)),
                ('ipsec_key', models.CharField(default='uurnik123', max_length=16)),
                ('trans_name', models.CharField(default='UURNIK', max_length=15)),
                ('profile_name', models.CharField(default='UURNIK_CONNECT', max_length=15)),
                ('nhs_server', models.CharField(default='none', max_length=200)),
                ('nhs_nbma', models.CharField(default='none', max_length=200)),
                ('access_type', models.IntegerField(blank=True, null=True)),
                ('ip_sla_process', models.CharField(default='214', max_length=3)),
                ('track_ip', models.GenericIPAddressField(null=True)),
                ('is_sla_configured', models.BooleanField(default=False)),
                ('is_device_hardening_configured', models.BooleanField(default=False)),
                ('is_copp_configured', models.BooleanField(default=False)),
                ('hubs_fqds', models.TextField(blank=True, max_length=300)),
                ('dns', models.GenericIPAddressField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Hosts',
            fields=[
                ('ip', models.CharField(max_length=15)),
                ('name', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=30)),
                ('password', models.CharField(default=False, max_length=30)),
                ('platform', models.CharField(default='ios', max_length=20)),
                ('group', models.CharField(default=False, max_length=6)),
                ('is_configured', models.BooleanField(default=False)),
                ('wan_int', models.CharField(blank=True, max_length=30)),
                ('wan_subnet', models.CharField(blank=True, max_length=15)),
                ('next_hop', models.CharField(blank=True, max_length=15)),
                ('tunnel_ip', models.CharField(blank=True, max_length=30)),
                ('loop_back', models.CharField(blank=True, max_length=35)),
                ('vendor', models.CharField(blank=True, max_length=40)),
                ('model', models.CharField(blank=True, max_length=30)),
                ('os_version', models.TextField(blank=True, max_length=100)),
                ('serial_no', models.CharField(blank=True, max_length=50)),
                ('dev_name', models.TextField(blank=True, max_length=30)),
                ('interfaces', models.TextField(blank=True, max_length=200)),
                ('fqdn', models.TextField(blank=True, max_length=100)),
                ('ram_size', models.CharField(blank=True, max_length=20)),
                ('copp_bw', models.IntegerField(null=True)),
                ('static_tunnel_network', models.GenericIPAddressField(null=True, protocol='ipv4')),
                ('fhrp', models.BooleanField(default=False)),
                ('fhrp_interface', models.CharField(blank=True, max_length=30)),
                ('primary_router', models.BooleanField(default=False)),
                ('virtual_ip', models.GenericIPAddressField(null=True)),
                ('advertised_interfaces', models.CharField(blank=True, max_length=400)),
                ('advertised_static_routes', models.CharField(blank=True, max_length=800)),
                ('crypto', models.IntegerField(null=True)),
                ('tunnel_int', models.IntegerField(null=True)),
                ('routing', models.IntegerField(null=True)),
                ('vrfs', models.IntegerField(null=True)),
                ('tcl_scp', models.IntegerField(null=True)),
                ('acl', models.IntegerField(null=True)),
                ('nat', models.IntegerField(null=True)),
                ('route_map_prefix_list', models.IntegerField(null=True)),
                ('snmp_int_index', models.IntegerField(null=True)),
                ('logging_host', models.GenericIPAddressField(null=True)),
                ('logging_level', models.TextField(max_length=15, null=True)),
                ('logging_facility', models.TextField(max_length=15, null=True)),
                ('logging_configured', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='StaticTunnelNet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parentnetwork', models.GenericIPAddressField(protocol='ipv4')),
                ('network', models.GenericIPAddressField(protocol='ipv4')),
                ('used', models.BooleanField(default=False)),
                ('vendor', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='TunnelPool',
            fields=[
                ('ip', models.CharField(max_length=15, primary_key=True, serialize=False)),
                ('is_used', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Routes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lan_routes', models.CharField(blank=True, max_length=20)),
                ('custom_route', models.CharField(blank=True, max_length=60)),
                ('advertised', models.BooleanField(default=False)),
                ('protocol', models.TextField(max_length=10, null=True)),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routes', to='api.hosts')),
            ],
        ),
    ]
