# Nome da imagem e container
IMAGE_NAME=hack-n-tap
CONTAINER_NAME=hack-n-tap-container

# Credenciais do superuser
DJANGO_SUPERUSER_USERNAME=tap
DJANGO_SUPERUSER_EMAIL=tap@tap.lhc
DJANGO_SUPERUSER_PASSWORD=tijolo22

# ---------- TARGETS PRINCIPAIS ---------- #

## build: Build da imagem Docker
build:
	docker build -t $(IMAGE_NAME) .

## publish: Envia a imagem para o Docker Hub
publish:
	docker tag $(IMAGE_NAME) srmarinho/$(IMAGE_NAME):latest
	docker push srmarinho/$(IMAGE_NAME):latest

## run: Sobe o container, aplica migrate e cria superuser
run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p 8000:8000 \
		-e DJANGO_SUPERUSER_USERNAME=$(DJANGO_SUPERUSER_USERNAME) \
		-e DJANGO_SUPERUSER_EMAIL=$(DJANGO_SUPERUSER_EMAIL) \
		-e DJANGO_SUPERUSER_PASSWORD=$(DJANGO_SUPERUSER_PASSWORD) \
		$(IMAGE_NAME) \
		bash -c "\
			python manage.py migrate && \
			python manage.py createsuperuser --noinput || true && \
			python manage.py runserver 0.0.0.0:8000 \
		"

## stop: Para e remove o container
stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

## logs: Mostra logs em tempo real

logs:
	docker logs $(CONTAINER_NAME)

## clean: Remove imagem e container
clean: stop
	docker rmi $(IMAGE_NAME) || true

## help: Lista os comandos disponíveis
help:
	@echo ""
	@echo "Comandos disponíveis:"
	@echo "  make build   -> Builda a imagem Docker"
	@echo "  make run     -> Sobe container + migrate + superuser"
	@echo "  make logs    -> Logs do container"
	@echo "  make stop    -> Para e remove o container"
	@echo "  make clean   -> Remove imagem e container"

