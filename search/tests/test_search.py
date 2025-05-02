import json

import pytest
from django.contrib.gis.geos.collections import MultiPolygon
from django.contrib.gis.geos.point import Point
from django.contrib.gis.geos.polygon import Polygon
from django.test.client import Client

from search.models import District
from utils.mock_test_data import (
    mock_common_company_user,
    mock_company_user,
    mock_job_posting,
)


@pytest.mark.django_db
def test_get_search_success(
    mock_job_posting, mock_company_user, mock_common_company_user
):
    center_lon, center_lat = 127.0473, 37.5172
    delta = 0.03  # 약 3km (위도 0.01도 ≈ 1.11km)
    polygon = Polygon(
        [
            (center_lon - delta, center_lat - delta),
            (center_lon - delta, center_lat + delta),
            (center_lon + delta, center_lat + delta),
            (center_lon + delta, center_lat - delta),
            (center_lon - delta, center_lat - delta),
        ]
    )
    district = District.objects.create(
        city_name="서울특별시",
        district_name="강남구",
        emd_name="역삼동",
        geometry=MultiPolygon([polygon]),
    )
    district.geometry.srid = 5179
    district.save()

    # 2. District의 중심점에서 2km 떨어진 지점에 채용공고 생성
    # 위도 0.018도 ≈ 2km (1.11km * 0.018 ≈ 1998m)
    job_location = Point(center_lon, center_lat + 0.018)
    job_location.srid = 5179

    mock_job_posting.city = "서울특별시"
    mock_job_posting.district = "강남구"
    mock_job_posting.town = "역삼동"
    mock_job_posting.location = job_location
    mock_job_posting.save()
    calculated_distance = district.geometry.centroid.distance(
        mock_job_posting.location) * 111000  # Approximate conversion degrees to meters
    print(
        f"Distance between District centroid and Job Posting location (meters): {calculated_distance}")
    assert calculated_distance <= 3000

    client = Client()
    response = client.get("/api/search/?town=역삼동")

    print(json.loads(response.content))
    assert response.status_code == 200
    response_data = json.loads(response.content)

    assert "results" in response_data
    assert isinstance(response_data["results"], list)

    assert len(response_data["results"]) == 1

    result_job_posting = response_data["results"][0]
    assert result_job_posting["job_posting_id"] == str(
        mock_job_posting.job_posting_id)  # UUID는 보통 문자열로 직렬화됨
    assert result_job_posting[
               "job_posting_title"] == mock_job_posting.job_posting_title