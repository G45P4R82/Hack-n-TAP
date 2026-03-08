

help:
	@echo "Available commands:"
	@echo "  run - Run the application"
	@echo "  clean - Clean up build artifacts"
	@echo "  help - Show this help message"
	@echo "  setup - Create a virtual environment and install dependencies"
	@echo "  activate - Activate the virtual environment"
	@echo "  deactivate - Deactivate the virtual environment"
	@echo "  serial - List serial ports"

clean:
	@echo "Cleaning up build artifacts..."
	@rm -rf __pycache__
	@rm -rf *.py[cod]
	@rm -rf *$py.class
	@rm -rf *.so
	@rm -rf .Python
	@rm -rf build/
	@rm -rf develop-eggs/
	@rm -rf dist/
	@rm -rf downloads/
	@rm -rf eggs/
	@rm -rf .eggs/
	@rm -rf lib/
	@rm -rf lib64/
	@rm -rf parts/
	@rm -rf sdist/
	@rm -rf var/
	@rm -rf wheels/
	@rm -rf *.egg-info/
	@rm -rf .installed.cfg
	@rm -rf *.egg
	@rm -rf MANIFEST
	@rm -rf .env
	@rm -rf .venv
	@rm -rf env/
	@rm -rf venv/
	@rm -rf .pytest_cache/
	@rm -rf .coverage
	@rm -rf htmlcov/
	@rm -rf .mypy_cache/

setup:
	@echo "Creating virtual environment..."
	@python3 virtualenv env --python=python3 
	@echo "Activating virtual environment..."
	@source env/bin/activate
	@echo "Installing dependencies..."
	@pip install -r requirements.txt
	@echo "Done!"

activate:
	@echo "Activating virtual environment..."
	@source env/bin/activate

run:
	@echo "Running the application..."
	@python tap/main.py

deactivate:
	@echo "Deactivating virtual environment..."
	@deactivate
serial:
	@echo "Serial port..."
	@ls /dev/ttyACM*
	@ls /dev/ttyUSB*
	@ls /dev/ttyS*
