# Generated manually for LHC Tap System

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taps', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TapSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=64, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('used', 'Utilizado'), ('expired', 'Expirado')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('used_at', models.DateTimeField(blank=True, null=True)),
                ('tap', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='taps.tap')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tap_sessions',
            },
        ),
        migrations.AddIndex(
            model_name='tapsession',
            index=models.Index(fields=['token'], name='tap_sessions_token_idx'),
        ),
        migrations.AddIndex(
            model_name='tapsession',
            index=models.Index(fields=['user', 'tap'], name='tap_sessions_user_tap_idx'),
        ),
        migrations.AddIndex(
            model_name='tapsession',
            index=models.Index(fields=['expires_at'], name='tap_sessions_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='tapsession',
            index=models.Index(fields=['status'], condition=models.Q(('status', 'pending')), name='pending_sessions_idx'),
        ),
        migrations.AddConstraint(
            model_name='tapsession',
            constraint=models.CheckConstraint(check=models.Q(('expires_at__gt', models.F('created_at'))), name='valid_expiration'),
        ),
    ]
