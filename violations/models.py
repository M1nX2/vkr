from django.db import models


class Violation(models.Model):
    time = models.CharField(max_length=20, verbose_name='Время нарушения')
    type = models.CharField(max_length=255, verbose_name='Тип нарушения')
    description = models.TextField(verbose_name='Описание')
    source = models.CharField(max_length=255, verbose_name='Источник')
    date = models.DateField(verbose_name='Дата нарушения')
    video_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='ID видео')
    video_url = models.URLField(null=True, blank=True, verbose_name='URL видео')
    breed = models.CharField(max_length=255, null=True, blank=True, verbose_name='Порода')
    muzzle = models.BooleanField(null=True, blank=True, verbose_name='Намордник')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'violations'
        ordering = ['date', 'time']
        indexes = [
            models.Index(fields=['date', 'time']),
            models.Index(fields=['video_id']),
        ]

    def __str__(self):
        return f"{self.date} {self.time} - {self.type}"

