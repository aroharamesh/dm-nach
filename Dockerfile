#
FROM python:3.9.2-alpine

#
WORKDIR /code

#
COPY ./requirements.txt /code/requirements.txt

#
RUN  apk add build-base

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install 'uvicorn[standard]'
RUN pip install fastapi-utils

#
COPY ./dm_nac_service /code/dm_nac_service

#
#CMD ["uvicorn", "app.post_service:app", "--host", "0.0.0.0", "--port", "80", "--root-path", "/fastapi"]

EXPOSE 3306
CMD ["uvicorn", "dm_nac_service.main:app", "--host", "0.0.0.0", "--port", "9009"]
