import os

from django.http import HttpResponse, FileResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from backend.models import Attachment
from tickets.settings import MEDIA_ROOT


@api_view(['GET'])
def get_attachment(request, attachment):

    if not Attachment.objects.filter(id=attachment).exists():
        return Response(status=status.HTTP_404_NOT_FOUND)

    cur_attachment = Attachment.objects.get(id=attachment)

    if not cur_attachment.file:
        return Response(status=status.HTTP_404_NOT_FOUND)

    file_location = MEDIA_ROOT + '/' + cur_attachment.file.name

    # try:
    with open(file_location, 'rb') as f:
       file_data = f.read()

    ext = os.path.splitext(str(cur_attachment.file.filename))[1]
    # sending response
    response = HttpResponse(file_data, content_type=f'application/{ext}')
    response['Content-Disposition'] = f'attachment; filename="{cur_attachment.file.filename}"'

    # return FileResponse(open(file_location, 'rb'))

    # except IOError:
    #     # handle file not exist case here
    #     response = HttpResponseNotFound('<h1>File not exist</h1>')

    # return Response(status=status.HTTP_200_OK, data=data)
    return response