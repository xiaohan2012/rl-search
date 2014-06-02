from time import time
from scrapy.http import Response


class DownloadTimer(object):
    def process_request(self, request, spider):
        request.meta['__start_time'] = time()
        # this not block middlewares which are has greater number then this
        return None

    def process_response(self, request, response, spider):
        request.meta['__end_time'] = time()
        return response  # return response coz we should

    def process_exception(self, request, exception, spider):
        request.meta['__end_time'] = time()
        return Response(
            url=request.url,
            status=110,
            request=request)
