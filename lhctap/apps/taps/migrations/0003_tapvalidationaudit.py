# Generated manually for LHC Tap System

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('taps', '0002_tapsession'),
    ]

    operations = [
        migrations.CreateModel(
            name='TapValidationAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(max_length=64)),
                ('token', models.CharField(max_length=64)),
                ('result', models.CharField(choices=[('ok', 'Sucesso'), ('expired', 'Token Expirado'), ('used', 'Token Já Utilizado'), ('insufficient', 'Saldo Insuficiente'), ('not_found', 'Token Não Encontrado'), ('rate_limited', 'Rate Limit Excedido'), ('tap_inactive', 'Tap Inativo')], max_length=16)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('tap', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='taps.tap')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'tap_validations_audit',
            },
        ),
        migrations.AddIndex(
            model_name='tapvalidationaudit',
            index=models.Index(fields=['device_id', '-created_at'], name='audit_device_created_idx'),
        ),
        migrations.AddIndex(
            model_name='tapvalidationaudit',
            index=models.Index(fields=['token'], name='audit_token_idx'),
        ),
        migrations.AddIndex(
            model_name='tapvalidationaudit',
            index=models.Index(fields=['result', '-created_at'], name='audit_result_created_idx'),
        ),
        migrations.AddIndex(
            model_name='tapvalidationaudit',
            index=models.Index(fields=['-created_at'], name='audit_created_idx'),
        ),
    ]
