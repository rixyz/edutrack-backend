# Generated by Django 5.1.3 on 2024-12-25 13:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academics', '0002_initial'),
        ('evaluations', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentperformancemetrics',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.student'),
        ),
        migrations.AddField(
            model_name='studentperformancemetrics',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academics.subject'),
        ),
        migrations.AddField(
            model_name='studentresult',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.student'),
        ),
        migrations.AddField(
            model_name='studentresult',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academics.subject'),
        ),
        migrations.AlterUniqueTogether(
            name='studentperformancemetrics',
            unique_together={('student', 'subject')},
        ),
        migrations.AlterUniqueTogether(
            name='studentresult',
            unique_together={('student', 'subject', 'semester')},
        ),
    ]