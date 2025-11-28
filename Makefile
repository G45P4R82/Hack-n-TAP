# Nome da imagem (ajusta pro teu projeto)
IMAGE_NAME = hack-n-tap
CONTAINER_NAME = hack-n-tap-container

# ---------- TARGETS PRINCIPAIS ---------- #

## build: Build da imagem Docker
build:
	docker build -t $(IMAGE_NAME) .

## publish: Envia a imagem para o Docker Hub (necessário estar logado)
## Ex: make publish USER=meuuser
publish:
	docker tag $(IMAGE_NAME) srmarinho/$(IMAGE_NAME):latest
	docker push srmarinho/$(IMAGE_NAME):latest

## run: Sobe o container com a aplicação Django
run:
	docker run -d \
		--name $(CONTAINER_NAME) \
		-p 8000:8000 \
		$(IMAGE_NAME)

## stop: Para o container
stop:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

## logs: Mostra logs em tempo real
logs:
	docker logs -f $(CONTAINER_NAME)

## clean: Remove imagem e container
clean: stop
	docker rmi $(IMAGE_NAME) || true

## help: Lista os comandos disponíveis
help:
	@echo ""
	@echo "Comandos disponíveis no Makefile:"
	@echo "  make build      -> Builda a imagem Docker"
	@echo "  make publish    -> Publica no Docker Hub (use USER=usuario)"
	@echo "  make run        -> Roda o container"
	@echo "  make logs       -> Mostra logs"
	@echo "  make stop       -> Para e remove o container"
	@echo "  make clean      -> Remove imagem e container"
	@echo "  make help       -> Mostra esta ajuda"
	@echo ""

