import dotenv
import os
import json
import subprocess
import shlex
import signal
import sys

dotenv.load_dotenv(override=True)

platform_id = "OTHER"

OUTPUT_PATH = os.getenv("OUTPUT_PATH") or "./outputs"
RESOURCE_PATH = os.getenv("RESOURCE_PATH") or "./my-runpod-volume/models"
PROGRAM_PATH = os.getenv("PROGRAM_PATH") or "./stable-diffusion-webui-forge"

if "RUNPOD_POD_ID" in os.environ.keys():
    platform_id = "RUNPOD"
elif "PAPERSPACE_FQDN" in os.environ.keys():
    platform_id = "PAPERSPACE"

FORGE_PORT = 7860

check_types = [
    "checkpoints",
    "vae",
    "text-encoder",
    "gfpgan",
    "embeddings",
    "hypernetwork",
    "esrgan",
    "clip",
    "controlnet",
    "loras",
]

argss = [
    "--ckpt-dir",
    "--vae-dir",
    "--text-encoder-dir",
    "--gfpgan-dir",
    "--embeddings-dir",
    "--hypernetwork-dir",
    "--esrgan-models-path",
    "--clip-models-path",
    "--controlnet-dir",
    "--lora-dir",
]

types_mapping = {
    "checkpoints": "ckpts",
    "vae": "vae",
    "text-encoder": "text-encoder",
    "upscale_models": "esrgan",
    "unet": "ckpts",
    "clip": "text-encoder",
    "embeddings": "embeddings",
    "controlnet": "controlnet",
    "hypernetworks": "hypernetwork",
}

patch_output_directory = {
    "outdir_txt2img_samples": "/notebooks/outputs/txt2img-images",
    "outdir_img2img_samples": "/notebooks/outputs/img2img-images",
    "outdir_extras_samples": "/notebooks/outputs/extras-images",
    "outdir_txt2img_grids": "/notebooks/outputs/txt2img-grids",
    "outdir_img2img_grids": "/notebooks/outputs/img2img-grids",
    "outdir_init_images": "/notebooks/outputs/init-images",
}

# Global variable to store the subprocess
forge_process = None


def signal_handler(signum, frame):
    """Handle termination signals and clean up subprocess"""
    print(f"Received signal {signum}. Cleaning up...")
    cleanup_and_exit()


def cleanup_and_exit():
    """Terminate the subprocess and exit"""
    global forge_process
    if forge_process:
        print("Terminating Forge process...")
        try:
            # Try graceful termination first
            forge_process.terminate()
            forge_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            print("Graceful termination failed, forcing kill...")
            forge_process.kill()
            forge_process.wait()
        except Exception as e:
            print(f"Error during cleanup: {e}")
    sys.exit(0)


def is_posix():
    try:
        import posix

        return True
    except ImportError:
        return False


def auto_launch_forge():
    global forge_process

    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Define subdirectories
    subdirs = [
        "txt2img-images",
        "img2img-images",
        "extras-images",
        "img2img-grids",
        "init-images",
    ]

    # Create all directories using os.path.join
    for subdir in subdirs:
        full_path = os.path.join(OUTPUT_PATH, subdir)
        os.makedirs(full_path, exist_ok=True)

    command = "python -u launch.py --loglevel WARNING --disable-console-progressbars --disable-safe-unpickle --enable-insecure-extension-access --no-download-sd-model --no-hashing --api --xformers --cuda-stream --cuda-malloc --disable-gpu-warning"

    for args, value in zip(argss, check_types):
        if value == "checkpoints":
            value = "ckpts"
        model_path = os.path.join(RESOURCE_PATH, value)
        command += f" {args} {model_path}"

    proxy_url = (
        f"not found please check the provider proxy url port {FORGE_PORT} or 3001"
    )
    if platform_id == "RUNPOD":
        proxy_url = f'URL : https://{os.environ.get("RUNPOD_POD_ID")}-{FORGE_PORT}.proxy.runpod.net'
        command += f" --port {FORGE_PORT} --listen"
    elif platform_id == "PAPERSPACE":
        proxy_url = f'URL : https://tensorboard-{os.environ.get("PAPERSPACE_FQDN")}'
        command += f" --port {FORGE_PORT} --listen"
    else:
        command += f" --share --port {FORGE_PORT} --listen"

    pos = is_posix()

    print("RUNNING CMD", shlex.split(command, posix=pos))

    os.chdir(PROGRAM_PATH)  # Change to the Forge directory

    # Check if file exists; if not, create it with an empty dictionary
    config_file = "config.json"
    if not os.path.exists(config_file):
        with open(config_file, "w") as fp:
            json.dump({}, fp, indent=4)

    # Read, update, and write back the config
    with open(config_file, "r") as fp:
        load_config = json.load(fp)

    load_config.update(patch_output_directory)

    with open(config_file, "w") as fp:
        json.dump(load_config, fp, indent=4)

    try:
        # Start the subprocess with unbuffered output
        # Use process group to ensure child processes are also terminated
        forge_process = subprocess.Popen(
            shlex.split(command, posix=pos),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # Line buffering
            preexec_fn=(
                os.setsid if hasattr(os, "setsid") else None
            ),  # Create new process group
        )

        print("WebUI Forge has been started")
        print(proxy_url)

        # Read output from the subprocess
        try:
            for line in forge_process.stdout:
                print(line.strip())
        except KeyboardInterrupt:
            print("Keyboard interrupt received")
            cleanup_and_exit()

        # Wait for the subprocess to complete
        forge_process.wait()

    except Exception as e:
        print(f"Error starting Forge: {e}")
        cleanup_and_exit()


if __name__ == "__main__":
    auto_launch_forge()
