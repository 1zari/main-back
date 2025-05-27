import os
import uuid

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.http import JsonResponse


def upload_to_ncp_storage(file_obj):
    # 확장자 추출
    ext = os.path.splitext(file_obj.name)[1]  # ".jpg", ".png" 이런거
    # UUID + 확장자 조합
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    # 업로드 경로 (폴더 구분 가능)
    s3_key = f"uploads/{unique_filename}"

    s3 = boto3.client(
        "s3",
        endpoint_url=settings.NCP_S3_ENDPOINT,
        aws_access_key_id=settings.NCP_S3_ACCESS_KEY,
        aws_secret_access_key=settings.NCP_S3_SECRET_KEY,
    )

    bucket_name = settings.NCP_S3_BUCKET_NAME

    try:
        s3.upload_fileobj(
            Fileobj=file_obj,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": file_obj.content_type,
            },
        )
        # 성공하면 파일 URL 리턴
        file_url = f"https://kr.object.ncloudstorage.com/{bucket_name}/{s3_key}"
        return file_url

    except (BotoCoreError, ClientError) as e:
        raise Exception(f"파일 업로드 실패: {e}")


"""
def upload_view(request):  #이미지 업로드 메서드
    if request.method == "POST":
        if 'file' not in request.FILES:
            return JsonResponse({'error': '파일이 없습니다.'}, status=400)

        file_obj = request.FILES['file']

        try:
            file_url = upload_to_ncp_storage(file_obj) # 실제 스토리지에 저장된 파일 url
            
            return JsonResponse({'file_url': file_url})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST 요청만 지원합니다.'}, status=405)

"""
