from django.contrib.gis.utils import LayerMapping

from config.settings.base import BASE_DIR
from search.models import District

district_mapping = {
    "district_no": "DIST_NO",
    "district_name": "DIST_NAME",
    "city_no": "CITY_NO",
    "city_name": "CITY_NAME",
    "emd_no": "EMD_NO",
    "emd_name": "EMD_NAME",
    "geometry": "POLYGON",
}

shp_file = str(BASE_DIR / "search/logical_data/new_logical_data.shp")


def run(verbose=True):
    try:
        District.objects.all().delete()
        lm = LayerMapping(
            District,
            shp_file,
            district_mapping,
            transform=True,
            source_srs="ESRI:102080",
            encoding="utf-8",
        )
        lm.save(strict=True, verbose=verbose)
    except Exception as e:
        print(str(e))
