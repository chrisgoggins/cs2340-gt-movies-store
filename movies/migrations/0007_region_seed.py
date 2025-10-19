from django.db import migrations


def create_regions(apps, schema_editor):
    Region = apps.get_model('movies', 'Region')
    default_regions = [
        {
            'name': 'Southeast US',
            'code': 'southeast-us',
            'center_lat': 33.7490,
            'center_lng': -84.3880,
        },
        {
            'name': 'Northeast US',
            'code': 'northeast-us',
            'center_lat': 40.7128,
            'center_lng': -74.0060,
        },
        {
            'name': 'Midwest US',
            'code': 'midwest-us',
            'center_lat': 41.8781,
            'center_lng': -87.6298,
        },
        {
            'name': 'Southwest US',
            'code': 'southwest-us',
            'center_lat': 32.7157,
            'center_lng': -117.1611,
        },
        {
            'name': 'West Coast US',
            'code': 'west-coast-us',
            'center_lat': 34.0522,
            'center_lng': -118.2437,
        },
    ]

    for region in default_regions:
        Region.objects.get_or_create(code=region['code'], defaults=region)


def remove_regions(apps, schema_editor):
    Region = apps.get_model('movies', 'Region')
    codes = [
        'southeast-us',
        'northeast-us',
        'midwest-us',
        'southwest-us',
        'west-coast-us',
    ]
    Region.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0006_region'),
    ]

    operations = [
        migrations.RunPython(create_regions, remove_regions),
    ]
