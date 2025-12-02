# Generated migration
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Violation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.CharField(max_length=20, verbose_name='Время нарушения')),
                ('type', models.CharField(max_length=255, verbose_name='Тип нарушения')),
                ('description', models.TextField(verbose_name='Описание')),
                ('source', models.CharField(max_length=255, verbose_name='Источник')),
                ('date', models.DateField(verbose_name='Дата нарушения')),
                ('video_id', models.CharField(blank=True, max_length=255, null=True, verbose_name='ID видео')),
                ('video_url', models.URLField(blank=True, null=True, verbose_name='URL видео')),
                ('breed', models.CharField(blank=True, max_length=255, null=True, verbose_name='Порода')),
                ('muzzle', models.BooleanField(blank=True, null=True, verbose_name='Намордник')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'violations',
                'ordering': ['date', 'time'],
            },
        ),
        migrations.AddIndex(
            model_name='violation',
            index=models.Index(fields=['date', 'time'], name='violations_date_ti_idx'),
        ),
        migrations.AddIndex(
            model_name='violation',
            index=models.Index(fields=['video_id'], name='violations_video_i_idx'),
        ),
    ]

