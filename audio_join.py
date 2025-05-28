import subprocess

def combine_video_audio(video_path, audio_path, output_path):
    command = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    subprocess.run(command, check=True)

combine_video_audio("./output.mp4", "../output_audio/output_5.mp3", "final_output.mp4")
