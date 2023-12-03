.phony: docker-push
docker-push:
	docker builder prune --force
	docker build -t carbon-app-image -f Dockerfile .
	docker tag carbon-app-image gcr.io/burnished-flare-400911/carbon-app-image
	docker push gcr.io/burnished-flare-400911/carbon-app-image

.phony: kube-deploy
kube-deploy:
	kubectl apply -f deployment.yml
	kubectl apply -f service.yml