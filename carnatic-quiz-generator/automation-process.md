Automation process

Collecting the information for the video

1.	Run `select_quiz_tracks.py` to pick a similar ragam pair from `ragam_pairs.json` and choose 3 vocal tracks from the main ragam plus 1 from the odd ragam. Track metadata comes from `MasterWebAppMusicIndex.csv`. Only local files in `audio-clips/` are considered (download with `fetch_audio_clips.sh`; see `audio-clips/README.md`).
2.	The ragam pair is chosen randomly each run (use `--seed` for reproducibility).
3.	After the ragams are picked, 3 audios from the main ragam and 1 from the odd ragam are selected randomly from eligible local `audio-clips/` files.
4.	Each audio clip should then be labeled clip1, clip2, clip3 until clip4 which should always be the odd one out (opposing ragam).
5.	It should select a 30 second clip with vocal cords as part of the audio.
6.	It should start running each clip and there should be a check point after it gets each clip to make sure that the part of the audio is correct, if it is it will keep going through and getting the other clip audios.
7.	After all the clip audios have been approved, clips can be randomly arranged into a video format.
8.	A quiz folder should be created, indexing after each quiz made- #49.. #50 and so on for the title of the quiz folder.
9.	In the quiz folder there should be a meta data file and four audio files. The meta data file should include the artist, regam and audio file.
10.	To create the video with the four separate audio clips, each clip should correspond to an image of the artist. The artists photo will be in a folder titled “Pics”. The photos should be displayed when the audio clip plays with a similar or matching audio file name to the image in the Pics folder.
11.	Inside each numbered quiz folder there should be a text file that converts the audio file name to the name of the artist.
