from django.contrib.gis.db import models
from django.db.models.manager import Manager


class District(models.Model):
    city_no = models.CharField(verbose_name="시 고유번호", max_length=20, db_index=True)
    city_name = models.CharField(verbose_name="시 이름", max_length=40, db_index=True)
    district_no = models.CharField(verbose_name="구 고유번호", max_length=20, db_index=True)
    district_name = models.CharField(verbose_name="구 이름", max_length=40, db_index=True)
    emd_no = models.CharField(
        verbose_name="읍면동 고유번호",
        max_length=20,
        unique=True,
        db_index=True,
    )
    emd_name = models.CharField(verbose_name="읍면동 이름", max_length=40, db_index=True)

    geometry = models.MultiPolygonField(verbose_name="읍면동 경계", srid=5179, spatial_index=True)

    objects = Manager()

    def __str__(self):
        return f"{self.city_name} {self.district_name} {self.emd_name}"
