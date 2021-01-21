# Generated by Django 2.2.4 on 2021-01-20 17:10

from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_countries.fields
import jasmin_notifications.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Institution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('country', django_countries.fields.CountryField(max_length=2)),
                ('institution_type', models.CharField(choices=[('NERC', 'NERC'), ('University', 'University'), ('School', 'School'), ('Government', 'Government'), ('Commercial', 'Commercial'), ('Other', 'Other')], max_length=20)),
            ],
            options={
                'ordering': ('name', 'country'),
            },
        ),
        migrations.CreateModel(
            name='CEDAUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('discipline', models.CharField(choices=[('Atmospheric Physics', 'Atmospheric Physics'), ('Atmospheric Chemistry', 'Atmospheric Chemistry'), ('Climate Change', 'Climate Change'), ('Earth System Science', 'Earth System Science'), ('Marine Science', 'Marine Science'), ('Terrestrial and Fresh Water', 'Terrestrial and Fresh Water'), ('Earth Observation', 'Earth Observation'), ('Polar Science', 'Polar Science'), ('Geography', 'Geography'), ('Engineering', 'Engineering'), ('Medical/Biological Sciences', 'Medical/Biological Sciences'), ('Mathematics/Computer Science', 'Mathematics/Computer Science'), ('Economics', 'Economics'), ('Personal use', 'Personal use'), ('Other', 'Other')], help_text='Please select the closest match to the discipline that you work in', max_length=30)),
                ('degree', models.CharField(blank=True, choices=[('', 'Not studying for a degree'), ('First degree', "First Degree (Bachelor's / Undergraduate Master's)"), ("Postgraduate Master's", "Postgraduate Master's"), ('Doctorate', 'Doctorate'), ('Other', 'Other')], help_text='The type of degree you are studying for, if applicable', max_length=30)),
                ('service_user', models.BooleanField(default=False, help_text='Indicates if this user is a service user, i.e. a user that exists to run a service rather than a regular user account.')),
                ('email_confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('conditions_accepted_at', models.DateTimeField(blank=True, null=True)),
                ('approved_for_root_by', models.CharField(blank=True, max_length=200, null=True)),
                ('approved_for_root_at', models.DateTimeField(blank=True, null=True)),
                ('user_reason', models.TextField(blank=True, help_text='Indicate why the user has been suspended', verbose_name='Reason for suspension (user)')),
                ('internal_reason', models.TextField(blank=True, help_text="Any internal details about the user's suspension that should not be displayed to the user", verbose_name='Reason for suspension (internal)')),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('institution', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='account.Institution')),
                ('responsible_users', models.ManyToManyField(blank=True, help_text='For service users, these are the users responsible for the administration of the service user.', limit_choices_to={'service_user': False}, to=settings.AUTH_USER_MODEL)),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'CEDA User',
                'verbose_name_plural': 'CEDA Users',
                'ordering': ('username',),
            },
            bases=(models.Model, jasmin_notifications.models.NotifiableUserMixin),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]