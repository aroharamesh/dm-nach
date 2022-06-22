#
FROM python:3.9.0-alpine

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

#
RUN  apk add build-base

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# 
COPY ./arthmate_lender_handoff_service /code/arthmate_lender_handoff_service

RUN mkdir -p /code/arthmate_lender_handoff_service/logs/

# 
#CMD ["uvicorn", "app.post_service:app", "--host", "0.0.0.0", "--port", "80", "--root-path", "/fastapi"]

CMD ["uvicorn", "arthmate_lender_handoff_service.main:app", "--host", "0.0.0.0", "--port", "9798"]
