import boto3
from pathlib import Path
from typing import Optional, List, Dict
from botocore.config import Config
from core.config import (
    CF_ACCOUNT_ID,
    CF_R2_ACCESS_KEY,
    CF_R2_SECRET_KEY,
    CF_R2_BUCKET,
    CF_R2_PUBLIC_URL
)

def _get_s3_client():
    """Initializes and returns boto3 S3 client configured for Cloudflare R2."""
    if not (CF_ACCOUNT_ID and CF_R2_ACCESS_KEY and CF_R2_SECRET_KEY):
        return None
    endpoint_url = f"https://{CF_ACCOUNT_ID}.r2.cloudflarestorage.com"
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=CF_R2_ACCESS_KEY,
        aws_secret_access_key=CF_R2_SECRET_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4")
    )

def upload_to_r2(file_path: Path, remote_filename: Optional[str] = None) -> Optional[str]:
    """
    Uploads a generated reel MP4 to Cloudflare R2 object storage (Zero Egress fees)
    and returns a public or presigned streaming URL.
    """
    s3 = _get_s3_client()
    if not s3:
        print("[Uploader] Cloudflare R2 credentials not set. Keeping local file.")
        return None

    if not remote_filename:
        remote_filename = file_path.name

    try:
        # Upload file with explicit video/mp4 ContentType
        s3.upload_file(
            Filename=str(file_path.resolve()),
            Bucket=CF_R2_BUCKET,
            Key=remote_filename,
            ExtraArgs={"ContentType": "video/mp4"}
        )

        # Use clean permanent universal public URL if configured
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

def list_r2_videos() -> List[Dict]:
    """
    Retrieves list of all videos stored in the Cloudflare R2 bucket.
    Returns list of dicts with name, size_mb, last_modified, and public url.
    """
    s3 = _get_s3_client()
    if not s3:
        return []

    try:
        response = s3.list_objects_v2(Bucket=CF_R2_BUCKET)
        contents = response.get("Contents", [])
        
        # Sort by latest first
        contents.sort(key=lambda x: x["LastModified"], reverse=True)

        videos = []
        for item in contents:
            key = item["Key"]
            size_mb = round(item["Size"] / (1024 * 1024), 2)
            url = f"{CF_R2_PUBLIC_URL.rstrip('/')}/{key}" if CF_R2_PUBLIC_URL else None
            videos.append({
                "name": key,
                "size_mb": size_mb,
                "size_bytes": item["Size"],
                "last_modified": item["LastModified"].strftime("%Y-%m-%d %H:%M:%S UTC"),
                "url": url
            })
        return videos
    except Exception as e:
        print(f"[Uploader] Error listing R2 objects: {e}")
        return []

def delete_from_r2(remote_filename: str) -> bool:
    """
    Permanently deletes a video object from the Cloudflare R2 bucket to free up space.
    """
    s3 = _get_s3_client()
    if not s3:
        return False

    try:
        s3.delete_object(Bucket=CF_R2_BUCKET, Key=remote_filename)
        print(f"[Uploader] Successfully deleted {remote_filename} from Cloudflare R2")
        return True
    except Exception as e:
        print(f"[Uploader] Error deleting {remote_filename} from R2: {e}")
        return False

def get_r2_storage_stats() -> Dict:
    """
    Calculates total used space in R2 and returns summary metrics against 10GB free limit.
    """
    videos = list_r2_videos()
    total_bytes = sum(v["size_bytes"] for v in videos)
    total_mb = round(total_bytes / (1024 * 1024), 2)
    free_gb_limit = 10.0
    used_gb = total_bytes / (1024 ** 3)
    free_gb_remaining = max(0.0, free_gb_limit - used_gb)

    return {
        "total_files": len(videos),
        "total_mb": total_mb,
        "used_gb": round(used_gb, 3),
        "free_gb_remaining": round(free_gb_remaining, 3),
        "percent_used": round((used_gb / free_gb_limit) * 100, 2)
    }
