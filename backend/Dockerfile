FROM public.ecr.aws/lambda/python:3.11

COPY pyproject.toml ${LAMBDA_TASK_ROOT}/pyproject.toml
COPY src ${LAMBDA_TASK_ROOT}/src

RUN pip install --no-cache-dir "${LAMBDA_TASK_ROOT}" --target "${LAMBDA_TASK_ROOT}"

# Overridden per Lambda function in infra/modules/lambda (backend-api vs
# recommendation-engine use the same image, different handlers).
CMD ["trading_backend.main.handler"]
