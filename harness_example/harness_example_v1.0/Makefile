all: compile run clean

compile:
	c++ -O3 -Wall -shared -std=c++11 -fPIC $(shell python3 -m pybind11 --includes) example.cpp -o example$(shell python3-config --extension-suffix)

run:
	python test.py

clean:
	-rm -rf *.so


# time make
