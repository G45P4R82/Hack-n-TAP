# Generated manually for LHC Tap System

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('type', models.CharField(choices=[('beer', 'Chope'), ('mate', 'Mate')], max_length=10)),
                ('location', models.CharField(blank=True, max_length=120, null=True)),
                ('dose_ml', models.PositiveIntegerField(default=300)),
                ('price_cents', models.PositiveIntegerField(default=1000)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'taps',
            },
        ),
        migrations.AddIndex(
            model_name='tap',
            index=models.Index(fields=['type', 'is_active'], name='taps_type_active_idx'),
        ),
        migrations.AddIndex(
            model_name='tap',
            index=models.Index(fields=['location'], name='taps_location_idx'),
        ),
        migrations.AddConstraint(
            model_name='tap',
            constraint=models.CheckConstraint(check=models.Q(('dose_ml__gt', 0)), name='positive_dose'),
        ),
        migrations.AddConstraint(
            model_name='tap',
            constraint=models.CheckConstraint(check=models.Q(('price_cents__gt', 0)), name='positive_price'),
        ),
    ]
