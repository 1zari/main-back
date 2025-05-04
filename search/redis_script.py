import json
from typing import cast

import psycopg2
import redis

from config import settings
from config.settings.base import DATABASES, REDIS_HOST, REDIS_PORT
from search.job_tree import JOB_CATEGORIES

db_settings = settings.base.DATABASES["default"]
PG_CONFIG = {
    "database": db_settings["NAME"],
    "user": db_settings["USER"],
    "password": db_settings["PASSWORD"],
    "host": db_settings["HOST"],
    "port": db_settings["PORT"],
}


# 2. PostgreSQL 연결 및 데이터 가져오기
def fetch_regions():
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT city_no, city_name, district_no, district_name, emd_no, emd_name
        FROM search_district;
    """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


r = redis.Redis(
    host=cast(str, REDIS_HOST),
    port=cast(int, REDIS_PORT),
    decode_responses=True,
)


# Redis에 저장 (key: region:시:군구:읍면동, value: polygon WKT)
def save_regions_to_redis(regions):
    try:
        region_tree = []
        city_map = {}  # city_no -> city 객체

        for (
            city_no,
            city_name,
            district_no,
            district_name,
            emd_no,
            emd_name,
        ) in regions:
            # 시/도 객체 생성 또는 조회
            if city_no not in city_map:
                city_obj = {"id": city_no, "name": city_name, "districts": []}
                city_map[city_no] = city_obj
                region_tree.append(city_obj)
            else:
                city_obj = city_map[city_no]

            # 시군구 객체 생성 또는 조회
            district_map = city_obj.setdefault("_district_map", {})
            if district_no not in district_map:
                district_obj = {
                    "id": district_no,
                    "name": district_name,
                    "towns": [],
                }
                district_map[district_no] = district_obj
                city_obj["districts"].append(district_obj)
            else:
                district_obj = district_map[district_no]

            # 읍면동 추가 (중복 방지)
            town_entry = {"id": emd_no, "name": emd_name}
            if town_entry not in district_obj["towns"]:
                district_obj["towns"].append(town_entry)

        # 임시 _district_map 제거
        for city_obj in region_tree:
            if "_district_map" in city_obj:
                del city_obj["_district_map"]

        r.set("region_tree", json.dumps(region_tree, ensure_ascii=False))
        print("지역 계층 구조 저장 완료!")
    except Exception as e:
        print(f"에러 발생: {str(e)}")
        raise


def save_job_to_redis(job):
    try:
        r.set("job_categories", json.dumps(job, ensure_ascii=False))

    except Exception as e:
        return print(f"error: {str(e)}")
    print("직업 카테고리 저장 완료!")


if __name__ == "__main__":
    try:
        regions = fetch_regions()
        save_regions_to_redis(regions)
        job = JOB_CATEGORIES
        save_job_to_redis(job)

        print("All data uploaded to Redis.")
    except Exception as e:
        raise e
