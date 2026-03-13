from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import aiofiles
import aioboto3

from backend.config.settings import get_settings


@dataclass(slots=True)
class StoredObject:
    url: str
    storage_path: str
    size: int


class StorageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def save_bytes(self, relative_path: str, content: bytes) -> StoredObject:
        if self.settings.storage_backend == "s3":
            return await self._save_s3(relative_path, content)
        return await self._save_local(relative_path, content)

    async def load_bytes(self, storage_path: str) -> bytes:
        if self.settings.storage_backend == "s3":
            return await self._load_s3(storage_path)
        path = Path(storage_path)
        async with aiofiles.open(path, "rb") as file:
            return await file.read()

    async def delete(self, storage_path: str) -> None:
        if self.settings.storage_backend == "s3":
            await self._delete_s3(storage_path)
            return
        path = Path(storage_path)
        if path.exists():
            path.unlink()

    async def _save_local(self, relative_path: str, content: bytes) -> StoredObject:
        base_dir = Path(self.settings.local_storage_path)
        target = base_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(target, "wb") as file:
            await file.write(content)
        return StoredObject(url=str(target), storage_path=str(target), size=len(content))

    async def _save_s3(self, relative_path: str, content: bytes) -> StoredObject:
        session = aioboto3.Session()
        endpoint_url = self.settings.s3_endpoint_url
        async with session.client(
            "s3",
            region_name=self.settings.s3_region,
            endpoint_url=endpoint_url,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
            use_ssl=self.settings.s3_use_ssl,
        ) as client:
            await client.put_object(Bucket=self.settings.s3_bucket, Key=relative_path, Body=content)
        url = f"{endpoint_url.rstrip('/')}/{self.settings.s3_bucket}/{relative_path}" if endpoint_url else relative_path
        return StoredObject(url=url, storage_path=relative_path, size=len(content))

    async def _load_s3(self, storage_path: str) -> bytes:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            region_name=self.settings.s3_region,
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
            use_ssl=self.settings.s3_use_ssl,
        ) as client:
            result = await client.get_object(Bucket=self.settings.s3_bucket, Key=storage_path)
            async with result["Body"] as body:
                return await body.read()

    async def _delete_s3(self, storage_path: str) -> None:
        session = aioboto3.Session()
        async with session.client(
            "s3",
            region_name=self.settings.s3_region,
            endpoint_url=self.settings.s3_endpoint_url,
            aws_access_key_id=self.settings.s3_access_key_id,
            aws_secret_access_key=self.settings.s3_secret_access_key,
            use_ssl=self.settings.s3_use_ssl,
        ) as client:
            await client.delete_object(Bucket=self.settings.s3_bucket, Key=storage_path)