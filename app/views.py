'''
Basic views
'''
import json

from user.utils import auth_permission_required
from .settings import LOGS_FILE_DIR
from .utils import catch_exception, gen_response, parse_args


@catch_exception('POST')
@auth_permission_required()
def get_logs(request):
    ''' api/logs POST
    para: offset(int) = 0, size(int) = 20
    return: data(str), code =
        200: success
    '''
    offset, size = parse_args(request.body, 'offset', 'size', offset=0, size=20)
    data = []
    with open(LOGS_FILE_DIR, 'r', encoding='utf8') as logs_file:
        logs = logs_file.readlines()[::-1]
        data = logs[offset: (offset + size)]
    data = [json.loads(line[:-1]) for line in data]
    return gen_response(code=200, data=data)
