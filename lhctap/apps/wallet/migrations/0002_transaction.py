# Generated manually for LHC Tap System

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wallet', '0001_initial'),
        ('taps', '0002_tapsession'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount_cents', models.IntegerField()),
                ('category', models.CharField(choices=[('beer', 'Chope'), ('mate', 'Mate'), ('topup', 'Recarga')], max_length=10)),
                ('volume_ml', models.PositiveIntegerField(default=0)),
                ('description', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('ref_session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='taps.tapsession')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'transactions',
            },
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['user', '-created_at'], name='transactions_user_created_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['category', '-created_at'], name='transactions_category_created_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['-created_at'], name='transactions_created_idx'),
        ),
        migrations.AddConstraint(
            model_name='transaction',
            constraint=models.CheckConstraint(
                check=models.Q(
                    models.Q(('category__in', ['beer', 'mate']), ('amount_cents__lt', 0), ('volume_ml__gt', 0)),
                    models.Q(('category', 'topup'), ('amount_cents__gt', 0), ('volume_ml', 0)),
                    _connector='OR'
                ),
                name='valid_transaction_type'
            ),
        ),
    ]
