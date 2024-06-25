build: # docker image 빌드
	docker build -t audiate .

run: # docker container 실행
	docker run -it --rm -v $(PWD):/app audiate
