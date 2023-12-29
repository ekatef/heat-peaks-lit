# Makefile

get_data:
	echo "Load heat-peaks modeling data"
	python heat-peaks-lit/app/repo.py
	echo "Download successful. Stored in eee-project/heat-peaks"
	
run_app:
	streamlit run app/Introduction.py