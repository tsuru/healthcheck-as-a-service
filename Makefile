deps:
	@pip install -r test-requirements.txt

clean:
	@find . -name "*.pyc" -delete

test: deps clean
	@py.test .
