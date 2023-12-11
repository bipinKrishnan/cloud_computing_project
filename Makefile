.phony: docker-push
docker-push:
	docker builder prune --force
	docker build -t carbon-app-image -f Dockerfile .
	docker tag carbon-app-image gcr.io/mini-project-406211/carbon-app-image
	docker push gcr.io/mini-project-406211/carbon-app-image

.phony: kube-deploy
kube-deploy:
	kubectl apply -f deployment.yml
	kubectl apply -f service.yml