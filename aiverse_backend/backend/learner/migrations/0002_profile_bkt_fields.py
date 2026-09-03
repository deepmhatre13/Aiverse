from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learner', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='conceptmastery',
            name='bkt_trace',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='learnerprofile',
            name='learner_ability',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='learnerprofile',
            name='streak_days',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='learnerprofile',
            name='learning_velocity',
            field=models.FloatField(default=0.0),
        ),
    ]
