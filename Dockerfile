#
FROM python:3.9.2-alpine

#
WORKDIR /code

#
COPY ./requirements.txt /code/requirements.txt
RUN mkdir -p ./static
RUN mkdir -p ./logs

#
RUN  apk add build-base

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install 'uvicorn[standard]'
RUN pip install fastapi-utils

#
COPY ./dm_nac_service /code/dm_nac_service

#


#EXPOSE 3306
#CMD ["uvicorn", "dm_nac_service.main:app", "--host", "0.0.0.0", "--port", "9019"]
CMD ["uvicorn", "dm_nac_service.main:app", "--host", "0.0.0.0", "--port", "9019", "--root-path", "/dm-nac"]
