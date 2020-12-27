.PHONY: bundles
bundles:
	rm -rf zipline_bundles || exit 0
	git clone https://github.com/hhatefi/zipline_bundles
	cd zipline_bundles && \
		python install.py -f || exit 0 && \
		pip install -r requirements.txt