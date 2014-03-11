deps:
	@pip install -r requirements.txt

test-deps:
	@pip install -r test-requirements.txt

clean:
	@find . -name "*.pyc" -delete

test: test-deps clean
	@PYTHONPATH=. py.test -s .
	@flake8 .

run: deps
	@honcho start
