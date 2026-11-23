import boto3
from pathlib import Path
from typing import Optional
from botocore.config import Config
from core.config import (
    CF_ACCOUNT_ID,
    CF_R2_ACCESS_KEY,
    CF_R2_SECRET_KEY,
    CF_R2_BUCKET,
    CF_R2_PUBLIC_URL
)

def upload_to_r2(file_path: Path, remote_filename: Optional[str] = None) -> Optional[str]:
    """
    Uploads a generated reel MP4 to Cloudflare R2 object storage (Zero Egress fees)
    and returns a public or presigned streaming URL.
    """
    if not (CF_ACCOUNT_ID and CF_R2_ACCESS_KEY and CF_R2_SECRET_KEY):
        print("[Uploader] Cloudflare R2 credentials not set. Keeping local file.")
        return None

    if not remote_filename:
        remote_filename = file_path.name

    endpoint_url = f"https://{CF_ACCOUNT_ID}.r2.cloudflarestorage.com"
    
    try:
        s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=CF_R2_ACCESS_KEY,
            aws_secret_access_key=CF_R2_SECRET_KEY,
            region_name="auto",
            config=Config(signature_version="s3v4")
        )

        # Upload file
        s3.upload_file(
            Filename=str(file_path.resolve()),
            Bucket=CF_R2_BUCKET,
            Key=remote_filename,
            ExtraArgs={"ContentType": "video/mp4"}
        )

        # Use clean permanent universal public URL if configured, otherwise fallback to presigned URL
        if CF_R2_PUBLIC_URL:
            url = f"{CF_R2_PUBLIC_URL.rstrip('/')}/{remote_filename}"
        else:
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": CF_R2_BUCKET, "Key": remote_filename},
                ExpiresIn=604800 # 7 days
            )
        print(f"[Uploader] Successfully uploaded to Cloudflare R2: {remote_filename}")
        print(f"[Uploader] Permanent Public URL: {url}")
        return url
    except Exception as e:
        print(f"[Uploader] Cloudflare R2 upload warning: {e}")
        return None
