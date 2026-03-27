from django.db import migrations


def seed_datasets(apps, schema_editor):
    Dataset = apps.get_model("playground", "Dataset")

    rows = [
        ("iris", "Classic Iris flower classification dataset.", 150, 4),
        ("breast_cancer", "Breast cancer classification dataset.", 569, 30),
        ("wine", "Wine cultivar classification dataset.", 178, 13),
        ("digits", "Handwritten digits classification dataset.", 1797, 64),
    ]

    for name, description, n_samples, n_features in rows:
        Dataset.objects.update_or_create(
            name=name,
            defaults={
                "task_type": "classification",
                "description": description,
                "n_samples": int(n_samples),
                "n_features": int(n_features),
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("playground", "0002_alter_dataset_options_remove_dataset_columns_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_datasets, migrations.RunPython.noop),
    ]

