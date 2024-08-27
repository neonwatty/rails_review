from s3 import s3_client
from s3 import bucket_name as bucket_name_main


def add(
    user_id: str,
    file_id: str,
    filename: str,
    bucket_name: str | None = bucket_name_main,
    stage: str = "dev",
    conditions: list | None = None,  # [["content-length-range", 0, 5 * 1024 * 1024]],
    expiration: int = 120,
) -> dict:
    try:
        # add custom path
        object_name = f"{stage}/{user_id}/{file_id}/{filename}"

        # get presigned url
        response = s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=None,
            Conditions=conditions,
            ExpiresIn=expiration,
        )
        return response
    except Exception as e:
        raise e
