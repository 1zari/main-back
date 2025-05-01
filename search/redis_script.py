import json

import psycopg2
import redis

from config import settings
from config.settings.base import DATABASES, REDIS_HOST, REDIS_PORT

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
        SELECT city_name, district_name, emd_name
        FROM search_district;
    """
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


REDIS_CONFIG = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "decode_responses": True,
}


# Redis에 저장 (key: region:시:군구:읍면동, value: polygon WKT)
def save_regions_to_redis(regions):
    r = redis.Redis(**REDIS_CONFIG)
    region_tree = {}
    for city, district, town in regions:
        # 시/도 추가
        if city not in region_tree:
            region_tree[city] = {}
        # 시군구 추가
        if district not in region_tree[city]:
            region_tree[city][district] = []
        # 읍면동 추가 (중복 방지)
        if town not in region_tree[city][district]:
            region_tree[city][district].append(town)

    # JSON으로 직렬화 후 Redis 저장
    r.set("region_tree", json.dumps(region_tree, ensure_ascii=False))
    print("지역 계층 구조 저장 완료!")


if __name__ == "__main__":
    regions = fetch_regions()
    save_regions_to_redis(regions)
    print("All regions uploaded to Redis.")
