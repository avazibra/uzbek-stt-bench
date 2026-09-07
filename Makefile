.PHONY: clips score edit
clips:            ## download and cut the audio clips (needs ffmpeg)
	python3 scripts/fetch_clips.py
score:            ## score all transcripts that have a reference, refresh README table
	python3 scripts/score.py
edit:             ## open the reference editor for CLIP (default ep40)
	@echo "Open http://localhost:8765/tools/editor.html?clip=$(or $(CLIP),ep40)"
	python3 -m http.server 8765
