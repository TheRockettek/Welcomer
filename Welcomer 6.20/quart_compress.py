from gzip import GzipFile
import gzip
from io import BytesIO
import inspect
import hashlib
import mimetypes
import os
import aiofiles
import brotli
import math
import time
import xxhash
import base64

from quart import request, current_app


def encodeid(i):
    return base64.b32encode(
        i.to_bytes(
            (i.bit_length() + 8) // 8,
            'big',
            signed=True)).decode("ascii")


class FolderCompressor:
    def __init__(self):
        self.path = "/home/rock/Welcomer 6.0/cache/"

    async def get(self, key):
        filepath = os.path.join(self.path, key)

        if not os.path.exists(filepath):
            print("[FOLDERCOMPR]", filepath, "does not exist")
            return None

        async with aiofiles.open(filepath, "rb") as f:
            data = await f.read()

        return data

    async def set(self, key, content):
        filepath = os.path.join(self.path, key)

        print("[FOLDERCOMPR] saving data to", filepath)
        async with aiofiles.open(filepath, "wb") as f:
            await f.write(content)

    async def get_key(self, response, encoding):
        # We cache as we will use in set likely
        if inspect.iscoroutinefunction(response.get_data):
            data = await response.get_data()
        else:
            data = response.get_data()

        digest = xxhash.xxh3_64(data, seed=0).hexdigest()
        filename = encoding + "_" + digest + \
            mimetypes.guess_extension(response.mimetype)

        return filename


class Compress:
    def __init__(self, app, USE_FOLDER_STORE):
        print("LOADED COMPRESSOR")
        self.app = app
        self.USE_FOLDER_STORE = USE_FOLDER_STORE
        self.init_app(app)

    def init_app(self, app):
        defaults = [
            (
                "COMPRESS_MIMETYPES",
                [
                    "text/html",
                    "text/css",
                    "text/xml",
                    "application/javascript",
                    "application/octet-stream",
                ],
            ),
            ("COMPRESS_LEVEL_GZIP", 9),
            ("COMPRESS_LEVEL_BROTLI", 11),
            ("COMPRESS_MIN_SIZE", 500),
            ("COMPRESS_CACHE_KEY", None),
            ("COMPRESS_CACHE_BACKEND", None),
            ("COMPRESS_REGISTER", True),
        ]

        for k, v in defaults:
            app.config.setdefault(k, v)

        if self.USE_FOLDER_STORE:
            self.cache = FolderCompressor()
            self.cache_key = self.cache.get_key
        else:
            self.cache = None
            self.cache_key = None

        if app.config["COMPRESS_REGISTER"] and app.config["COMPRESS_MIMETYPES"]:
            app.after_request(self.after_request)

    async def after_request(self, response):
        start = time.time()
        app = self.app or current_app
        accept_encoding = request.headers.get("Accept-Encoding", "").lower()

        if (
            response.mimetype not in app.config["COMPRESS_MIMETYPES"]
            or not 200 <= response.status_code < 300
            or (response.content_length is not None and response.content_length < app.config["COMPRESS_MIN_SIZE"])
            or "Content-Encoding" in response.headers
        ):
            return response

        # encoding = "br"

        if "br" in accept_encoding:
            encoding = "br"
        elif "gzip" in accept_encoding:
            encoding = "gzip"
        else:
            return

        response.direct_passthrough = False

        hit = False
        key = ""

        if self.cache:
            key = await self.cache_key(response, encoding)

            content = await self.cache.get(key)
            if not content:
                content = await self.compress(app, response, encoding)
                await self.cache.set(key, content)
            else:
                hit = True
        else:
            content = await self.compress(app, response, encoding)

        response.set_data(content)

        response.headers["Content-Encoding"] = encoding
        response.headers["Content-Length"] = response.content_length

        vary = response.headers.get("Vary")
        if vary:
            if "accept-encoding" not in vary.lower():
                response.headers["Vary"] = "{}, Accept-Encoding".format(vary)
        else:
            response.headers["Vary"] = "Accept-Encoding"

        response.headers["X-Compression-Duration"] = math.ceil(
            (time.time() - start) * 1000)
        response.headers["X-Compression-Method"] = encoding
        response.headers["X-Compression-Chunk"] = key.split(".")[0]
        response.headers["X-Compression-Hit"] = "hit" if hit else "miss"

        return response

    async def compress(self, app, response, encoding):
        buffer = BytesIO()

        if inspect.iscoroutinefunction(response.get_data):
            data = await response.get_data()
        else:
            data = response.get_data()

        if encoding == "gzip":
            with GzipFile(mode="wb", compresslevel=app.config["COMPRESS_LEVEL_GZIP"], fileobj=buffer) as gzip_file:
                gzip_file.write(data)
        elif encoding == "br":
            buffer.write(brotli.compress(data))

        return buffer.getvalue()
